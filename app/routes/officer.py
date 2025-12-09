# Krishi Bhavan Officer Module Routes
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_file, make_response
from flask_login import login_required, current_user
from app.utils.reports import generate_pdf_report, generate_csv_report
from werkzeug.utils import secure_filename
from app.models import (
    db, User, ProductRequest, Notice, Product, ProductStockHistory
)
from datetime import datetime, date, timedelta
from sqlalchemy import func, desc, and_, or_
from pathlib import Path
import os

officer_bp = Blueprint('officer', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# ==================== DASHBOARD ====================

@officer_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    # Statistics
    total_products = Product.query.count()
    low_stock_products = Product.query.filter(Product.stock_quantity < 10).count()
    total_requests = ProductRequest.query.count()
    pending_requests = ProductRequest.query.filter_by(status='pending').count()
    approved_requests = ProductRequest.query.filter_by(status='approved').count()
    total_notices = Notice.query.filter_by(posted_by=current_user.id).count()
    active_notices = Notice.query.filter_by(
        posted_by=current_user.id,
        is_active=True
    ).filter(
        or_(Notice.expires_at.is_(None), Notice.expires_at >= datetime.utcnow())
    ).count()
    
    # Recent product requests
    recent_requests = ProductRequest.query.order_by(ProductRequest.created_at.desc()).limit(5).all()
    
    # Low stock products
    low_stock = Product.query.filter(Product.stock_quantity < 10).order_by(Product.stock_quantity.asc()).limit(5).all()
    
    # Recent notices
    recent_notices = Notice.query.filter_by(posted_by=current_user.id)\
        .order_by(Notice.created_at.desc()).limit(5).all()
    
    return render_template('officer/dashboard.html',
                         total_products=total_products,
                         low_stock_products=low_stock_products,
                         total_requests=total_requests,
                         pending_requests=pending_requests,
                         approved_requests=approved_requests,
                         total_notices=total_notices,
                         active_notices=active_notices,
                         recent_requests=recent_requests,
                         low_stock=low_stock,
                         recent_notices=recent_notices)

# ==================== PRODUCT MANAGEMENT ====================

@officer_bp.route('/products')
@login_required
def products():
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    products_list = Product.query.order_by(Product.created_at.desc()).all()
    
    return render_template('officer/products.html', products=products_list)

@officer_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        product_type = request.form.get('product_type')
        description = request.form.get('description')
        stock_quantity = request.form.get('stock_quantity')
        unit = request.form.get('unit')
        is_free = request.form.get('is_free') == 'on'
        category = request.form.get('category')
        supplier = request.form.get('supplier')
        expiry_date = request.form.get('expiry_date')
        
        # Image upload
        image_path = None
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename != '' and allowed_image_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{current_user.id}_{timestamp}_{filename}"
                
                upload_folder = Path(current_app.config['PRODUCT_IMAGES_FOLDER'])
                upload_folder.mkdir(parents=True, exist_ok=True)
                
                file_path = upload_folder / filename
                file.save(str(file_path))
                image_path = f"uploads/products/{filename}"
        
        if not all([name, product_type, stock_quantity]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('officer/add_product.html')
        
        try:
            stock_qty = int(stock_quantity)
        except ValueError:
            flash('Invalid stock quantity.', 'danger')
            return render_template('officer/add_product.html')
        
        product = Product(
            name=name,
            product_type=product_type,
            description=description,
            image_path=image_path,
            stock_quantity=stock_qty,
            unit=unit,
            is_free=is_free,
            category=category,
            supplier=supplier,
            expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
            created_by=current_user.id
        )
        
        # Create stock history entry
        stock_history = ProductStockHistory(
            product_id=product.id,
            quantity_change=stock_qty,
            previous_stock=0,
            new_stock=stock_qty,
            reason='Initial stock',
            changed_by=current_user.id
        )
        
        try:
            db.session.add(product)
            db.session.flush()  # Get product ID
            stock_history.product_id = product.id
            db.session.add(stock_history)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('officer.products'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
    
    product_types = ['Seed', 'Fertilizer', 'Pesticide', 'Equipment', 'Other']
    units = ['kg', 'liter', 'piece', 'packet', 'bag', 'box']
    
    return render_template('officer/add_product.html',
                         product_types=product_types,
                         units=units)

@officer_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.product_type = request.form.get('product_type')
        product.description = request.form.get('description')
        product.stock_quantity = int(request.form.get('stock_quantity'))
        product.unit = request.form.get('unit')
        product.is_free = request.form.get('is_free') == 'on'
        product.category = request.form.get('category')
        product.supplier = request.form.get('supplier')
        expiry_date = request.form.get('expiry_date')
        product.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None
        
        # Image upload (optional update)
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename != '' and allowed_image_file(file.filename):
                # Delete old image if exists
                if product.image_path:
                    old_path = Path(current_app.config['UPLOAD_FOLDER'].parent) / 'app' / 'static' / product.image_path
                    if old_path.exists():
                        old_path.unlink()
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{current_user.id}_{timestamp}_{filename}"
                
                upload_folder = Path(current_app.config['PRODUCT_IMAGES_FOLDER'])
                upload_folder.mkdir(parents=True, exist_ok=True)
                
                file_path = upload_folder / filename
                file.save(str(file_path))
                product.image_path = f"uploads/products/{filename}"
        
        try:
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('officer.products'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
    
    product_types = ['Seed', 'Fertilizer', 'Pesticide', 'Equipment', 'Other']
    units = ['kg', 'liter', 'piece', 'packet', 'bag', 'box']
    
    return render_template('officer/edit_product.html',
                         product=product,
                         product_types=product_types,
                         units=units)

@officer_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    product = Product.query.get_or_404(product_id)
    
    # Delete image if exists
    if product.image_path:
        image_path = Path(current_app.config['UPLOAD_FOLDER'].parent) / 'app' / 'static' / product.image_path
        if image_path.exists():
            image_path.unlink()
    
    try:
        # Check if product has any requests
        has_requests = ProductRequest.query.filter_by(product_name=product.name).count() > 0
        if has_requests:
            flash('Cannot delete product. There are pending requests associated with this product.', 'warning')
            return redirect(url_for('officer.products'))
        
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the product: {str(e)}', 'danger')
    
    return redirect(url_for('officer.products'))

@officer_bp.route('/products/<int:product_id>/update-stock', methods=['POST'])
@login_required
def update_stock(product_id):
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    product = Product.query.get_or_404(product_id)
    quantity_change = int(request.form.get('quantity_change'))
    reason = request.form.get('reason', 'Stock adjustment')
    
    previous_stock = product.stock_quantity
    new_stock = previous_stock + quantity_change
    
    if new_stock < 0:
        flash('Stock cannot be negative.', 'danger')
        return redirect(url_for('officer.products'))
    
    product.stock_quantity = new_stock
    
    # Create stock history entry
    stock_history = ProductStockHistory(
        product_id=product_id,
        quantity_change=quantity_change,
        previous_stock=previous_stock,
        new_stock=new_stock,
        reason=reason,
        changed_by=current_user.id
    )
    
    try:
        db.session.add(stock_history)
        db.session.commit()
        flash('Stock updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'danger')
    
    return redirect(url_for('officer.products'))

# ==================== NOTICES MANAGEMENT ====================

@officer_bp.route('/notices')
@login_required
def notices():
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    notices_list = Notice.query.filter_by(posted_by=current_user.id)\
        .order_by(Notice.created_at.desc()).all()
    
    # Check and update expired notices
    now = datetime.utcnow()
    for notice in notices_list:
        if notice.expires_at and notice.expires_at < now and notice.is_active:
            notice.is_active = False
    db.session.commit()
    
    return render_template('officer/notices.html', notices=notices_list, current_time=now)

@officer_bp.route('/notices/add', methods=['GET', 'POST'])
@login_required
def add_notice():
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        priority = request.form.get('priority')
        target_audience = request.form.get('target_audience')
        expires_at = request.form.get('expires_at')
        is_broadcast = request.form.get('is_broadcast') == 'on'
        
        if not all([title, content]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('officer/add_notice.html')
        
        notice = Notice(
            title=title,
            content=content,
            category=category,
            priority=priority,
            posted_by=current_user.id,
            target_audience=target_audience if not is_broadcast else 'all',
            expires_at=datetime.strptime(expires_at, '%Y-%m-%d').replace(hour=23, minute=59) if expires_at else None,
            is_active=True
        )
        
        try:
            db.session.add(notice)
            db.session.commit()
            flash('Notice added successfully!', 'success')
            return redirect(url_for('officer.notices'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
    
    categories = ['Subsidy', 'Scheme', 'Alert', 'General', 'Training', 'Event']
    priorities = ['High', 'Normal', 'Low']
    audiences = ['All', 'Farmers', 'Experts']
    
    return render_template('officer/add_notice.html',
                         categories=categories,
                         priorities=priorities,
                         audiences=audiences)

@officer_bp.route('/notices/<int:notice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_notice(notice_id):
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    notice = Notice.query.get_or_404(notice_id)
    
    if notice.posted_by != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('officer.notices'))
    
    if request.method == 'POST':
        notice.title = request.form.get('title')
        notice.content = request.form.get('content')
        notice.category = request.form.get('category')
        notice.priority = request.form.get('priority')
        notice.target_audience = request.form.get('target_audience')
        expires_at = request.form.get('expires_at')
        notice.expires_at = datetime.strptime(expires_at, '%Y-%m-%d').replace(hour=23, minute=59) if expires_at else None
        notice.is_active = request.form.get('is_active') == 'on'
        
        try:
            db.session.commit()
            flash('Notice updated successfully!', 'success')
            return redirect(url_for('officer.notices'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
    
    categories = ['Subsidy', 'Scheme', 'Alert', 'General', 'Training', 'Event']
    priorities = ['High', 'Normal', 'Low']
    audiences = ['All', 'Farmers', 'Experts']
    
    return render_template('officer/edit_notice.html',
                         notice=notice,
                         categories=categories,
                         priorities=priorities,
                         audiences=audiences)

@officer_bp.route('/notices/<int:notice_id>/delete', methods=['POST'])
@login_required
def delete_notice(notice_id):
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    notice = Notice.query.get_or_404(notice_id)
    
    if notice.posted_by != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('officer.notices'))
    
    try:
        db.session.delete(notice)
        db.session.commit()
        flash('Notice deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'danger')
    
    return redirect(url_for('officer.notices'))

# ==================== PRODUCT REQUESTS ====================

@officer_bp.route('/product-requests')
@login_required
def product_requests():
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    requests_list = ProductRequest.query.order_by(ProductRequest.created_at.desc()).all()
    
    return render_template('officer/product_requests.html', requests=requests_list)

@officer_bp.route('/product-requests/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_request(request_id):
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    product_request = ProductRequest.query.get_or_404(request_id)
    
    # Check if product exists and has stock
    # In a real system, you'd match the product request to actual products
    # For now, we'll just approve it
    
    product_request.status = 'approved'
    product_request.approved_by = current_user.id
    product_request.approval_date = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Product request approved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'danger')
    
    return redirect(url_for('officer.product_requests'))

@officer_bp.route('/product-requests/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    product_request = ProductRequest.query.get_or_404(request_id)
    
    rejection_reason = request.form.get('rejection_reason', 'Request rejected by officer')
    
    product_request.status = 'rejected'
    product_request.approved_by = current_user.id
    product_request.approval_date = datetime.utcnow()
    product_request.rejection_reason = rejection_reason
    
    try:
        db.session.commit()
        flash('Product request rejected.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred.', 'danger')
    
    return redirect(url_for('officer.product_requests'))

# ==================== REPORTS ====================

@officer_bp.route('/reports/stock/pdf')
@login_required
def report_stock_pdf():
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    products = Product.query.order_by(Product.product_type, Product.name).all()
    
    data = []
    for product in products:
        # Get stock history summary
        stock_changes = ProductStockHistory.query.filter_by(product_id=product.id)\
            .order_by(ProductStockHistory.created_at.desc()).limit(5).all()
        recent_change = stock_changes[0] if stock_changes else None
        
        data.append({
            'ID': product.id,
            'Product Name': product.name,
            'Type': product.product_type,
            'Stock': f"{product.stock_quantity} {product.unit}",
            'Status': 'Low Stock' if product.stock_quantity < 10 else 'Adequate',
            'Category': product.category or 'N/A',
            'Supplier': product.supplier or 'N/A',
            'Free Product': 'Yes' if product.is_free else 'No',
            'Last Updated': recent_change.created_at.strftime('%Y-%m-%d') if recent_change else 'N/A'
        })
    
    summary = {
        'Total Products': len(products),
        'Low Stock Items': len([p for p in products if p.stock_quantity < 10]),
        'Total Stock Value': 'N/A',  # Can be calculated if price_per_unit is set
        'Free Products': len([p for p in products if p.is_free])
    }
    
    pdf_buffer = generate_pdf_report(
        data,
        'Stock Report',
        current_user.full_name,
        subtitle=f"Krishi Bhavan Officer: {current_user.full_name}",
        summary=summary
    )
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'stock_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@officer_bp.route('/reports/stock/csv')
@login_required
def report_stock_csv():
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    
    products = Product.query.order_by(Product.product_type, Product.name).all()
    
    data = []
    for product in products:
        data.append({
            'ID': product.id,
            'Product Name': product.name,
            'Type': product.product_type,
            'Stock': f"{product.stock_quantity} {product.unit}",
            'Status': 'Low Stock' if product.stock_quantity < 10 else 'Adequate',
            'Category': product.category or 'N/A',
            'Supplier': product.supplier or 'N/A',
            'Free Product': 'Yes' if product.is_free else 'No',
            'Created': product.created_at.strftime('%Y-%m-%d') if hasattr(product, 'created_at') else 'N/A'
        })
    
    csv_data = generate_csv_report(data, 'stock')
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=stock_report_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

