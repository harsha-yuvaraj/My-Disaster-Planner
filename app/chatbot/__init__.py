from flask import Blueprint

# No 'template_folder' specified, so it uses the app's main 'templates' folder.
chatbot_bp = Blueprint('chatbot', __name__)

# Import routes at the bottom to avoid circular dependencies with 'chatbot_bp'
from app.chatbot import routes