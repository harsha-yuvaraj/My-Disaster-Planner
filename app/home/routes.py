from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy.orm.attributes import flag_modified 
from flask import current_app
from datetime import datetime
import io, re
from weasyprint import HTML
from zoneinfo import ZoneInfo
from app.models import Plan
from app.home import home_bp
from app.utils import parse_plan_response, send_plan_to_recipients
from app import db
from .plan_config import all_steps, TOTAL_PLAN_STEPS, form_data_lists, risk_assessment_questions
from app.risk_assessment import get_flood_risk_by_address, get_travel_distance_and_time
from app.s3_storage import upload_file_to_s3, generate_presigned_url, delete_object_from_s3, download_file_as_bytesio


@home_bp.route('/main')
@login_required
def main():
    # Get all plans belonging to the current user and order them by the most recently updated.
    plans = Plan.query.filter_by(user_id=current_user.id).order_by(Plan.updated_at.desc()).all()
    return render_template('home/home.html', plans=plans, title='Home')


@home_bp.route('/plan/new', methods=['GET', 'POST'])
@login_required
def start_new_plan():
    """Renders the initial welcome screen where a user create and name a new plan."""
    if request.method == 'POST':
        plan_name = request.form.get('plan_name').strip()
        is_for_self = (request.form.get('plan_for').strip() == 'self') # Will be 'self' or 'other'
        # Ensure plan name is not empty after stripping whitespace
        if not plan_name:
            plan_name = f'disaster-plan-{datetime.now().strftime('%Y%m%d%H%M%S')}'

        plan = Plan(user_id=current_user.id, name=plan_name, is_for_self=is_for_self, answers_json={})
        db.session.add(plan)
        db.session.commit()

        # Redirect to the first step of the questionnaire
        return redirect(url_for('home.plan_step', plan_id=plan.id, step_num=1))

    return render_template('home/plan/start_plan.html', title="Start a New Plan")


