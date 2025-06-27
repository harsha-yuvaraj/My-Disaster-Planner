from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from sqlalchemy.orm.attributes import flag_modified 
from flask import current_app
from datetime import datetime
import json, os
from weasyprint import HTML
from zoneinfo import ZoneInfo
from app.models import Plan
from app.home import home_bp
from app.utils import parse_plan_response
from app import db
from .plan_config import all_steps, TOTAL_PLAN_STEPS, form_data_lists, risk_assessment_questions
from app.risk_assessment import get_flood_risk_by_address, get_travel_distance_and_time



@home_bp.route('/main')
@login_required
def main():
    return render_template('home/home.html', title='Home')


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
                # All steps are done, time to generate plan
                result = generate_plan(plan_id=plan.id)
                if not result:
                    flash('There was an error generating your plan. Please try again later.', 'danger')
                    return redirect(url_for('home.main'))
                
                flash(f"Your plan '{plan.name}' is ready!" if plan.is_for_self else f"Your plan '{plan.name}' for {plan.answers_json.get("step_1",{}).get('care_recipient_name', 'the person you care for')} is ready!", "success")
                return redirect(url_for('home.main')) 
            else:
                return redirect(url_for('home.plan_step', plan_id=plan.id, step_num=next_step))

    # For a GET request, render the correct step's template
    return render_template(f'home/plan/step_{step_num}.html', plan=plan, current_step=step_num, steps=all_steps, fl_cemw_data=fl_cemw_data)


def generate_plan(plan_id):
    """Generates a disaster plan (pdf) based on the user's answers."""
    plan = Plan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    if not plan.answers_json:
        flash('Error generating this plan. Please review again and answer all questions thoroughly.', 'danger')
        return False

    plan_for = current_user.first_name if plan.is_for_self else plan.answers_json.get('step_1', {}).get('care_recipient_name', 'NA')[:60]   
    output_filename = f"mdp_plan_{plan_for}_{plan.id}_{current_user.id}"
    output_filename = output_filename.strip().lower()
    output_extension = '.pdf'

    plan_last_updated = plan.updated_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M:%S %p %Z")
    is_florida = (current_user.state == 'FL') if plan.is_for_self else (plan.answers_json.get('step_1', {}).get('care_recipient_state', '').strip() == 'FL')
    
    html_content = render_template('home/plan/plan_report.html', plan=plan, plan_last_updated=plan_last_updated, risk_assessment_questions=risk_assessment_questions, is_florida=is_florida)
    
    try:
        HTML(string=html_content).write_pdf(output_filename + output_extension)
        os.path.abspath(output_filename + output_extension)
        
    except Exception as e:
        print(f"Error occurred while pdf generation for {plan.id} for {repr(current_user)}: {e}")

    return True
    