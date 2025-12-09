# Authentication Routes
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# ==================== FARMER ROUTES ====================

@auth_bp.route('/farmer/register', methods=['GET', 'POST'])
def farmer_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        farm_size = request.form.get('farm_size')
        farm_location = request.form.get('farm_location')
        
        # Validation
        if not all([username, email, password, full_name]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/farmer_register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/farmer_register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/farmer_register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('auth/farmer_register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            address=address,
            role='farmer',
            farm_size=float(farm_size) if farm_size else None,
            farm_location=farm_location
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.farmer_login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/farmer_register.html')

@auth_bp.route('/farmer/login', methods=['GET', 'POST'])
def farmer_login():
    if current_user.is_authenticated and current_user.is_farmer():
        return redirect(url_for('auth.farmer_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/farmer_login.html')
        
        user = User.query.filter_by(username=username, role='farmer').first()
        
        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            session['role'] = 'farmer'
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('auth.farmer_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/farmer_login.html')

@auth_bp.route('/farmer/dashboard')
@login_required
def farmer_dashboard():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    return redirect(url_for('farmer.dashboard'))

# ==================== EXPERT ROUTES ====================

@auth_bp.route('/expert/register', methods=['GET', 'POST'])
def expert_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        expertise_area = request.form.get('expertise_area')
        qualifications = request.form.get('qualifications')
        years_of_experience = request.form.get('years_of_experience')
        
        # Validation
        if not all([username, email, password, full_name]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/expert_register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/expert_register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/expert_register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('auth/expert_register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            address=address,
            role='expert',
            expertise_area=expertise_area,
            qualifications=qualifications,
            years_of_experience=int(years_of_experience) if years_of_experience else None
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.expert_login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/expert_register.html')

@auth_bp.route('/expert/login', methods=['GET', 'POST'])
def expert_login():
    if current_user.is_authenticated and current_user.is_expert():
        return redirect(url_for('auth.expert_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/expert_login.html')
        
        user = User.query.filter_by(username=username, role='expert').first()
        
        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            session['role'] = 'expert'
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('auth.expert_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/expert_login.html')

@auth_bp.route('/expert/dashboard')
@login_required
def expert_dashboard():
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    return redirect(url_for('expert.dashboard'))

# ==================== ADMIN ROUTES ====================

@auth_bp.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        # Validation
        if not all([username, email, password, full_name]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/admin_register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/admin_register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/admin_register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('auth/admin_register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role='admin'
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.admin_login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/admin_register.html')

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin():
        return redirect(url_for('auth.admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/admin_login.html')
        
        user = User.query.filter_by(username=username, role='admin').first()
        
        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            session['role'] = 'admin'
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('auth.admin_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/admin_login.html')

@auth_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    return redirect(url_for('admin.dashboard'))

# ==================== KRISHI BHAVAN OFFICER ROUTES ====================

@auth_bp.route('/krishi-bhavan-officer/register', methods=['GET', 'POST'])
def krishi_bhavan_officer_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        officer_id = request.form.get('officer_id')
        designation = request.form.get('designation')
        department = request.form.get('department')
        
        # Validation
        if not all([username, email, password, full_name, officer_id]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/krishi_bhavan_officer_register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/krishi_bhavan_officer_register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/krishi_bhavan_officer_register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('auth/krishi_bhavan_officer_register.html')
        
        if User.query.filter_by(officer_id=officer_id).first():
            flash('Officer ID already exists.', 'danger')
            return render_template('auth/krishi_bhavan_officer_register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            address=address,
            role='krishi_bhavan_officer',
            officer_id=officer_id,
            designation=designation,
            department=department
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.krishi_bhavan_officer_login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/krishi_bhavan_officer_register.html')

@auth_bp.route('/krishi-bhavan-officer/login', methods=['GET', 'POST'])
def krishi_bhavan_officer_login():
    if current_user.is_authenticated and current_user.is_krishi_bhavan_officer():
        return redirect(url_for('auth.krishi_bhavan_officer_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/krishi_bhavan_officer_login.html')
        
        user = User.query.filter_by(username=username, role='krishi_bhavan_officer').first()
        
        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            session['role'] = 'krishi_bhavan_officer'
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('auth.krishi_bhavan_officer_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/krishi_bhavan_officer_login.html')

@auth_bp.route('/krishi-bhavan-officer/dashboard')
@login_required
def krishi_bhavan_officer_dashboard():
    if not current_user.is_krishi_bhavan_officer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.krishi_bhavan_officer_login'))
    return redirect(url_for('officer.dashboard'))

# ==================== LOGOUT ====================

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    
    # Clear explicit session keys just in case
    for key in list(session.keys()):
        session.pop(key, None)
    session.clear()
    
    flash('You have been logged out successfully.', 'info')
    
    # Create response and prevent caching
    from flask import make_response
    response = make_response(redirect(url_for('main.index')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Explicitly delete remember me cookie if it exists
    response.set_cookie('remember_token', '', expires=0)
    
    return response

