from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.models import Plan
from app.home import home_bp
from app import db
from datetime import datetime

# Define the labels for all steps
all_steps = [
    "Information", 
    "Supplies", 
    "Contacts", 
    "Evacuation", 
    "Communicate", 
    "Review"
]

# Steps total for the questionnaire
TOTAL_PLAN_STEPS = len(all_steps)

@home_bp.route('/main')
@login_required
def main():
    return render_template('home/home.html', title='Home')

@home_bp.route('/plan/new', methods=['GET', 'POST'])
@login_required
def start_new_plan():
    """Renders the initial welcome screen where a user create and name a new plan."""
    if request.method == 'POST':
        plan_name = request.form.get('plan_name', 'My New Disaster Plan').strip()

        # Ensure plan name is not empty after stripping whitespace
        if not plan_name:
            plan_name = f'disaster-plan-{datetime.now().strftime('%Y%m%d%H%M%S')}'

        plan = Plan(user_id=current_user.id, name=plan_name, answers_json={})
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

    if request.method == 'POST':
        # Get the existing answers
        answers = plan.answers_json 

        # Store all form data for the current step under its specific key
        step_key = f"step_{step_num}"
        answers[step_key] = request.form.to_dict()
        plan.answers_json = answers
        db.session.flag_modified(plan, 'answers_json') # Important for JSON mutation
        db.session.commit()

        next_step = step_num + 1
        if next_step > TOTAL_PLAN_STEPS:
            # All steps are done, time to finalize
            # return redirect(url_for('home.finalize_plan', plan_id=plan.id))
            return "Plan is ready to be finalized!" # Placeholder
        else:
            return redirect(url_for('home.plan_step', plan_id=plan.id, step_num=next_step))

    # For a GET request, render the correct step's template
    return render_template(f'home/plan/step_{step_num}.html', plan=plan, current_step=step_num, steps=all_steps)
        
        