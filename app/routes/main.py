# Main Routes
from flask import Blueprint, redirect, url_for, render_template
from app.models import Product
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

