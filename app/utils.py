# app/email.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app, render_template

def send_password_reset_email(user):
    """Sends the password reset email to a user."""
    token = user.get_reset_token() # Generate the token
    
    # Create the email message using a template
    message = Mail(
        from_email=current_app.config['DEFAULT_MAIL_SENDER'],
        to_emails=user.email,
        subject='My Disaster Planner - Password Reset Request',
        html_content=render_template('auth/emailResetPassword.html', user=user, token=token)
    )
    
    try:
        sg = SendGridAPIClient(current_app.config['SENDGRID_API_KEY'])
        response = sg.send(message)
        return response
    except Exception as e:
        print(f"Error sending password reset email to {user.email}: {e}")
        return None

