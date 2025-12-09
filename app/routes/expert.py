# Expert Module Routes
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from sqlalchemy import func
from flask_login import login_required, current_user
from app.models import (
    db, CropIssue, YieldPrediction, ChatMessage, User,
    DiagnosisReport, ExpertRating
)
from app.utils.ml_helpers import predict_disease, predict_yield
from datetime import datetime
import json
from sqlalchemy import func, desc

expert_bp = Blueprint('expert', __name__)

# ==================== DASHBOARD ====================

@expert_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    
    # Get weather data
    location = "Kerala, India"  # Default location, can be customized
    from app.utils.weather import get_weather
    weather = get_weather(location)
    
    # Statistics
    total_issues = CropIssue.query.count()
    pending_issues = CropIssue.query.filter_by(status='pending').count()
    my_diagnoses = DiagnosisReport.query.filter_by(expert_id=current_user.id).count()
    my_ratings = ExpertRating.query.filter_by(expert_id=current_user.id).count()
    
    # Average rating
    avg_rating_result = db.session.query(func.avg(ExpertRating.rating))\
        .filter_by(expert_id=current_user.id).scalar()
    avg_rating = round(avg_rating_result, 1) if avg_rating_result else 0
    
    # Recent pending issues
    recent_pending = CropIssue.query.filter_by(status='pending')\
        .order_by(CropIssue.created_at.desc()).limit(5).all()
    
    # My recent diagnoses
    my_recent_diagnoses = DiagnosisReport.query.filter_by(expert_id=current_user.id)\
        .order_by(DiagnosisReport.created_at.desc()).limit(5).all()
    
    # Analytics data
    issues_by_status = db.session.query(
        CropIssue.status,
        func.count(CropIssue.id)
    ).group_by(CropIssue.status).all()
    
    issues_by_crop = db.session.query(
        CropIssue.crop_type,
        func.count(CropIssue.id)
    ).group_by(CropIssue.crop_type).limit(5).all()
    
    # Monthly diagnoses (last 6 months)
    monthly_diagnoses = db.session.query(
        func.strftime('%Y-%m', DiagnosisReport.created_at).label('month'),
        func.count(DiagnosisReport.id)
    ).filter_by(expert_id=current_user.id)\
     .group_by('month')\
     .order_by(desc('month'))\
     .limit(6).all()
    
    return render_template('expert/dashboard.html',
                         weather=weather,
                         total_issues=total_issues,
                         pending_issues=pending_issues,
                         my_diagnoses=my_diagnoses,
                         my_ratings=my_ratings,
                         avg_rating=avg_rating,
                         recent_pending=recent_pending,
                         my_recent_diagnoses=my_recent_diagnoses,
                         issues_by_status=dict(issues_by_status),
                         issues_by_crop=dict(issues_by_crop),
                         monthly_diagnoses=dict(monthly_diagnoses))

# ==================== PENDING ISSUES ====================

@expert_bp.route('/issues/pending')
@login_required
def pending_issues():
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    
    issues = CropIssue.query.filter_by(status='pending')\
        .order_by(CropIssue.created_at.desc()).all()
    
    return render_template('expert/pending_issues.html', issues=issues)

@expert_bp.route('/issues/<int:issue_id>')
@login_required
def view_issue(issue_id):
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    
    issue = CropIssue.query.get_or_404(issue_id)
    
    # Check if already diagnosed
    existing_report = DiagnosisReport.query.filter_by(crop_issue_id=issue_id).first()
    
    # Get AI prediction if available
    ai_prediction = None
    if issue.ai_prediction:
        try:
            ai_prediction = json.loads(issue.ai_prediction)
        except:
            pass
    
    return render_template('expert/view_issue.html',
                         issue=issue,
                         existing_report=existing_report,
                         ai_prediction=ai_prediction)

# ==================== DIAGNOSE ISSUE ====================

