from flask import Blueprint

# No 'template_folder' specified, so it uses the app's main 'templates' folder.
# We will organize auth templates under 'app/templates/auth/'.
auth_bp = Blueprint('auth', __name__)

# Import routes at the bottom to avoid circular dependencies with 'auth_bp'
from app.auth import routes
