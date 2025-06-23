from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from sqlalchemy.orm.attributes import flag_modified 
from app.models import Plan
from app.home import home_bp
from app.utils import parse_plan_response
from app import db
from .plan_config import all_steps, TOTAL_PLAN_STEPS, form_data_lists
from datetime import datetime


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

    risk_data = {} if step_num==2 else None

    if request.method == 'POST':
        # Get the existing answers, ensuring it's a dictionary
        answers = plan.answers_json or {} 

        # --- Data Saving Logic ---
        step_key = f"step_{step_num}"
        
        # Create a mutable copy of the form data
        form_data = request.form.to_dict()
        form_data["last_step"] = step_num  # Store the current step number in the form data
        
        for key in form_data_lists.get(step_num, []):
            form_data[key] = request.form.getlist(key) if key in form_data else []

        # Parse the form data into a structured dictionary
        answers[step_key] = parse_plan_response(form_data, step_num)
        plan.answers_json = answers
        flag_modified(plan, 'answers_json') # Important for JSON mutation

        # Save the plan to the database
        db.session.commit()
        
        # --- Redirection Logic ---
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
    return render_template(f'home/plan/step_{step_num}.html', plan=plan, current_step=step_num, steps=all_steps, risk_data=risk_data)

        
