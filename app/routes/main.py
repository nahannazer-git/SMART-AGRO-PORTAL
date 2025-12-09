# Main Routes
from flask import Blueprint, redirect, url_for, render_template, jsonify
from app.models import Product, db, User
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page - Central Portal Landing"""
    # If user is already logged in, redirect to their dashboard
    if current_user.is_authenticated:
        if current_user.is_farmer():
            return redirect(url_for('farmer.dashboard'))
        elif current_user.is_expert():
            return redirect(url_for('expert.dashboard'))
        elif current_user.role == 'krishi_bhavan_officer':
            return redirect(url_for('officer.dashboard'))
            
    return render_template('landing.html')

@main_bp.route('/marketplace')
def marketplace():
    """Public Public Marketplace/Notice Page"""
    # Get all active products with stock > 0
    products = Product.query.filter(
        Product.stock_quantity > 0,
        Product.is_active == True
    ).order_by(Product.created_at.desc()).all()
    
    return render_template('marketplace.html', products=products)

@main_bp.route('/seed-users')
def seed_users_manual():
    """Manual endpoint to seed demo users (for debugging)"""
    try:
        # Import the seeding function from the app module
        from app import seed_demo_users_if_needed
        
        # Run seeding (already in app context from route handler)
        seed_demo_users_if_needed()
        
        # Check if users were created
        users = User.query.all()
        user_list = [{'username': u.username, 'role': u.role, 'email': u.email} for u in users]
        
        return jsonify({
            'status': 'success',
            'message': 'Seeding completed. Check logs for details.',
            'total_users': len(users),
            'users': user_list
        }), 200
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

@main_bp.route('/check-users')
def check_users():
    """Check if demo users exist"""
    try:
        demo_users = ['farmer_demo', 'expert_demo', 'admin_demo', 'officer_demo']
        result = {}
        
        for username in demo_users:
            user = User.query.filter_by(username=username).first()
            result[username] = {
                'exists': user is not None,
                'role': user.role if user else None,
                'email': user.email if user else None,
                'is_active': user.is_active if user else None
            }
        
        total_users = User.query.count()
        
        return jsonify({
            'status': 'success',
            'total_users_in_db': total_users,
            'demo_users': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

