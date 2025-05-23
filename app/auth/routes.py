# app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash # For password hashing
from app import db
from app.auth import auth_bp
from app.models import User

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = True if request.form.get('remember_me') else False

        # Basic manual validation
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('auth/login.html', title='Sign In')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('auth/login.html', title='Sign In', username=username) # Pass back username

        login_user(user, remember=remember_me)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('home.main')
        flash('Login successful!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html', title='Sign In')

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
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        # Basic manual validation
        error = False
        if not username:
            flash('Username is required.', 'danger')
            error = True
        if not email:
            flash('Email is required.', 'danger')
            error = True
        if not password:
            flash('Password is required.', 'danger')
            error = True
        if password != password2:
            flash('Passwords do not match.', 'danger')
            error = True

        if User.query.filter_by(username=username).first():
            flash('That username is already taken. Please choose a different one.', 'warning')
            error = True
        if User.query.filter_by(email=email).first():
            flash('That email address is already in use. Please choose a different one.', 'warning')
            error = True
        
        if error:
             # Pass submitted values back to the template to repopulate the form
            return render_template('auth/register.html', title='Register',
                                   username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Register')