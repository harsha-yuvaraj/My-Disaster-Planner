# app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash # For password hashing
from app import db
from app.auth import auth_bp
from app.models import User
import re

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # If user is already logged in
        return redirect(url_for('home.main')) 
    
    if request.method == 'POST':
        # The Flask-SeaSurf extension automatically validates the CSRF token.
        email = request.form.get('email')
        password = request.form.get('password')
        remember_me = True if request.form.get('remember_me') else False

        # Find the user by their email address
        user = User.query.filter_by(email=email).first()

        # Check if the user exists and the password is correct
        if user is None or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            # Re-render the form, passing back the email to repopulate the field
            return render_template('auth/login.html', email=email)

        # All checks passed, log the user in with Flask-Login
        login_user(user, remember=remember_me)

        # If the user was trying to access a protected page, redirect them there.
        # Otherwise, redirect to a default main page.
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('home.main') 

        flash('You have been logged in successfully!', 'success')
        return redirect(next_page)

    # For a GET request, just render the blank login form
    return render_template('auth/login.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('auth/forgotPassword.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        # Redirect to your main app page if the user is already logged in
        return redirect(url_for('home.main')) 

    if request.method == 'POST':
        # Retrieve all form data 
        form_data = request.form
        first_name = form_data.get('first_name')
        last_name = form_data.get('last_name')
        email = form_data.get('email')
        gender = form_data.get('gender')
        street_address = form_data.get('street_address')
        city = form_data.get('city')
        state = form_data.get('state')
        zip_code = form_data.get('zip_code')
        phone_number = form_data.get('phone_number') # Optional field
        password = form_data.get('password')
        password2 = form_data.get('password2')

        # Perform server-side validation
        errors = False
        # Check required fields
        required_fields = {
            'First Name': first_name, 'Last Name': last_name, 'Email': email,
            'Gender': gender, 'Street Address': street_address, 'City': city,
            'State': state, 'Zip Code': zip_code, 'Password': password
        }
        for field_name, value in required_fields.items():
            if not value:
                flash(f'{field_name} is required.', 'danger')
                errors = True

        # Check password match
        if password != password2:
            flash('Passwords do not match.', 'danger')
            errors = True

        # Check email uniqueness
        if email and User.query.filter_by(email=email).first():
            flash('That email address is already in use. Please choose a different one.', 'warning')
            errors = True

        # Check zip code and phone number formats using regular expressions
        if zip_code and not re.match(r'^\d{5}$', zip_code):
            flash('Zip Code must be exactly 5 digits.', 'danger')
            errors = True
            
        if phone_number and not re.match(r'^\d{10}$', phone_number):
            flash('Phone Number must be exactly 10 digits.', 'danger')
            errors = True

        if errors:
            # If there are any errors, re-render the form.
            # The 'value' attributes in the HTML will repopulate the fields.
            return render_template('auth/register.html', title='Create Your Account')

        try:
            # All checks passed, create the new user object
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                gender=gender,
                street_address=street_address,
                city=city,
                state=state,
                zip_code=zip_code,
                # Set phone_number only if it's not an empty string
                phone_number=phone_number if phone_number else None
            )
            new_user.set_password(password) # Hash the password
            
            db.session.add(new_user)
            db.session.commit()

            flash('Congratulations, your account has been created! Please sign in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback() # Rollback the session in case of a database error
            flash(f'An unexpected error occurred. Please try again. Error: {e}', 'danger')

    # For a GET request, just render the blank form
    return render_template('auth/register.html', title='Create Your Account')