from mailjet_rest import Client
import re
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
    

def parse_plan_response(form_data, step_num):
    """
    Parses form data from a plan step into a structured dictionary.

    Args:
        form_data (dict): The form data from the request.
        step_num (int): The current step number being processed.
        form_data_lists (list): A list of field names that should be treated as lists.

    Returns:
        dict: A cleanly structured dictionary of the parsed data.
    """
    parsed_data = {}
    
    # --- Main Parsing Loop ---
    
    # This loop assumes form_data is a standard Python dictionary.
    for key, value in form_data.items():
        # Skip fields we don't want to save in our JSON data
        if key in ['_csrf_token', 'save_and_exit']:
            continue
        
        # This generic assignment works for both single values and lists.
        parsed_data[key] = value

    # --- Step 1 Specific Logic: Contact Parsing ---
    if step_num == 1 and 'contacts[0][name]' in parsed_data: # Check if contact data exists
        temp_contacts = {}
        contact_pattern = re.compile(r'contacts\[(\d+)\]\[(\w+)\]')
        
        # Iterate through a copy of the keys because we will be modifying the dict
        for key in list(parsed_data.keys()):
            contact_match = contact_pattern.match(key)
            if contact_match:
                index = int(contact_match.group(1))
                field_name = contact_match.group(2)
                
                if index not in temp_contacts:
                    temp_contacts[index] = {}
                
                # Add the value to our temporary dict and remove the flat key from parsed_data
                temp_contacts[index][field_name] = parsed_data.pop(key)

        # Convert the temporary contacts dictionary into a sorted, clean list of objects
        if temp_contacts:
            contact_list = [v for k, v in sorted(temp_contacts.items())]
            # Filter out any completely empty contact rows that might be submitted
            parsed_data['contacts'] = [contact for contact in contact_list if any(contact.values())]

    return parsed_data