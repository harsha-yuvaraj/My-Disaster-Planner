from flask import Blueprint

# No 'template_folder' specified, so it uses the app's main 'templates' folder.
# We will organize home templates under 'app/templates/home'.
home_bp = Blueprint('home', __name__)

# Import routes at the bottom to avoid circular dependencies with 'home_bp'
from app.home import routes
