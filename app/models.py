from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, date, timedelta
from sqlalchemy.sql import func # For database-level default timestamps
import uuid

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Personal Information
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(150), index=True, unique=True, nullable=False)
    gender = db.Column(db.String(8), nullable=False) 
    phone_number = db.Column(db.String(10), nullable=True) 
    date_of_birth = db.Column(db.Date, nullable=False)

    # Address Information
    street_address = db.Column(db.String(128), nullable=False)
    city = db.Column(db.String(64), nullable=False)
    state = db.Column(db.String(2), nullable=False) 
    zip_code = db.Column(db.String(5), nullable=False) 

    # Password and Timestamps
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime(), default=lambda: datetime.now())

    # Password Reset Fields
    reset_token = db.Column(db.String(36), nullable=True) # To store UUID as string
    reset_time_limit = db.Column(db.DateTime(), nullable=True)

    # one to many relationship with Plan
    plans = db.relationship('Plan', backref='user', cascade="all, delete-orphan", lazy=True)

    # Add __table_args__ to define constraints and indexes with names
    __table_args__ = (
        db.UniqueConstraint('reset_token', name='uq_user_reset_token'),
        db.Index('ix_user_reset_token', 'reset_token', unique=True), # This creates a unique index
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    # Example methods for handling reset tokens
    def get_reset_token(self, expires_in_seconds=900): # Default to 15 minutes
        """Generates a password reset token and sets its expiration."""
        self.reset_token = str(uuid.uuid4())
        self.reset_time_limit = datetime.now() + timedelta(seconds=expires_in_seconds)
        return self.reset_token

    @staticmethod
    def verify_reset_token(token):
        """Verifies a password reset token."""
        user = User.query.filter_by(reset_token=token).first()
        if user:
            # Check if the token is still valid
            if user.reset_time_limit and user.reset_time_limit > datetime.now():
                return user
            else:
                user.reset_token = None
                user.reset_time_limit = None
                db.session.commit()
            
        return None # Token is invalid or expired
    
    @property
    def age(self):
        """Calculates the user's current age from their date of birth."""
        if not self.date_of_birth:
            return None
        today = date.today()
        # This calculates the years difference, then subtracts 1 if the birthday hasn't occurred yet this year.
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    @property
    def address(self):
        """Returns the user's full address as a formatted string."""
        return f"{self.street_address}, {self.city}, {self.state} {self.zip_code}, USA"

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name} - ({self.email})>'


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="My Disaster Plan")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Stores all questionnaire answers as a JSON object
    answers_json = db.Column(db.JSON, nullable=True)
    
    # Stores the filename of the report stored on S3
    report_name = db.Column(db.String(100), nullable=True)
    
    # Tracks if the plan is complete or pending
    is_complete = db.Column(db.Boolean, default=False, nullable=False)

    # Boolean to indicate if the plan is for the user creating it.
    is_for_self = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timezone-aware timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f'<Plan id={self.id} name="{self.name}" status={self.is_complete}>'
