# Public Agro Marketplace Routes
# This module handles the public marketplace for farmers to sell products
# NO impact on existing features - completely isolated

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, FarmerProduct, User, ChatMessage
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from flask import current_app

marketplace_bp = Blueprint('marketplace', __name__, url_prefix='/marketplace')


# ============================================================================
# PUBLIC MARKETPLACE ROUTES (No login required)
# ============================================================================

@marketplace_bp.route('/')
def index():
    """Public marketplace listing page - View all available products"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category = request.args.get('category', '', type=str)
    
    query = FarmerProduct.query.filter_by(is_available=True)
    
    # Search by product name
    if search:
        query = query.filter(FarmerProduct.product_name.ilike(f'%{search}%'))
    
    # Filter by category
    if category:
        query = query.filter_by(category=category)
    
    # Order by newest first
    products = query.order_by(FarmerProduct.created_at.desc()).paginate(page=page, per_page=12)
    
    # Get all categories for filter dropdown
    categories = db.session.query(FarmerProduct.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('marketplace/index.html', 
                         products=products,
                         categories=categories,
                         search=search,
                         selected_category=category)


@marketplace_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page with farmer contact info"""
    product = FarmerProduct.query.get_or_404(product_id)
    
    if not product.is_available:
        flash('This product is no longer available.', 'warning')
        return redirect(url_for('marketplace.index'))
    
    farmer = User.query.get(product.farmer_id)
    
    if not farmer:
        flash('Farmer information not found for this product.', 'warning')
        return redirect(url_for('marketplace.index'))
    
    return render_template('marketplace/product_detail.html', 
                         product=product,
                         farmer=farmer)


@marketplace_bp.route('/contact-farmer', methods=['POST'])
def contact_farmer():
    """
    Public users can contact farmer for product inquiry
    Creates a chat message without requiring login
    """
    product_id = request.form.get('product_id')
    farmer_id = request.form.get('farmer_id')
    message = request.form.get('message', '').strip()
    visitor_name = request.form.get('visitor_name', 'Guest').strip()
    visitor_phone = request.form.get('visitor_phone', '').strip()
    
    if not message:
        return jsonify({'status': 'error', 'message': 'Message cannot be empty'}), 400
    
    product = FarmerProduct.query.get_or_404(product_id)
    
    try:
        # Create a message (as a public inquiry)
        # We store visitor info in the message content or create a special record
        inquiry_message = f"[Public Inquiry] {visitor_name} ({visitor_phone}): {message}"
        
        chat_message = ChatMessage(
            farmer_id=farmer_id,
            expert_id=None,  # Not an expert conversation
            message=inquiry_message,
            sender_role='public',  # New role for public marketplace inquiries
            is_read=False
        )
        
        db.session.add(chat_message)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Your inquiry has been sent to the farmer!'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"Error sending inquiry: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# FARMER PRODUCT MANAGEMENT ROUTES (Login required - Farmer only)
# ============================================================================

@marketplace_bp.route('/my-products')
@login_required
def my_products():
    """Farmer's product management dashboard"""
    if not current_user.is_farmer():
        flash('Access denied. Only farmers can manage products.', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    products = FarmerProduct.query.filter_by(farmer_id=current_user.id)\
                              .order_by(FarmerProduct.created_at.desc())\
                              .paginate(page=page, per_page=10)
    
    return render_template('marketplace/my_products.html', products=products)


@marketplace_bp.route('/products/new', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new product for sale"""
    if not current_user.is_farmer():
        flash('Access denied. Only farmers can add products.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        product_name = request.form.get('product_name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        quantity = request.form.get('quantity', type=float)
        unit = request.form.get('unit', '').strip()
        price = request.form.get('price_per_unit', type=float)
        location = request.form.get('location', '').strip()
        
        # Validate
        if not all([product_name, category, quantity, unit, price]):
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('marketplace.add_product'))
        
        if quantity <= 0 or price <= 0:
            flash('Quantity and price must be greater than 0.', 'danger')
            return redirect(url_for('marketplace.add_product'))
        
        # Handle image upload
        image_path = None
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename != '':
                if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'farmer_products')
                    os.makedirs(upload_dir, exist_ok=True)
                    filename = secure_filename(f"product_{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}")
                    file.save(os.path.join(upload_dir, filename))
                    image_path = f"uploads/farmer_products/{filename}"
                else:
                    flash('Only image files are allowed.', 'danger')
                    return redirect(url_for('marketplace.add_product'))
        
        try:
            product = FarmerProduct(
                farmer_id=current_user.id,
                product_name=product_name,
                category=category,
                description=description,
                quantity=quantity,
                unit=unit,
                price_per_unit=price,
                location=location or current_user.location,
                product_image_path=image_path,
                is_available=True
            )
            
            db.session.add(product)
            db.session.commit()
            
            flash(f'Product "{product_name}" added successfully!', 'success')
            return redirect(url_for('marketplace.my_products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
            return redirect(url_for('marketplace.add_product'))
    
    return render_template('marketplace/add_product.html')


@marketplace_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit product details"""
    product = FarmerProduct.query.get_or_404(product_id)
    
    # Authorization check
    if product.farmer_id != current_user.id:
        flash('You can only edit your own products.', 'danger')
        return redirect(url_for('marketplace.my_products'))
    
    if request.method == 'POST':
        product.product_name = request.form.get('product_name', '').strip()
        product.category = request.form.get('category', '').strip()
        product.description = request.form.get('description', '').strip()
        product.quantity = request.form.get('quantity', type=float)
        product.unit = request.form.get('unit', '').strip()
        product.price_per_unit = request.form.get('price_per_unit', type=float)
        product.location = request.form.get('location', '').strip()
        
        # Validate
        if not all([product.product_name, product.category, product.quantity, product.unit, product.price_per_unit]):
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('marketplace.edit_product', product_id=product_id))
        
        if product.quantity <= 0 or product.price_per_unit <= 0:
            flash('Quantity and price must be greater than 0.', 'danger')
            return redirect(url_for('marketplace.edit_product', product_id=product_id))
        
        # Handle image upload
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename != '':
                if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'farmer_products')
                    os.makedirs(upload_dir, exist_ok=True)
                    filename = secure_filename(f"product_{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}")
                    file.save(os.path.join(upload_dir, filename))
                    product.product_image_path = f"uploads/farmer_products/{filename}"
                else:
                    flash('Only image files are allowed.', 'danger')
        
        try:
            product.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('marketplace.my_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
            return redirect(url_for('marketplace.edit_product', product_id=product_id))
    
    return render_template('marketplace/edit_product.html', product=product)


@marketplace_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete/Archive product"""
    product = FarmerProduct.query.get_or_404(product_id)
    
    # Authorization check
    if product.farmer_id != current_user.id:
        flash('You can only delete your own products.', 'danger')
        return redirect(url_for('marketplace.my_products'))
    
    try:
        # Soft delete - mark as unavailable instead of hard delete
        product.is_available = False
        product.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Product removed from marketplace.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')
    
    return redirect(url_for('marketplace.my_products'))


@marketplace_bp.route('/products/<int:product_id>/toggle-availability', methods=['POST'])
@login_required
def toggle_availability(product_id):
    """Toggle product availability on/off"""
    product = FarmerProduct.query.get_or_404(product_id)
    
    # Authorization check
    if product.farmer_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    try:
        product.is_available = not product.is_available
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'is_available': product.is_available,
            'message': f'Product is now {"available" if product.is_available else "unavailable"}'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
