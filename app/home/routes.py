from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from sqlalchemy.orm.attributes import flag_modified 
from flask import current_app
from datetime import datetime
from app.models import Plan
from app.home import home_bp
from app.utils import parse_plan_response
from app import db
from .plan_config import all_steps, TOTAL_PLAN_STEPS, form_data_lists
from app.risk_assessment import get_flood_risk_by_address



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
                address = data.get('care_recipient_address', '') + ", " +data.get('care_recipient_city', '') + data.get('care_recipient_state', '') + " " + data.get('care_recipient_zip', '') + ", USA"
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
                # All steps are done, time to finalize
                # return redirect(url_for('home.finalize_plan', plan_id=plan.id))
                flash("You've completed your plan!", "success")
                return redirect(url_for('home.main')) # Redirect to overview when done
            else:
                return redirect(url_for('home.plan_step', plan_id=plan.id, step_num=next_step))

    # For a GET request, render the correct step's template
    return render_template(f'home/plan/step_{step_num}.html', plan=plan, current_step=step_num, steps=all_steps, fl_cemw_data=fl_cemw_data)

        
