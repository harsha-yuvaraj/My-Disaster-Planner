from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.home import home_bp
from app import db

@home_bp.route('/main')
@login_required
def main():
    return render_template('home/home.html', title='Home Page')

