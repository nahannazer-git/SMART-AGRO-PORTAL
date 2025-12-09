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
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.farmer import farmer_bp
    from app.routes.expert import expert_bp
    from app.routes.admin import admin_bp
    from app.routes.officer import officer_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(farmer_bp, url_prefix='/farmer')
    app.register_blueprint(expert_bp, url_prefix='/expert')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(officer_bp, url_prefix='/officer')
    
    return app

