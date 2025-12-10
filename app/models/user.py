# User Model
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, index=True)  # farmer, expert, admin, krishi_bhavan_officer
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Role-specific fields
    # For Farmer
    farm_size = db.Column(db.Float)  # in acres
    farm_location = db.Column(db.String(200))
    
    # For Expert
    expertise_area = db.Column(db.String(100))
    qualifications = db.Column(db.Text)
    years_of_experience = db.Column(db.Integer)
    
    # For Krishi Bhavan Officer
    officer_id = db.Column(db.String(50), unique=True)
    designation = db.Column(db.String(100))
    department = db.Column(db.String(100))
    
    def set_password(self, password):
        """Hash and set password using bcrypt"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash using bcrypt"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def is_farmer(self):
        return self.role == 'farmer'
    
    def is_expert(self):
        return self.role == 'expert'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_krishi_bhavan_officer(self):
        return self.role == 'krishi_bhavan_officer'
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

