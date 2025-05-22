# run.py
from app import create_app, db
from app.models import User # Import any models as needed

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Makes variables available in the Flask shell context for easier debugging."""
    return {'db': db, 'User': User} # Add other models or objects here

if __name__ == '__main__':
    app.run() # For development. For production, we will use a WSGI server like Gunicorn.