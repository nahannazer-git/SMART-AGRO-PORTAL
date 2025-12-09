# Farmer Module Routes
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file, session, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, CropIssue, YieldPrediction, Notice, ProductRequest, ChatMessage, User, ExpertRating, DiagnosisReport
from app.utils.weather import get_weather_data, get_temperature_for_location
from app.utils.ml_helpers import predict_disease, predict_yield
from app.utils.reports import generate_pdf_report, generate_csv_report
from datetime import datetime, date
from sqlalchemy import func
import json
import os
import time
from pathlib import Path

farmer_bp = Blueprint('farmer', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== DASHBOARD ====================

@farmer_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    # Get weather data
    location = current_user.farm_location or "Kerala, India"
    weather = get_weather_data(location)
    
    # Get statistics
    total_issues = CropIssue.query.filter_by(farmer_id=current_user.id).count()
    pending_issues = CropIssue.query.filter_by(farmer_id=current_user.id, status='pending').count()
    total_predictions = YieldPrediction.query.filter_by(farmer_id=current_user.id).count()
    active_chats = ChatMessage.query.filter_by(farmer_id=current_user.id).distinct(ChatMessage.expert_id).count()
    
    # Recent issues
    recent_issues = CropIssue.query.filter_by(farmer_id=current_user.id)\
        .order_by(CropIssue.created_at.desc()).limit(5).all()
    
    # Recent notices
    recent_notices = Notice.query.filter_by(is_active=True)\
        .filter(Notice.target_audience.in_(['all', 'farmers']))\
        .order_by(Notice.created_at.desc()).limit(5).all()
    
    # Marketplace inquiries count
    marketplace_inquiries_count = ChatMessage.query.filter_by(
        farmer_id=current_user.id,
        sender_role='public',
        is_read=False
    ).count()
    
    return render_template('farmer/dashboard.html', 
                         weather=weather,
                         total_issues=total_issues,
                         pending_issues=pending_issues,
                         total_predictions=total_predictions,
                         active_chats=active_chats,
                         recent_issues=recent_issues,
                         recent_notices=recent_notices,
                         marketplace_inquiries_count=marketplace_inquiries_count)

# ==================== CROP ISSUE SUBMISSION ====================

@farmer_bp.route('/crop-issue/new', methods=['GET', 'POST'])
@login_required
def new_crop_issue():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    if request.method == 'POST':
        crop_type = request.form.get('crop_type')
        crop_variety = request.form.get('crop_variety')
        planting_date = request.form.get('planting_date')
        issue_description = request.form.get('issue_description')
        symptoms = request.form.getlist('symptoms')  # Multiple symptoms
        location = request.form.get('location')
        
        # Image upload
        image_path = None
        if 'crop_image' in request.files:
            file = request.files['crop_image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{current_user.id}_{timestamp}_{filename}"
                
                upload_folder = Path(current_app.config['CROP_IMAGES_FOLDER'])
                upload_folder.mkdir(parents=True, exist_ok=True)
                
                file_path = upload_folder / filename
                file.save(str(file_path))
                image_path = f"uploads/crops/{filename}"
        
        # Validation
        if not all([crop_type, issue_description]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('farmer/new_crop_issue.html')
        
        # Create crop issue
        crop_issue = CropIssue(
            farmer_id=current_user.id,
            crop_type=crop_type,
            crop_variety=crop_variety,
            planting_date=datetime.strptime(planting_date, '%Y-%m-%d').date() if planting_date else None,
            issue_description=issue_description,
            symptoms=json.dumps(symptoms),
            image_path=image_path,
            location=location or current_user.farm_location
        )
        
        # AI Disease Prediction
        if image_path or symptoms:
            ai_prediction = predict_disease(image_path, symptoms, crop_type)
            crop_issue.ai_prediction = ai_prediction
        
        try:
            db.session.add(crop_issue)
            db.session.commit()
            flash('Crop issue submitted successfully! AI prediction is available.', 'success')
            return redirect(url_for('farmer.view_disease_prediction', issue_id=crop_issue.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while submitting your crop issue: {str(e)}. Please try again.', 'danger')
    
    # Symptom options for dropdown
    symptom_options = [
        'Yellowing leaves', 'Brown spots', 'Wilting', 'Stunted growth',
        'Leaf curling', 'White powdery substance', 'Black spots',
        'Holes in leaves', 'Discolored stems', 'Root rot', 'Fruit drop',
        'Flower drop', 'Mosaic pattern', 'Necrosis', 'Chlorosis'
    ]
    
    crop_types = ['Rice', 'Wheat', 'Corn', 'Tomato', 'Potato', 'Cotton', 'Sugarcane', 'Other']
    
    return render_template('farmer/new_crop_issue.html',
                         symptom_options=symptom_options,
                         crop_types=crop_types)

# ==================== YIELD PREDICTION ====================

@farmer_bp.route('/yield-prediction/new', methods=['GET', 'POST'])
@login_required
def new_yield_prediction():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    if request.method == 'POST':
        crop_type = request.form.get('crop_type')
        crop_variety = request.form.get('crop_variety')
        soil_type = request.form.get('soil_type')
        irrigation_type = request.form.get('irrigation_type')
        fertilizer_type = request.form.get('fertilizer_type')
        planting_date = request.form.get('planting_date')
        farm_size = request.form.get('farm_size')
        location = request.form.get('location')
        
        # Auto-fetch temperature and rainfall from weather API
        location_for_weather = location or current_user.farm_location or "Kerala, India"
        weather_data = get_weather_data(location_for_weather)
        temperature = float(request.form.get('temperature', weather_data.get('temperature', 28.0)))
        rainfall = weather_data.get('rain_chance', 0.0) * 100  # Convert to mm estimate (simplified)
        
        # Validation
        if not all([crop_type, soil_type, irrigation_type, fertilizer_type, planting_date, farm_size, location]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('farmer/new_yield_prediction.html', temperature=temperature)
        
        try:
            farm_size_float = float(farm_size)
            planting_date_obj = datetime.strptime(planting_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid data format.', 'danger')
            return render_template('farmer/new_yield_prediction.html', temperature=temperature)
        
        # AI Yield Prediction
        prediction_result = predict_yield(
            crop_type, soil_type, irrigation_type, fertilizer_type,
            temperature, rainfall, farm_size_float, location
        )
        
        # Create yield prediction record
        yield_prediction = YieldPrediction(
            farmer_id=current_user.id,
            crop_type=crop_type,
            crop_variety=crop_variety,
            soil_type=soil_type,
            irrigation_type=irrigation_type,
            fertilizer_type=fertilizer_type,
            planting_date=planting_date_obj,
            temperature=temperature,
            rainfall=rainfall,
            farm_size=farm_size_float,
            location=location,
            predicted_yield=prediction_result['predicted_yield_per_acre'],
            confidence_score=prediction_result['confidence_score'],
            ai_model_used='yield_predictor_v1'
        )
        
        try:
            db.session.add(yield_prediction)
            db.session.commit()
            flash('Yield prediction generated successfully!', 'success')
            return redirect(url_for('farmer.view_yield_prediction', prediction_id=yield_prediction.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while processing your yield prediction: {str(e)}. Please try again.', 'danger')
    
    # Get current weather data for display
    location = current_user.farm_location or "Kerala, India"
    weather_data = get_weather_data(location)
    temperature = weather_data.get('temperature', 28.0)
    
    crop_types = ['Rice', 'Wheat', 'Corn', 'Tomato', 'Potato', 'Cotton', 'Sugarcane', 'Other']
    soil_types = ['Loamy', 'Clay', 'Sandy', 'Silt', 'Red Soil', 'Black Soil']
    irrigation_types = ['Drip', 'Sprinkler', 'Flood', 'Rainfed', 'Furrow']
    fertilizer_types = ['Organic', 'Chemical', 'Mixed', 'None', 'Bio-fertilizer']
    
    return render_template('farmer/new_yield_prediction.html',
                         crop_types=crop_types,
                         soil_types=soil_types,
                         irrigation_types=irrigation_types,
                         fertilizer_types=fertilizer_types,
                         temperature=temperature)

# ==================== VIEW PREDICTIONS ====================

@farmer_bp.route('/disease-prediction/<int:issue_id>')
@login_required
def view_disease_prediction(issue_id):
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    issue = CropIssue.query.get_or_404(issue_id)
    
    if issue.farmer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('farmer.dashboard'))
    
    prediction_data = None
    if issue.ai_prediction:
        try:
            prediction_data = json.loads(issue.ai_prediction)
        except:
            pass
    
    # Get diagnosis report if available
    diagnosis_report = DiagnosisReport.query.filter_by(crop_issue_id=issue_id).first()
    
    # Check if farmer has already rated this expert for this issue
    existing_rating = None
    if diagnosis_report:
        existing_rating = ExpertRating.query.filter_by(
            farmer_id=current_user.id,
            expert_id=diagnosis_report.expert_id,
            crop_issue_id=issue_id
        ).first()
    
    return render_template('farmer/view_disease_prediction.html',
                         issue=issue,
                         prediction=prediction_data,
                         diagnosis_report=diagnosis_report,
                         existing_rating=existing_rating)

@farmer_bp.route('/yield-prediction/<int:prediction_id>')
@login_required
def view_yield_prediction(prediction_id):
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    prediction = YieldPrediction.query.get_or_404(prediction_id)
    
    if prediction.farmer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('farmer.dashboard'))
    
    return render_template('farmer/view_yield_prediction.html',
                         prediction=prediction)

# ==================== NOTICES ====================

@farmer_bp.route('/notices')
@login_required
def notices():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    notices_list = Notice.query.filter_by(is_active=True)\
        .filter(Notice.target_audience.in_(['all', 'farmers']))\
        .order_by(Notice.created_at.desc()).all()
    
    return render_template('farmer/notices.html', notices=notices_list)

# ==================== PRODUCT REQUESTS ====================

@farmer_bp.route('/product-request/new', methods=['GET', 'POST'])
@login_required
def new_product_request():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        product_type = request.form.get('product_type')
        quantity = request.form.get('quantity')
        unit = request.form.get('unit')
        purpose = request.form.get('purpose')
        
        if not all([product_name, product_type, quantity]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('farmer/new_product_request.html')
        
        try:
            quantity_int = int(quantity)
        except ValueError:
            flash('Invalid quantity.', 'danger')
            return render_template('farmer/new_product_request.html')
        
        product_request = ProductRequest(
            farmer_id=current_user.id,
            product_name=product_name,
            product_type=product_type,
            quantity=quantity_int,
            unit=unit,
            purpose=purpose
        )
        
        try:
            db.session.add(product_request)
            db.session.commit()
            flash('Product request submitted successfully!', 'success')
            return redirect(url_for('farmer.product_requests'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
    
    product_types = ['Seed', 'Fertilizer', 'Pesticide', 'Equipment', 'Other']
    units = ['kg', 'liter', 'piece', 'packet', 'bag']
    
    return render_template('farmer/new_product_request.html',
                         product_types=product_types,
                         units=units)

@farmer_bp.route('/product-requests')
@login_required
def product_requests():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    requests_list = ProductRequest.query.filter_by(farmer_id=current_user.id)\
        .order_by(ProductRequest.created_at.desc()).all()
    
    return render_template('farmer/product_requests.html', requests=requests_list)

# ==================== CHAT WITH EXPERT ====================

@farmer_bp.route('/chat')
@login_required
def chat_list():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    # Get unique experts that farmer has chatted with with unread counts
    experts_with_unread = db.session.query(
        User,
        func.count(ChatMessage.id).label('unread_count')
    ).join(ChatMessage, User.id == ChatMessage.expert_id)\
     .filter(ChatMessage.farmer_id == current_user.id)\
     .filter(ChatMessage.sender_role == 'expert', ChatMessage.is_read == False)\
     .group_by(User.id).all()
    
    # Get all experts farmer has chatted with
    experts = db.session.query(User).join(ChatMessage, User.id == ChatMessage.expert_id)\
        .filter(ChatMessage.farmer_id == current_user.id)\
        .distinct().all()
    
    # Create unread count dict
    unread_counts = {expert.id: count for expert, count in experts_with_unread}
    for expert in experts:
        if expert.id not in unread_counts:
            unread_counts[expert.id] = 0
    
    # Also get all available experts
    all_experts = User.query.filter_by(role='expert', is_active=True).all()
    
    # Get total unread count
    total_unread = ChatMessage.query.filter(
        ChatMessage.farmer_id == current_user.id,
        ChatMessage.sender_role == 'expert',
        ChatMessage.is_read == False
    ).count()
    
    return render_template('farmer/chat_list.html',
                         experts=experts,
                         all_experts=all_experts,
                         unread_counts=unread_counts,
                         total_unread=total_unread)

@farmer_bp.route('/chat/<int:expert_id>', methods=['GET', 'POST'])
@login_required
def chat_with_expert(expert_id):
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    expert = User.query.get_or_404(expert_id)
    if not expert.is_expert():
        flash('Invalid expert.', 'danger')
        return redirect(url_for('farmer.chat_list'))
    
    if request.method == 'POST':
        message = request.form.get('message')
        related_issue_id = request.form.get('related_issue_id')
        image = request.files.get('image')
        image_path = None
        
        if image:
            from werkzeug.utils import secure_filename
            import os
            
            # Ensure upload directory exists
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'chat_images')
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = secure_filename(f"chat_{int(datetime.utcnow().timestamp())}_{image.filename}")
            image.save(os.path.join(upload_dir, filename))
            image_path = f"uploads/chat_images/{filename}"

        if message or image_path:
            chat_message = ChatMessage(
                farmer_id=current_user.id,
                expert_id=expert_id,
                message=message if message else "Sent an image",  # Fallback text if just image
                sender_role='farmer',
                related_issue_id=int(related_issue_id) if related_issue_id else None,
                image_path=image_path
            )
            
            try:
                db.session.add(chat_message)
                db.session.commit()
                # Return JSON for AJAX
                return jsonify({
                    'status': 'success', 
                    'message': 'Message sent!',
                    'data': {
                        'id': chat_message.id,
                        'message': chat_message.message,
                        'image_path': chat_message.image_path,
                        'created_at': chat_message.created_at.strftime('%Y-%m-%d %H:%M'),
                        'sender_role': 'farmer'
                    }
                })
            except Exception as e:
                db.session.rollback()
                print(f"Error sending message: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
    # Get chat messages
    messages = ChatMessage.query.filter(
        ChatMessage.farmer_id == current_user.id,
        ChatMessage.expert_id == expert_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # Mark messages as read
    for msg in messages:
        if msg.sender_role == 'expert' and not msg.is_read:
            msg.is_read = True
    db.session.commit()
    
    # Get farmer's crop issues for linking
    crop_issues = CropIssue.query.filter_by(farmer_id=current_user.id).all()
    
    return render_template('farmer/chat.html',
                         expert=expert,
                         messages=messages,
                         crop_issues=crop_issues,
                         last_message_id=messages[-1].id if messages else 0)

@farmer_bp.route('/chat/<int:expert_id>/poll')
@login_required
def chat_poll(expert_id):
    """Long-polling endpoint to check for new messages"""
    if not current_user.is_farmer():
        return jsonify({'error': 'Access denied'}), 403
    
    last_message_id = request.args.get('last_message_id', 0, type=int)
    timeout = 30  # seconds
    
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check for new messages
        new_messages = ChatMessage.query.filter(
            ChatMessage.farmer_id == current_user.id,
            ChatMessage.expert_id == expert_id,
            ChatMessage.id > last_message_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        if new_messages:
            # Mark expert messages as read
            for msg in new_messages:
                if msg.sender_role == 'expert' and not msg.is_read:
                    msg.is_read = True
            db.session.commit()
            
            messages_data = []
            for msg in new_messages:
                messages_data.append({
                    'id': msg.id,
                    'message': msg.message,
                    'sender_role': msg.sender_role,
                    'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'time_display': msg.created_at.strftime('%Y-%m-%d %H:%M')
                })
            
            return jsonify({
                'new_messages': messages_data,
                'last_message_id': new_messages[-1].id
            })
        
        time.sleep(1)  # Check every second
    
    # Timeout - no new messages
    return jsonify({'new_messages': [], 'last_message_id': last_message_id})

@farmer_bp.route('/chat/unread-count')
@login_required
def chat_unread_count():
    """Get unread message count for farmer"""
    if not current_user.is_farmer():
        return jsonify({'error': 'Access denied'}), 403
    
    unread_count = ChatMessage.query.filter(
        ChatMessage.farmer_id == current_user.id,
        ChatMessage.sender_role == 'expert',
        ChatMessage.is_read == False
    ).count()
    
    return jsonify({'unread_count': unread_count})

# ==================== RATINGS ====================

@farmer_bp.route('/rate-expert', methods=['POST'])
@login_required
def rate_expert():
    """Submit rating for an expert"""
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    expert_id = request.form.get('expert_id', type=int)
    issue_id = request.form.get('issue_id', type=int)
    rating_value = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    
    # Validation
    if not all([expert_id, issue_id, rating_value]):
        flash('Please provide all required information.', 'danger')
        return redirect(url_for('farmer.view_disease_prediction', issue_id=issue_id))
    
    if rating_value < 1 or rating_value > 5:
        flash('Rating must be between 1 and 5.', 'danger')
        return redirect(url_for('farmer.view_disease_prediction', issue_id=issue_id))
    
    # Verify the issue belongs to the farmer
    issue = CropIssue.query.get_or_404(issue_id)
    if issue.farmer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('farmer.dashboard'))
    
    # Verify expert exists and has diagnosed this issue
    expert = User.query.get_or_404(expert_id)
    if not expert.is_expert():
        flash('Invalid expert.', 'danger')
        return redirect(url_for('farmer.view_disease_prediction', issue_id=issue_id))
    
    diagnosis_report = DiagnosisReport.query.filter_by(
        crop_issue_id=issue_id,
        expert_id=expert_id
    ).first()
    
    if not diagnosis_report:
        flash('This expert has not diagnosed this issue yet.', 'danger')
        return redirect(url_for('farmer.view_disease_prediction', issue_id=issue_id))
    
    # Check if rating already exists
    existing_rating = ExpertRating.query.filter_by(
        farmer_id=current_user.id,
        expert_id=expert_id,
        crop_issue_id=issue_id
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_value
        existing_rating.comment = comment
        try:
            db.session.commit()
            flash('Rating updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating rating: {str(e)}', 'danger')
    else:
        # Create new rating
        rating = ExpertRating(
            farmer_id=current_user.id,
            expert_id=expert_id,
            crop_issue_id=issue_id,
            rating=rating_value,
            comment=comment
        )
        try:
            db.session.add(rating)
            db.session.commit()
            flash('Thank you for rating the expert!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting rating: {str(e)}', 'danger')
    
    return redirect(url_for('farmer.view_disease_prediction', issue_id=issue_id))

# ==================== MARKETPLACE INQUIRIES ====================

@farmer_bp.route('/marketplace-inquiries')
@login_required
def marketplace_inquiries():
    """View inquiries from public users on marketplace products"""
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    # Get sort parameter
    sort_by = request.args.get('sort', 'latest')  # latest, oldest
    
    # Get all inquiries (ChatMessages with sender_role='public')
    query = ChatMessage.query.filter_by(
        farmer_id=current_user.id,
        sender_role='public'
    )
    
    # Apply sorting
    if sort_by == 'oldest':
        query = query.order_by(ChatMessage.created_at.asc())
    else:  # default: latest first
        query = query.order_by(ChatMessage.created_at.desc())
    
    inquiries_list = query.all()
    
    # Parse inquiry data from message format: "[Public Inquiry] {name} ({phone}): {message}"
    parsed_inquiries = []
    for inquiry in inquiries_list:
        message_text = inquiry.message
        # Parse the message format
        if message_text.startswith("[Public Inquiry]"):
            try:
                # Extract name, phone, and message
                parts = message_text.replace("[Public Inquiry]", "").strip()
                if "(" in parts and "):" in parts:
                    name_part = parts.split("(")[0].strip()
                    phone_part = parts.split("(")[1].split(")")[0].strip()
                    message_part = parts.split("):", 1)[1].strip() if "):" in parts else ""
                else:
                    # Fallback parsing
                    name_part = "Guest"
                    phone_part = "N/A"
                    message_part = parts
                
                parsed_inquiries.append({
                    'id': inquiry.id,
                    'name': name_part,
                    'phone': phone_part,
                    'message': message_part,
                    'created_at': inquiry.created_at,
                    'is_read': inquiry.is_read
                })
            except:
                # If parsing fails, show raw message
                parsed_inquiries.append({
                    'id': inquiry.id,
                    'name': 'Guest',
                    'phone': 'N/A',
                    'message': message_text,
                    'created_at': inquiry.created_at,
                    'is_read': inquiry.is_read
                })
        else:
            # Handle cases where format might be different
            parsed_inquiries.append({
                'id': inquiry.id,
                'name': 'Guest',
                'phone': 'N/A',
                'message': message_text,
                'created_at': inquiry.created_at,
                'is_read': inquiry.is_read
            })
    
    # Get unread count
    unread_count = ChatMessage.query.filter_by(
        farmer_id=current_user.id,
        sender_role='public',
        is_read=False
    ).count()
    
    return render_template('farmer/marketplace_inquiries.html',
                         inquiries=parsed_inquiries,
                         sort_by=sort_by,
                         unread_count=unread_count)

@farmer_bp.route('/marketplace-inquiries/<int:inquiry_id>/mark-read', methods=['POST'])
@login_required
def mark_inquiry_read(inquiry_id):
    """Mark an inquiry as read"""
    if not current_user.is_farmer():
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    inquiry = ChatMessage.query.get_or_404(inquiry_id)
    
    if inquiry.farmer_id != current_user.id or inquiry.sender_role != 'public':
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    
    try:
        inquiry.is_read = True
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Inquiry marked as read'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== HISTORY ====================

@farmer_bp.route('/history/issues')
@login_required
def history_issues():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    issues = CropIssue.query.filter_by(farmer_id=current_user.id)\
        .order_by(CropIssue.created_at.desc()).all()
    
    return render_template('farmer/history_issues.html', issues=issues)

@farmer_bp.route('/history/predictions')
@login_required
def history_predictions():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    predictions = YieldPrediction.query.filter_by(farmer_id=current_user.id)\
        .order_by(YieldPrediction.created_at.desc()).all()
    
    return render_template('farmer/history_predictions.html', predictions=predictions)

# ==================== REPORTS ====================

@farmer_bp.route('/reports/disease-history/pdf')
@login_required
def report_disease_history_pdf():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    issues = CropIssue.query.filter_by(farmer_id=current_user.id)\
        .order_by(CropIssue.created_at.desc()).all()
    
    data = []
    for issue in issues:
        # Parse AI prediction if available
        disease_name = 'N/A'
        confidence = 'N/A'
        if issue.ai_prediction:
            try:
                import json
                pred = json.loads(issue.ai_prediction)
                disease_name = pred.get('disease_name', 'N/A')
                confidence = f"{pred.get('confidence', 0) * 100:.1f}%" if pred.get('confidence') else 'N/A'
            except:
                pass
        
        # Parse symptoms
        symptoms = 'N/A'
        if issue.symptoms:
            try:
                import json
                symptoms_list = json.loads(issue.symptoms)
                symptoms = ', '.join(symptoms_list[:3]) + ('...' if len(symptoms_list) > 3 else '')
            except:
                symptoms = issue.symptoms[:50]
        
        data.append({
            'ID': issue.id,
            'Crop Type': issue.crop_type,
            'Crop Variety': issue.crop_variety or 'N/A',
            'Disease Predicted': disease_name,
            'Confidence': confidence,
            'Symptoms': symptoms,
            'Status': issue.status.title(),
            'Location': issue.location or 'N/A',
            'Date': issue.created_at.strftime('%Y-%m-%d'),
            'Expert Response': 'Yes' if issue.expert_response else 'No'
        })
    
    summary = {
        'Total Issues': len(issues),
        'Pending': len([i for i in issues if i.status == 'pending']),
        'Reviewed': len([i for i in issues if i.status == 'reviewed']),
        'Resolved': len([i for i in issues if i.status == 'resolved'])
    }
    
    pdf_buffer = generate_pdf_report(
        data, 
        'Disease History', 
        current_user.full_name,
        subtitle=f"Farmer: {current_user.full_name}",
        summary=summary
    )
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'disease_history_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@farmer_bp.route('/reports/disease-history/csv')
@login_required
def report_disease_history_csv():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    issues = CropIssue.query.filter_by(farmer_id=current_user.id)\
        .order_by(CropIssue.created_at.desc()).all()
    
    data = []
    for issue in issues:
        disease_name = 'N/A'
        confidence = 'N/A'
        if issue.ai_prediction:
            try:
                import json
                pred = json.loads(issue.ai_prediction)
                disease_name = pred.get('disease_name', 'N/A')
                confidence = f"{pred.get('confidence', 0) * 100:.1f}%" if pred.get('confidence') else 'N/A'
            except:
                pass
        
        symptoms = 'N/A'
        if issue.symptoms:
            try:
                import json
                symptoms_list = json.loads(issue.symptoms)
                symptoms = ', '.join(symptoms_list)
            except:
                symptoms = issue.symptoms[:100]
        
        data.append({
            'ID': issue.id,
            'Crop Type': issue.crop_type,
            'Crop Variety': issue.crop_variety or 'N/A',
            'Disease Predicted': disease_name,
            'Confidence': confidence,
            'Symptoms': symptoms,
            'Status': issue.status.title(),
            'Location': issue.location or 'N/A',
            'Date': issue.created_at.strftime('%Y-%m-%d'),
            'Expert Response': 'Yes' if issue.expert_response else 'No'
        })
    
    csv_data = generate_csv_report(data, 'disease_history')
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=disease_history_report_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

@farmer_bp.route('/reports/issues/pdf')
@login_required
def report_issues_pdf():
    """Alias for disease history PDF"""
    return report_disease_history_pdf()

@farmer_bp.route('/reports/issues/csv')
@login_required
def report_issues_csv():
    """Alias for disease history CSV"""
    return report_disease_history_csv()

@farmer_bp.route('/reports/yield-predictions/pdf')
@login_required
def report_yield_predictions_pdf():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    predictions = YieldPrediction.query.filter_by(farmer_id=current_user.id)\
        .order_by(YieldPrediction.created_at.desc()).all()
    
    data = []
    for pred in predictions:
        total_yield = (pred.predicted_yield * pred.farm_size) if pred.predicted_yield else 0
        data.append({
            'ID': pred.id,
            'Crop Type': pred.crop_type,
            'Crop Variety': pred.crop_variety or 'N/A',
            'Soil Type': pred.soil_type,
            'Irrigation': pred.irrigation_type,
            'Fertilizer': pred.fertilizer_type,
            'Yield/Acre (tons)': f"{pred.predicted_yield:.2f}" if pred.predicted_yield else 'N/A',
            'Farm Size (acres)': f"{pred.farm_size:.2f}",
            'Total Yield (tons)': f"{total_yield:.2f}" if pred.predicted_yield else 'N/A',
            'Confidence': f"{pred.confidence_score * 100:.1f}%" if pred.confidence_score else 'N/A',
            'Temperature (°C)': f"{pred.temperature:.1f}" if pred.temperature else 'N/A',
            'Rainfall (mm)': f"{pred.rainfall:.1f}" if pred.rainfall else 'N/A',
            'Location': pred.location,
            'Date': pred.created_at.strftime('%Y-%m-%d')
        })
    
    summary = {
        'Total Predictions': len(predictions),
        'Average Yield/Acre': f"{sum(p.predicted_yield for p in predictions if p.predicted_yield) / len([p for p in predictions if p.predicted_yield]):.2f} tons" if predictions else 'N/A',
        'Total Farm Area': f"{sum(p.farm_size for p in predictions):.2f} acres"
    }
    
    pdf_buffer = generate_pdf_report(
        data, 
        'Yield Predictions', 
        current_user.full_name,
        subtitle=f"Farmer: {current_user.full_name}",
        summary=summary
    )
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'yield_predictions_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@farmer_bp.route('/reports/yield-predictions/csv')
@login_required
def report_yield_predictions_csv():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_login'))
    
    predictions = YieldPrediction.query.filter_by(farmer_id=current_user.id)\
        .order_by(YieldPrediction.created_at.desc()).all()
    
    data = []
    for pred in predictions:
        total_yield = (pred.predicted_yield * pred.farm_size) if pred.predicted_yield else 0
        data.append({
            'ID': pred.id,
            'Crop Type': pred.crop_type,
            'Crop Variety': pred.crop_variety or 'N/A',
            'Soil Type': pred.soil_type,
            'Irrigation': pred.irrigation_type,
            'Fertilizer': pred.fertilizer_type,
            'Yield/Acre (tons)': f"{pred.predicted_yield:.2f}" if pred.predicted_yield else 'N/A',
            'Farm Size (acres)': f"{pred.farm_size:.2f}",
            'Total Yield (tons)': f"{total_yield:.2f}" if pred.predicted_yield else 'N/A',
            'Confidence': f"{pred.confidence_score * 100:.1f}%" if pred.confidence_score else 'N/A',
            'Temperature (°C)': f"{pred.temperature:.1f}" if pred.temperature else 'N/A',
            'Rainfall (mm)': f"{pred.rainfall:.1f}" if pred.rainfall else 'N/A',
            'Location': pred.location,
            'Date': pred.created_at.strftime('%Y-%m-%d')
        })
    
    csv_data = generate_csv_report(data, 'yield_predictions')
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=yield_predictions_report_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

@farmer_bp.route('/reports/predictions/pdf')
@login_required
def report_predictions_pdf():
    """Alias for yield predictions PDF"""
    return report_yield_predictions_pdf()

@farmer_bp.route('/reports/predictions/csv')
@login_required
def report_predictions_csv():
    """Alias for yield predictions CSV"""
    return report_yield_predictions_csv()

