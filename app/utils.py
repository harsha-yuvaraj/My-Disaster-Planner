from mailjet_rest import Client
from flask import current_app, render_template

def send_password_reset_email(user):
    """Sends the password reset email to a user via Mailjet."""
    token = user.get_reset_token() 

    api_key = current_app.config['MAILJET_API_KEY']
    api_secret = current_app.config['MAILJET_API_SECRET']
    
    # Check if credentials are set
    if not api_key or not api_secret:
        print("Error: Mailjet API keys are not configured.")
        return None

    # Initialize the Mailjet client 
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    
    # Render the HTML content for the email body
    html_content = render_template('auth/emailResetPassword.html', user=user, token=token)

    # Structure the email data as a dictionary (JSON) for the Mailjet API
    data = {
      'Messages': [
        {
          "From": {
            "Email": current_app.config['DEFAULT_MAIL_SENDER'],
            "Name": current_app.config.get('MAIL_FROM_NAME', "My Disaster Planner")
          },
          "To": [
            {
              "Email": user.email,
              "Name": user.first_name 
            }
          ],
          "Subject": "Reset your Password - My Disaster Planner",
          "HTMLPart": html_content
        }
      ]
    }
    
    try:
        # Send the request to Mailjet's API
        result = mailjet.send.create(data=data)
        return result.status_code
    
    except Exception as e:
        print(f"An exception occurred sending password reset email to {user.email}: {e}")
        return None