@home_bp.route('/plan/<int:plan_id>/<int:step_num>', methods=['GET', 'POST'])
@login_required
def plan_step(plan_id, step_num):
    """Handles every step of the current questionnaire dynamically."""
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    fl_cemw_data = {}

    if step_num < 1 or step_num > TOTAL_PLAN_STEPS:
        flash('Invalid Action.', 'danger')
        return redirect(url_for('home.main'))

    if step_num == 2:
        if 'flood_risk' not in plan.answers_json:
            answers = plan.answers_json or {}
            # If the plan is for someone else, we need to get their address
            if not plan.is_for_self:
                data = answers.get('step_1', {})
                address = data.get('care_recipient_address', '') + ", " +data.get('care_recipient_city', '') + ", " + data.get('care_recipient_state', '') + " " + data.get('care_recipient_zip', '') + ", USA"
            else:
                address = current_user.street_address + ", " + current_user.city + ", " + current_user.state + " " + current_user.zip_code + ", USA"
            
            # Get flood risk data for the address
            answers['flood_risk'] = get_flood_risk_by_address(address)
            plan.answers_json = answers
            flag_modified(plan, 'answers_json') 
            db.session.commit()
    
    if step_num == 3:
        if (plan.is_for_self and current_user.state == 'FL') or ((not plan.is_for_self) and plan.answers_json.get('step_1', {}).get('care_recipient_state', '').strip() == 'FL'):
            fl_cemw_data = current_app.config['FLORIDA_CEMW']

    if step_num == TOTAL_PLAN_STEPS and not plan.answers_json.get('evacuate_travel_info', {}):
        step_key = f"step_{step_num-1}"
        answers = plan.answers_json or {}
        plan_response = answers.get(step_key,{})
        plan_addresses = {}

        if answers.get('step_2', {}).get('decision', '').strip().lower() == 'evacuate' and plan_response.get('primary_transport', 'air').strip().lower() != 'air':
            for knows, addr, key in [('primary_knows_address', 'primary_address', 'primary_trip'), ('backup_knows_address', 'backup_address', 'backup_trip')]:
                if plan_response.get(knows, "") == "yes":
                    if plan.is_for_self:
                        plan_addresses[key] = {'source': current_user.address, 'dest': plan_response.get(addr, '')}
                    else:   
                        info_response = answers.get('step_1', {})
                        care_recipient_address =  info_response.get('care_recipient_address', '') + ", " + info_response.get('care_recipient_city', '') + ", " + info_response.get('care_recipient_state', '') + " " + info_response.get('care_recipient_zip', '') + ", USA"
                        plan_addresses[key] = {'source': care_recipient_address, 'dest': plan_response.get(addr, '')}
            
            plan_addresses["travel_by"] = plan_response.get('primary_transport', '')
            answers['evacuate_travel_info'] = get_travel_distance_and_time(plan_addresses)

        plan.answers_json = answers
        flag_modified(plan, 'answers_json') # Important for JSON mutation
        db.session.commit()


    if request.method == 'POST':
        # Get the existing answers, ensuring it's a dictionary
        answers = plan.answers_json or {} 

        # Data Saving Logic
        step_key = f"step_{step_num}"
        # Create a mutable copy of the form data
        form_data = request.form.to_dict()
        for key in form_data_lists.get(step_num, []):
            form_data[key] = request.form.getlist(key) if key in form_data else []

        # Parse the form data into a structured dictionary
        answers[step_key] = parse_plan_response(form_data, step_num)
        answers["last_step"] = step_num  # Update the last step in the answers
        plan.answers_json = answers
        flag_modified(plan, 'answers_json') # Important for JSON mutation
        # Save the plan to the database
        db.session.commit()
        
        # Redirection Logic
        # Check if the 'save_and_exit' button was clicked. Its 'name' attribute will be present in the form data if it was the button that submitted the form.
        if 'save_and_exit' in request.form:
            # Redirect to a plan overview or dashboard.
            flash(f'Your progress for {plan.name} has been saved.', 'success')
            return redirect(url_for('home.main'))
        else:
            # This is the "Save and Continue" case
            next_step = step_num + 1
            if next_step > TOTAL_PLAN_STEPS:
                # All steps are done, generate plan
                pdf_object = generate_plan(plan_id=plan.id)
                pdf_object_bytes = pdf_object.getvalue()
                plan_for = current_user.first_name if plan.is_for_self else plan.answers_json.get('step_1', {}).get('care_recipient_name', 'NA')[:60]   
                output_filename = f"mdp_plan_{plan_for}_{plan.id}_{current_user.id}.pdf".strip().replace(' ', '_').lower()

                sender_list = [current_user.email if plan.answers_json.get('step_4',{}).get('email_user', '') else '', plan.answers_json.get('step_1',{}).get('care_recipient_email', '') if plan.answers_json.get('step_4',{}).get('email_care_recipient', '') else '']
                sender_list = [email for email in sender_list if email]

                if not upload_file_to_s3(pdf_object, output_filename, content_type='application/pdf'):
                    flash('There was an error generating your plan. Please try again later.', 'danger')
                    return redirect(url_for('home.main'))
                
                plan.is_complete, plan.report_name  = True, output_filename
                db.session.commit()
                
                if sender_list:
                    print("Sneding generated plans.")
                    send_plan_to_recipients(recipient_emails=sender_list, plan_pdf_bytes=pdf_object_bytes, plan_name=output_filename)

                return redirect(url_for('home.view_plan', plan_id=plan.id)) 
            else:
                return redirect(url_for('home.plan_step', plan_id=plan.id, step_num=next_step))

    # For a GET request, render the correct step's template
    return render_template(f'home/plan/step_{step_num}.html', plan=plan, current_step=step_num, steps=all_steps, fl_cemw_data=fl_cemw_data)


@home_bp.route('/plan/view/<int:plan_id>', methods=['GET'])
@login_required
def view_plan(plan_id):
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    if not plan.is_complete:
        flash("Invalid action.", "danger")
        return redirect(url_for('home.main'))
    
    view_url = generate_presigned_url(plan.report_name) 
    download_url = generate_presigned_url(plan.report_name,response_disposition="attachment")

    return render_template('/home/view_plan.html', plan=plan, view_url=view_url, download_url=download_url, name=plan.report_name, title=f'Viewing {plan.name}')