@expert_bp.route('/issues/<int:issue_id>/diagnose', methods=['GET', 'POST'])
@login_required
def diagnose_issue(issue_id):
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    
    issue = CropIssue.query.get_or_404(issue_id)
    
    # Check if already diagnosed
    existing_report = DiagnosisReport.query.filter_by(crop_issue_id=issue_id).first()
    if existing_report:
        flash('This issue has already been diagnosed.', 'warning')
        return redirect(url_for('expert.view_issue', issue_id=issue_id))
    
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        disease_identified = request.form.get('disease_identified')
        severity = request.form.get('severity')
        treatment_plan = request.form.get('treatment_plan')
        preventive_measures = request.form.get('preventive_measures')
        recommended_products = request.form.getlist('recommended_products')
        use_ai_prediction = request.form.get('use_ai_prediction') == 'on'
        confidence_level = request.form.get('confidence_level')
        
        # AI Disease Prediction (if requested)
        ai_prediction_result = None
        if use_ai_prediction:
            symptoms = json.loads(issue.symptoms) if issue.symptoms else []
            ai_prediction_result = predict_disease(issue.image_path, symptoms, issue.crop_type)
        
        if not all([diagnosis, treatment_plan]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('expert/diagnose_issue.html', issue=issue)
        
        # Create diagnosis report
        report = DiagnosisReport(
            crop_issue_id=issue_id,
            expert_id=current_user.id,
            diagnosis=diagnosis,
            disease_identified=disease_identified,
            severity=severity,
            treatment_plan=treatment_plan,
            preventive_measures=preventive_measures,
            recommended_products=json.dumps(recommended_products) if recommended_products else None,
            ai_prediction_used=use_ai_prediction,
            confidence_level=confidence_level
        )
        
        # Update issue status
        issue.status = 'reviewed'
        issue.expert_id = current_user.id
        issue.expert_response = diagnosis
        
        try:
            db.session.add(report)
            db.session.commit()
            flash('Diagnosis report submitted successfully!', 'success')
            return redirect(url_for('expert.view_issue', issue_id=issue_id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while saving the diagnosis: {str(e)}. Please try again.', 'danger')
    
    # Get AI prediction if available
    ai_prediction = None
    if issue.ai_prediction:
        try:
            ai_prediction = json.loads(issue.ai_prediction)
        except:
            pass
    
    # Symptom options for AI prediction
    symptom_options = [
        'Yellowing leaves', 'Brown spots', 'Wilting', 'Stunted growth',
        'Leaf curling', 'White powdery substance', 'Black spots',
        'Holes in leaves', 'Discolored stems', 'Root rot', 'Fruit drop',
        'Flower drop', 'Mosaic pattern', 'Necrosis', 'Chlorosis'
    ]
    
    return render_template('expert/diagnose_issue.html',
                         issue=issue,
                         ai_prediction=ai_prediction,
                         symptom_options=symptom_options)

# ==================== AI PREDICTIONS ====================

@expert_bp.route('/ai/disease-prediction', methods=['POST'])
@login_required
def ai_disease_prediction():
    if not current_user.is_expert():
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    symptoms = data.get('symptoms', [])
    crop_type = data.get('crop_type')
    image_path = data.get('image_path')
    
    if not crop_type:
        return jsonify({'error': 'Crop type required'}), 400
    
    prediction = predict_disease(image_path, symptoms, crop_type)
    
    return jsonify(json.loads(prediction))

@expert_bp.route('/ai/yield-prediction', methods=['POST'])
@login_required
def ai_yield_prediction():
    if not current_user.is_expert():
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    result = predict_yield(
        data.get('crop_type'),
        data.get('soil_type'),
        data.get('irrigation_type'),
        data.get('fertilizer_type'),
        data.get('temperature', 28.0),
        data.get('rainfall', 0),
        data.get('farm_size', 1.0),
        data.get('location', '')
    )
    
    return jsonify(result)

# ==================== CHAT WITH FARMERS ====================

@expert_bp.route('/chat')
@login_required
def chat_list():
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    
    # Get farmers that expert has chatted with with unread counts
    farmers_with_unread = db.session.query(
        User,
        func.count(ChatMessage.id).label('unread_count')
    ).join(ChatMessage, User.id == ChatMessage.farmer_id)\
     .filter(ChatMessage.expert_id == current_user.id)\
     .filter(ChatMessage.sender_role == 'farmer', ChatMessage.is_read == False)\
     .group_by(User.id).all()
    
    # Get all farmers expert has chatted with
    farmers = db.session.query(User).join(ChatMessage, User.id == ChatMessage.farmer_id)\
        .filter(ChatMessage.expert_id == current_user.id)\
        .distinct().all()
    
    # Create unread count dict
    unread_counts = {farmer.id: count for farmer, count in farmers_with_unread}
    for farmer in farmers:
        if farmer.id not in unread_counts:
            unread_counts[farmer.id] = 0
    
    # Get total unread count
    total_unread = ChatMessage.query.filter(
        ChatMessage.expert_id == current_user.id,
        ChatMessage.sender_role == 'farmer',
        ChatMessage.is_read == False
    ).count()
    
    return render_template('expert/chat_list.html', 
                         farmers=farmers,
                         unread_counts=unread_counts,
                         total_unread=total_unread)

@expert_bp.route('/chat/<int:farmer_id>', methods=['GET', 'POST'])
@login_required
def chat_with_farmer(farmer_id):
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    farmer = User.query.get_or_404(farmer_id)
    if not farmer.is_farmer():
        flash('Invalid farmer.', 'danger')
        return redirect(url_for('expert.chat_list'))
    
    if request.method == 'POST':
        message = request.form.get('message')
        related_issue_id = request.form.get('related_issue_id')
        image = request.files.get('image')
        image_path = None

        # Handle image upload if present
        if image:
            from werkzeug.utils import secure_filename
            import os
            from datetime import datetime
            from flask import current_app
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'chat_images')
            os.makedirs(upload_dir, exist_ok=True)
            filename = secure_filename(f"chat_{int(datetime.utcnow().timestamp())}_{image.filename}")
            image.save(os.path.join(upload_dir, filename))
            image_path = f"uploads/chat_images/{filename}"

        if message or image_path:
            chat_message = ChatMessage(
                farmer_id=farmer_id,
                expert_id=current_user.id,
                message=message if message else "Sent an image",
                sender_role='expert',
                related_issue_id=int(related_issue_id) if related_issue_id else None,
                image_path=image_path
            )
            
            try:
                db.session.add(chat_message)
                db.session.commit()
                return jsonify({
                    'status': 'success',
                    'message': 'Message sent!',
                    'data': {
                        'id': chat_message.id,
                        'message': chat_message.message,
                        'image_path': chat_message.image_path,
                        'created_at': chat_message.created_at.strftime('%Y-%m-%d %H:%M'),
                        'sender_role': 'expert'
                    }
                })
            except Exception as e:
                db.session.rollback()
                print(f"Error sending message: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Get chat messages
    messages = ChatMessage.query.filter(
        ChatMessage.farmer_id == farmer_id,
        ChatMessage.expert_id == current_user.id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # Mark messages as read
    for msg in messages:
        if msg.sender_role == 'farmer' and not msg.is_read:
            msg.is_read = True
    db.session.commit()
    
    # Get farmer's crop issues
    crop_issues = CropIssue.query.filter_by(farmer_id=farmer_id).all()
    
    return render_template('expert/chat.html',
                         farmer=farmer,
                         messages=messages,
                         crop_issues=crop_issues,
                         last_message_id=messages[-1].id if messages else 0)

@expert_bp.route('/chat/<int:farmer_id>/poll')
@login_required
def chat_poll(farmer_id):
    """Long-polling endpoint to check for new messages"""
    if not current_user.is_expert():
        print(f"[DEBUG] expert.chat_poll access denied: current_user={{id:{getattr(current_user, 'id', None)}, role:{getattr(current_user, 'role', None)}}}, farmer_id={farmer_id}")
        return jsonify({'error': 'Access denied'}), 403
    
    last_message_id = request.args.get('last_message_id', 0, type=int)
    timeout = 30  # seconds
    print(f"[DEBUG] expert.chat_poll called: current_user_id={getattr(current_user, 'id', None)}, farmer_id={farmer_id}, last_message_id={last_message_id}")
    
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check for new messages
        new_messages = ChatMessage.query.filter(
            ChatMessage.farmer_id == farmer_id,
            ChatMessage.expert_id == current_user.id,
            ChatMessage.id > last_message_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        if new_messages:
            print(f"[DEBUG] expert.chat_poll found {len(new_messages)} new_messages for farmer_id={farmer_id}: {[m.id for m in new_messages]}")
            # Mark farmer messages as read
            for msg in new_messages:
                if msg.sender_role == 'farmer' and not msg.is_read:
                    msg.is_read = True
            db.session.commit()
            
            messages_data = []
            for msg in new_messages:
                messages_data.append({
                    'id': msg.id,
                    'message': msg.message,
                    'image_path': msg.image_path,
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

@expert_bp.route('/chat/unread-count')
@login_required
def chat_unread_count():
    """Get unread message count for expert"""
    if not current_user.is_expert():
        return jsonify({'error': 'Access denied'}), 403
    
    unread_count = ChatMessage.query.filter(
        ChatMessage.expert_id == current_user.id,
        ChatMessage.sender_role == 'farmer',
        ChatMessage.is_read == False
    ).count()
    
    return jsonify({'unread_count': unread_count})

# ==================== RATINGS ====================

@expert_bp.route('/ratings')
@login_required
def ratings():
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    
    ratings_list = ExpertRating.query.filter_by(expert_id=current_user.id)\
        .order_by(ExpertRating.created_at.desc()).all()
    
    # Calculate statistics
    total_ratings = len(ratings_list)
    avg_rating = db.session.query(func.avg(ExpertRating.rating))\
        .filter_by(expert_id=current_user.id).scalar()
    avg_rating = round(avg_rating, 1) if avg_rating else 0
    
    # Rating distribution
    rating_dist = {}
    for i in range(1, 6):
        count = ExpertRating.query.filter_by(
            expert_id=current_user.id,
            rating=i
        ).count()
        rating_dist[i] = count
    
    return render_template('expert/ratings.html',
                         ratings=ratings_list,
                         total_ratings=total_ratings,
                         avg_rating=avg_rating,
                         rating_dist=rating_dist)

# ==================== ANALYTICS ====================

@expert_bp.route('/analytics')
@login_required
def analytics():
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    
    # Detailed analytics
    total_diagnoses = DiagnosisReport.query.filter_by(expert_id=current_user.id).count()
    total_ratings = ExpertRating.query.filter_by(expert_id=current_user.id).count()
    
    # Average rating
    avg_rating = db.session.query(func.avg(ExpertRating.rating))\
        .filter_by(expert_id=current_user.id).scalar()
    avg_rating = round(avg_rating, 1) if avg_rating else 0
    
    # Diagnoses by crop type
    diagnoses_by_crop = db.session.query(
        CropIssue.crop_type,
        func.count(DiagnosisReport.id)
    ).join(DiagnosisReport, CropIssue.id == DiagnosisReport.crop_issue_id)\
     .filter(DiagnosisReport.expert_id == current_user.id)\
     .group_by(CropIssue.crop_type).all()
    
    # Diagnoses by severity
    diagnoses_by_severity = db.session.query(
        DiagnosisReport.severity,
        func.count(DiagnosisReport.id)
    ).filter_by(expert_id=current_user.id)\
     .group_by(DiagnosisReport.severity).all()
    
    # Monthly performance (last 12 months)
    monthly_performance = db.session.query(
        func.strftime('%Y-%m', DiagnosisReport.created_at).label('month'),
        func.count(DiagnosisReport.id).label('diagnoses')
    ).filter_by(expert_id=current_user.id)\
     .group_by('month')\
     .order_by(desc('month'))\
     .limit(12).all()
    
    # Response time (average days from issue creation to diagnosis)
    response_times = db.session.query(
        func.avg(
            func.julianday(DiagnosisReport.created_at) - 
            func.julianday(CropIssue.created_at)
        )
    ).join(CropIssue, DiagnosisReport.crop_issue_id == CropIssue.id)\
     .filter(DiagnosisReport.expert_id == current_user.id).scalar()
    
    avg_response_days = round(response_times, 1) if response_times else 0
    
    return render_template('expert/analytics.html',
                         total_diagnoses=total_diagnoses,
                         total_ratings=total_ratings,
                         avg_rating=avg_rating,
                         diagnoses_by_crop=dict(diagnoses_by_crop),
                         diagnoses_by_severity=dict(diagnoses_by_severity),
                         monthly_performance=dict(monthly_performance),
                         avg_response_days=avg_response_days)

# ==================== REPORTS ====================

@expert_bp.route('/reports/performance/pdf')
@login_required
def report_performance_pdf():
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    
    from app.utils.reports import generate_pdf_report
    from flask import send_file
    
    # Get all diagnoses
    diagnoses = DiagnosisReport.query.filter_by(expert_id=current_user.id)\
        .order_by(DiagnosisReport.created_at.desc()).all()
    
    data = []
    for diag in diagnoses:
        data.append({
            'Issue ID': diag.crop_issue_id,
            'Crop Type': diag.crop_issue.crop_type if diag.crop_issue else 'N/A',
            'Disease Identified': diag.disease_identified or 'N/A',
            'Severity': diag.severity or 'N/A',
            'Confidence': diag.confidence_level or 'N/A',
            'AI Used': 'Yes' if diag.ai_prediction_used else 'No',
            'Date': diag.created_at.strftime('%Y-%m-%d'),
            'Farmer': diag.crop_issue.farmer.full_name if diag.crop_issue else 'N/A'
        })
    
    # Get ratings
    ratings = ExpertRating.query.filter_by(expert_id=current_user.id).all()
    avg_rating = db.session.query(func.avg(ExpertRating.rating))\
        .filter_by(expert_id=current_user.id).scalar()
    
    summary = {
        'Total Diagnoses': len(diagnoses),
        'Total Ratings': len(ratings),
        'Average Rating': f"{avg_rating:.1f}/5.0" if avg_rating else 'N/A',
        'High Severity Cases': len([d for d in diagnoses if d.severity == 'High' or d.severity == 'Critical']),
        'AI-Assisted Diagnoses': len([d for d in diagnoses if d.ai_prediction_used])
    }
    
    pdf_buffer = generate_pdf_report(
        data,
        'Expert Performance',
        current_user.full_name,
        subtitle=f"Expert: {current_user.full_name}",
        summary=summary
    )
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'expert_performance_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@expert_bp.route('/reports/performance/csv')
@login_required
def report_performance_csv():
    if not current_user.is_expert():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.expert_login'))
    
    from app.utils.reports import generate_csv_report
    from flask import make_response
    
    diagnoses = DiagnosisReport.query.filter_by(expert_id=current_user.id)\
        .order_by(DiagnosisReport.created_at.desc()).all()
    
    data = []
    for diag in diagnoses:
        data.append({
            'Issue ID': diag.crop_issue_id,
            'Crop Type': diag.crop_issue.crop_type if diag.crop_issue else 'N/A',
            'Disease Identified': diag.disease_identified or 'N/A',
            'Severity': diag.severity or 'N/A',
            'Confidence': diag.confidence_level or 'N/A',
            'AI Used': 'Yes' if diag.ai_prediction_used else 'No',
            'Date': diag.created_at.strftime('%Y-%m-%d'),
            'Farmer': diag.crop_issue.farmer.full_name if diag.crop_issue else 'N/A'
        })
    
    csv_data = generate_csv_report(data, 'expert_performance')
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=expert_performance_report_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

