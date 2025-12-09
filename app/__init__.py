# Flask Application Factory
from flask import Flask
from flask_login import LoginManager
from pathlib import Path
from app.config import Config
from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.farmer_login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def seed_demo_users_if_needed():
    """Automatically seed demo users if they don't exist (for production)"""
    try:
        # Check if demo users already exist
        if User.query.filter_by(username='farmer_demo').first():
            return  # Users already exist, skip seeding
        
        # Common password for all demo users
        demo_password = "demo123"
        
        demo_users = [
            {
                'username': 'farmer_demo',
                'email': 'farmer@demo.com',
                'full_name': 'Demo Farmer',
                'phone': '9876543210',
                'address': 'Farm Village, Kerala',
                'role': 'farmer',
                'farm_size': 5.0,
                'farm_location': 'Kottayam, Kerala'
            },
            {
                'username': 'expert_demo',
                'email': 'expert@demo.com',
                'full_name': 'Dr. Demo Expert',
                'phone': '9876543211',
                'address': 'Agricultural Institute, Delhi',
                'role': 'expert',
                'expertise_area': 'Crop Disease Management',
                'qualifications': 'PhD in Plant Pathology',
                'years_of_experience': 10
            },
            {
                'username': 'admin_demo',
                'email': 'admin@demo.com',
                'full_name': 'Admin User',
                'phone': '9876543212',
                'address': 'Admin Office, Delhi',
                'role': 'admin'
            },
            {
                'username': 'officer_demo',
                'email': 'officer@demo.com',
                'full_name': 'Krishi Officer',
                'phone': '9876543213',
                'address': 'Krishi Bhavan, Mumbai',
                'role': 'krishi_bhavan_officer',
                'officer_id': 'KBO001',
                'designation': 'Agricultural Officer',
                'department': 'Agricultural Extension'
            }
        ]
        
        for user_data in demo_users:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                phone=user_data['phone'],
                address=user_data['address'],
                role=user_data['role'],
                is_active=True
            )
            
            # Add role-specific fields
            if user_data['role'] == 'farmer':
                user.farm_size = user_data.get('farm_size')
                user.farm_location = user_data.get('farm_location')
            elif user_data['role'] == 'expert':
                user.expertise_area = user_data.get('expertise_area')
                user.qualifications = user_data.get('qualifications')
                user.years_of_experience = user_data.get('years_of_experience')
            elif user_data['role'] == 'krishi_bhavan_officer':
                user.officer_id = user_data.get('officer_id')
                user.designation = user_data.get('designation')
                user.department = user_data.get('department')
            
            # Set password
            user.set_password(demo_password)
            db.session.add(user)
        
        db.session.commit()
        print("✅ Demo users auto-seeded successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Warning: Could not auto-seed demo users: {str(e)}")
        # Don't fail app startup if seeding fails

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Create upload directories
    with app.app_context():
        upload_folder = Path(app.config['UPLOAD_FOLDER'])
        crop_images_folder = Path(app.config['CROP_IMAGES_FOLDER'])
        ml_datasets_folder = Path(app.config['ML_DATASETS_FOLDER'])
        product_images_folder = Path(app.config['PRODUCT_IMAGES_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        crop_images_folder.mkdir(parents=True, exist_ok=True)
        ml_datasets_folder.mkdir(parents=True, exist_ok=True)
        product_images_folder.mkdir(parents=True, exist_ok=True)
    
    # Add custom Jinja2 filters
    @app.template_filter('from_json')
    def from_json_filter(value):
        import json
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return []
        return value if isinstance(value, list) else []
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Auto-seed demo users if they don't exist (for production deployment)
        seed_demo_users_if_needed()
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.farmer import farmer_bp
    from app.routes.expert import expert_bp
    from app.routes.admin import admin_bp
    from app.routes.officer import officer_bp
    from app.routes.marketplace import marketplace_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(farmer_bp, url_prefix='/farmer')
    app.register_blueprint(expert_bp, url_prefix='/expert')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(officer_bp, url_prefix='/officer')
    app.register_blueprint(marketplace_bp)
    
    return app