@home_bp.route('/plan/share-by-email/<int:plan_id>', methods=['POST'])
@login_required
def share_plan_by_email(plan_id):
    """
    API endpoint to share a plan with a list of email recipients.
    Accepts a JSON payload: {"emails": ["email1@example.com", ...]}
    """
    # Ensure the plan exists and belongs to the current user.
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first()
    if not plan or not plan.is_complete:
        return jsonify({'error': 'Plan not found or is incomplete.'}), 404

    # Input Validation
    data = request.get_json()
    if not data or 'emails' not in data:
        return jsonify({'error': 'Missing email data in request.'}), 400

    recipient_emails = data['emails']
    if not recipient_emails:
        return jsonify({'error': 'A non-empty list of emails is required.'}), 400
    
    recipient_emails = [email.strip() for email in recipient_emails.split(',')]

    # Enforce a limit on the number of recipients
    MAX_RECIPIENTS = 5
    if len(recipient_emails) > MAX_RECIPIENTS:
        return jsonify({'error': f'You can send to a maximum of {MAX_RECIPIENTS} recipients at a time.'}), 400
    
    # Pre-validate and filter email addresses using regex
    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    valid_emails = [email for email in recipient_emails if email_regex.match(email)]

    if not valid_emails:
        return jsonify({'error': 'No valid email addresses were provided.'}), 400

    # Retrieve the plan PDF from S3
    try:

        pdf_file_obj = download_file_as_bytesio(plan.report_name)
        if not pdf_file_obj:
            raise ValueError("Failed to retrieve plan file from storage.")
        
        plan_pdf_bytes = pdf_file_obj.getvalue()

    except Exception as e:
        print(f"Error retrieving plan {plan.report_name} from S3: {e}")
        return jsonify({'error': 'Could not access the plan file.'}), 500

    # Call the utility function to send the emails
    success = send_plan_to_recipients(
        recipient_emails=valid_emails,
        plan_pdf_bytes=plan_pdf_bytes,
        plan_name=plan.report_name
    )

    # Response
    if success:
        return jsonify({'message': f'Plan successfully sent to {len(valid_emails)} recipient(s).'}), 200
    else:
        return jsonify({'error': 'There was a problem sending the email. Try again later.'}), 500
    

@home_bp.route('/plan/delete/<int:plan_id>', methods=['POST'])
@login_required
def delete_plan(plan_id):
    """
    Handles the deletion of a specific plan. This includes removing the
    PDF report from S3 and the plan record from the database.
    """
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    
    try:
        # Delete from S3: If the plan was completed and has a report file, delete it.
        if plan.report_name:
            if not delete_object_from_s3(plan.report_name):
                # If S3 deletion fails, flash an error and halt
                flash(f'Could not delete the plan "{plan.name}". Try again later.', 'warning')
                return redirect(url_for('home.main'))
        
        # Delete from Database
        db.session.delete(plan)
        db.session.commit()

        flash(f'Successfully deleted the plan: {plan.name}', 'success')
        
    except Exception as e:
        # If anything goes wrong, roll back the transaction.
        db.session.rollback()
        print(f"Error deleting plan {plan_id}: {e}")
        flash('An unexpected error occurred while attempting to delete the plan. Please try again.', 'danger')

    # Always redirect back to the user's dashboard.
    return redirect(url_for('home.main'))


def generate_plan(plan_id):
    """Generates a disaster plan (pdf) based on the user's answers."""
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    if not plan.answers_json:
        flash('Error generating this plan. Please review again and answer all questions thoroughly.', 'danger')
        return False

    plan_last_updated = plan.updated_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M:%S %p %Z")
    is_florida = (current_user.state == 'FL') if plan.is_for_self else (plan.answers_json.get('step_1', {}).get('care_recipient_state', '').strip() == 'FL')
    
    html_content = render_template('home/plan/plan_report.html', plan=plan, plan_last_updated=plan_last_updated, risk_assessment_questions=risk_assessment_questions, is_florida=is_florida)
    
    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
        pdf_file_object = io.BytesIO(pdf_bytes)
        pdf_file_object.seek(0)

        return pdf_file_object

    except Exception as e:
        print(f"Error occurred while pdf generation for {plan.id} for {repr(current_user)}: {e}")

    return None
    