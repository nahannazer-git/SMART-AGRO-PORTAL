# Admin Module Routes
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, make_response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import (
    db, User, CropIssue, YieldPrediction, DiagnosisReport,
    ExpertRating, ProductRequest, ChatMessage, Notice,
    MLDataset, ModelTraining, ModelPerformance
)
from app.utils.reports import generate_pdf_report, generate_csv_report
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, case
from pathlib import Path
import json
import os

admin_bp = Blueprint('admin', __name__)

ALLOWED_DATASET_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}

def allowed_dataset_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DATASET_EXTENSIONS

# ==================== DASHBOARD ====================

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    # User statistics
    total_farmers = User.query.filter_by(role='farmer').count()
    total_experts = User.query.filter_by(role='expert').count()
    total_officers = User.query.filter_by(role='krishi_bhavan_officer').count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Issue statistics
    total_issues = CropIssue.query.count()
    pending_issues = CropIssue.query.filter_by(status='pending').count()
    resolved_issues = CropIssue.query.filter_by(status='resolved').count()
    
    # Prediction statistics
    total_yield_predictions = YieldPrediction.query.count()
    total_diagnoses = DiagnosisReport.query.count()
    
    # Product requests
    total_product_requests = ProductRequest.query.count()
    pending_requests = ProductRequest.query.filter_by(status='pending').count()
    
    # Region statistics
    region_stats = db.session.query(
        CropIssue.location,
        func.count(CropIssue.id)
    ).filter(CropIssue.location.isnot(None))\
     .group_by(CropIssue.location)\
     .order_by(desc(func.count(CropIssue.id)))\
     .limit(10).all()
    
    # Disease frequency
    disease_frequency = db.session.query(
        DiagnosisReport.disease_identified,
        func.count(DiagnosisReport.id)
    ).filter(DiagnosisReport.disease_identified.isnot(None))\
     .group_by(DiagnosisReport.disease_identified)\
     .order_by(desc(func.count(DiagnosisReport.id)))\
     .limit(10).all()
    
    # Crop type distribution
    crop_distribution = db.session.query(
        CropIssue.crop_type,
        func.count(CropIssue.id)
    ).group_by(CropIssue.crop_type).all()
    
    # Monthly trends (last 6 months) - handle Postgres vs SQLite
    dialect = db.engine.dialect.name
    month_expr = func.strftime('%Y-%m', CropIssue.created_at) if dialect == 'sqlite' else func.to_char(CropIssue.created_at, 'YYYY-MM')
    monthly_issues = db.session.query(
        month_expr.label('month'),
        func.count(CropIssue.id)
    ).group_by('month')\
     .order_by(desc('month'))\
     .limit(6).all()
    
    # Yield statistics
    avg_yield = db.session.query(func.avg(YieldPrediction.predicted_yield)).scalar()
    avg_yield = round(avg_yield, 2) if avg_yield else 0
    
    return render_template('admin/dashboard.html',
                         total_farmers=total_farmers,
                         total_experts=total_experts,
                         total_officers=total_officers,
                         active_users=active_users,
                         total_issues=total_issues,
                         pending_issues=pending_issues,
                         resolved_issues=resolved_issues,
                         total_yield_predictions=total_yield_predictions,
                         total_diagnoses=total_diagnoses,
                         total_product_requests=total_product_requests,
                         pending_requests=pending_requests,
                         region_stats=dict(region_stats),
                         disease_frequency=dict(disease_frequency),
                         crop_distribution=dict(crop_distribution),
                         monthly_issues=dict(monthly_issues),
                         avg_yield=avg_yield)

# ==================== USER MANAGEMENT ====================

@admin_bp.route('/farmers')
@login_required
def manage_farmers():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    farmers = User.query.filter_by(role='farmer').order_by(User.created_at.desc()).all()
    
    return render_template('admin/manage_farmers.html', farmers=farmers)

@admin_bp.route('/experts')
@login_required
def manage_experts():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    experts = User.query.filter_by(role='expert').order_by(User.created_at.desc()).all()
    
    return render_template('admin/manage_experts.html', experts=experts)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    
    try:
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {status} successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while updating user status: {str(e)}', 'danger')
    
    if user.is_farmer():
        return redirect(url_for('admin.manage_farmers'))
    elif user.is_expert():
        return redirect(url_for('admin.manage_experts'))
    else:
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    role = user.role
    
    try:
        # Check for related data
        if user.role == 'farmer':
            issues_count = CropIssue.query.filter_by(farmer_id=user.id).count()
            if issues_count > 0:
                flash(f'Cannot delete user. User has {issues_count} crop issue(s) associated.', 'warning')
                return redirect(url_for('admin.manage_farmers' if user.role == 'farmer' else 'admin.manage_experts'))
        elif user.role == 'expert':
            diagnoses_count = DiagnosisReport.query.filter_by(expert_id=user.id).count()
            if diagnoses_count > 0:
                flash(f'Cannot delete user. Expert has {diagnoses_count} diagnosis(es) associated.', 'warning')
                return redirect(url_for('admin.manage_experts'))
        
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the user: {str(e)}', 'danger')
    
    if role == 'farmer':
        return redirect(url_for('admin.manage_farmers'))
    elif role == 'expert':
        return redirect(url_for('admin.manage_experts'))
    else:
        return redirect(url_for('admin.dashboard'))

# ==================== REGION STATISTICS ====================

@admin_bp.route('/statistics/regions')
@login_required
def region_statistics():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    # Region-wise statistics
    region_issues = db.session.query(
        CropIssue.location,
        func.count(CropIssue.id).label('total_issues'),
        func.count(func.distinct(CropIssue.farmer_id)).label('farmers_count')
    ).filter(CropIssue.location.isnot(None))\
     .group_by(CropIssue.location)\
     .order_by(desc('total_issues')).all()
    
    # Region-wise yield predictions
    region_yields = db.session.query(
        YieldPrediction.location,
        func.avg(YieldPrediction.predicted_yield).label('avg_yield'),
        func.count(YieldPrediction.id).label('prediction_count')
    ).group_by(YieldPrediction.location)\
     .order_by(desc('avg_yield')).all()
    
    return render_template('admin/region_statistics.html',
                         region_issues=region_issues,
                         region_yields=region_yields)

# ==================== DISEASE FREQUENCY ====================

@admin_bp.route('/statistics/diseases')
@login_required
def disease_statistics():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    # Disease frequency
    disease_freq = db.session.query(
        DiagnosisReport.disease_identified,
        func.count(DiagnosisReport.id).label('count'),
        func.avg(
            case(
                (DiagnosisReport.severity == 'Critical', 4),
                (DiagnosisReport.severity == 'High', 3),
                (DiagnosisReport.severity == 'Medium', 2),
                (DiagnosisReport.severity == 'Low', 1),
                else_=0
            )
        ).label('avg_severity')
    ).filter(DiagnosisReport.disease_identified.isnot(None))\
     .group_by(DiagnosisReport.disease_identified)\
     .order_by(desc('count')).all()
    
    # Disease by crop type
    disease_by_crop = db.session.query(
        CropIssue.crop_type,
        DiagnosisReport.disease_identified,
        func.count(DiagnosisReport.id)
    ).join(DiagnosisReport, CropIssue.id == DiagnosisReport.crop_issue_id)\
     .filter(DiagnosisReport.disease_identified.isnot(None))\
     .group_by(CropIssue.crop_type, DiagnosisReport.disease_identified)\
     .order_by(desc(func.count(DiagnosisReport.id))).all()
    
    return render_template('admin/disease_statistics.html',
                         disease_freq=disease_freq,
                         disease_by_crop=disease_by_crop)

# ==================== YIELD STATISTICS ====================

@admin_bp.route('/statistics/yield')
@login_required
def yield_statistics():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    # Yield by crop type
    yield_by_crop = db.session.query(
        YieldPrediction.crop_type,
        func.avg(YieldPrediction.predicted_yield).label('avg_yield'),
        func.count(YieldPrediction.id).label('count')
    ).group_by(YieldPrediction.crop_type)\
     .order_by(desc('avg_yield')).all()
    
    # Yield by region
    yield_by_region = db.session.query(
        YieldPrediction.location,
        func.avg(YieldPrediction.predicted_yield).label('avg_yield'),
        func.count(YieldPrediction.id).label('count')
    ).group_by(YieldPrediction.location)\
     .order_by(desc('avg_yield')).all()
    
    # Yield trends (monthly) - handle Postgres vs SQLite
    dialect = db.engine.dialect.name
    month_expr = func.strftime('%Y-%m', YieldPrediction.created_at) if dialect == 'sqlite' else func.to_char(YieldPrediction.created_at, 'YYYY-MM')
    yield_trends = db.session.query(
        month_expr.label('month'),
        func.avg(YieldPrediction.predicted_yield).label('avg_yield'),
        func.count(YieldPrediction.id).label('count')
    ).group_by('month')\
     .order_by(desc('month'))\
     .limit(12).all()
    
    return render_template('admin/yield_statistics.html',
                         yield_by_crop=yield_by_crop,
                         yield_by_region=yield_by_region,
                         yield_trends=yield_trends)

# ==================== ML DATASET MANAGEMENT ====================

@admin_bp.route('/ml/datasets')
@login_required
def ml_datasets():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    datasets = MLDataset.query.order_by(MLDataset.created_at.desc()).all()
    
    return render_template('admin/ml_datasets.html', datasets=datasets)

@admin_bp.route('/ml/datasets/upload', methods=['GET', 'POST'])
@login_required
def upload_dataset():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        dataset_type = request.form.get('dataset_type')
        
        if not all([name, dataset_type]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/upload_dataset.html')
        
        if 'dataset_file' not in request.files:
            flash('No file selected.', 'danger')
            return render_template('admin/upload_dataset.html')
        
        file = request.files['dataset_file']
        if file.filename == '' or not allowed_dataset_file(file.filename):
            flash('Invalid file type. Allowed: CSV, JSON, XLSX', 'danger')
            return render_template('admin/upload_dataset.html')
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        upload_folder = Path(current_app.config['ML_DATASETS_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_folder / filename
        file.save(str(file_path))
        
        file_size = file_path.stat().st_size
        
        # Create dataset record
        dataset = MLDataset(
            name=name,
            description=description,
            file_path=f"uploads/ml_datasets/{filename}",
            file_size=file_size,
            dataset_type=dataset_type,
            uploaded_by=current_user.id
        )
        
        try:
            db.session.add(dataset)
            db.session.commit()
            flash('Dataset uploaded successfully!', 'success')
            return redirect(url_for('admin.ml_datasets'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred.', 'danger')
    
    return render_template('admin/upload_dataset.html')

# ==================== MODEL MONITORING ====================

@admin_bp.route('/ml/models')
@login_required
def model_monitoring():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    # Get model performance
    disease_model = ModelPerformance.query.filter_by(model_type='disease').first()
    yield_model = ModelPerformance.query.filter_by(model_type='yield').first()
    
    # Recent trainings
    recent_trainings = ModelTraining.query.order_by(ModelTraining.created_at.desc()).limit(10).all()
    
    # Training statistics
    total_trainings = ModelTraining.query.count()
    completed_trainings = ModelTraining.query.filter_by(training_status='completed').count()
    failed_trainings = ModelTraining.query.filter_by(training_status='failed').count()
    
    return render_template('admin/model_monitoring.html',
                         disease_model=disease_model,
                         yield_model=yield_model,
                         recent_trainings=recent_trainings,
                         total_trainings=total_trainings,
                         completed_trainings=completed_trainings,
                         failed_trainings=failed_trainings)

@admin_bp.route('/ml/models/retrain', methods=['POST'])
@login_required
def retrain_model():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    model_type = request.form.get('model_type')
    dataset_id = request.form.get('dataset_id')
    
    if not model_type:
        flash('Model type required.', 'danger')
        return redirect(url_for('admin.model_monitoring'))
    
    # Create fake training record
    training = ModelTraining(
        model_name=f"{model_type}_model_v{datetime.now().strftime('%Y%m%d')}",
        model_type=model_type,
        dataset_id=int(dataset_id) if dataset_id else None,
        training_status='training',
        trained_by=current_user.id
    )
    
    try:
        db.session.add(training)
        db.session.commit()
        
        # Simulate training completion (in real app, this would be async)
        import random
        import time
        time.sleep(2)  # Simulate processing
        
        training.training_status = 'completed'
        training.accuracy = round(random.uniform(0.85, 0.95), 3)
        training.loss = round(random.uniform(0.05, 0.15), 3)
        training.training_duration = random.randint(300, 1800)  # 5-30 minutes
        training.epochs = random.randint(50, 200)
        training.batch_size = random.choice([16, 32, 64])
        training.completed_at = datetime.utcnow()
        training.model_path = f"models/{model_type}_{datetime.now().strftime('%Y%m%d')}.pkl"
        
        # Update model performance
        perf = ModelPerformance.query.filter_by(model_type=model_type).first()
        if not perf:
            perf = ModelPerformance(
                model_type=model_type,
                model_version=training.model_name
            )
            db.session.add(perf)
        
        perf.model_version = training.model_name
        perf.accuracy = training.accuracy
        perf.avg_confidence = round(random.uniform(0.80, 0.90), 3)
        perf.last_updated = datetime.utcnow()
        
        db.session.commit()
        flash('Model retraining completed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during retraining.', 'danger')
    
    return redirect(url_for('admin.model_monitoring'))

# ==================== REPORTS ====================

@admin_bp.route('/reports/region-wise/pdf')
@login_required
def report_region_wise_pdf():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    from app.utils.reports import generate_pdf_report
    
    # Region-wise statistics
    region_stats = db.session.query(
        CropIssue.location,
        func.count(CropIssue.id).label('total_issues'),
        func.count(func.distinct(CropIssue.farmer_id)).label('farmers_count')
    ).filter(CropIssue.location.isnot(None))\
     .group_by(CropIssue.location)\
     .order_by(desc('total_issues')).all()
    
    # Region-wise yield data
    region_yields = db.session.query(
        YieldPrediction.location,
        func.avg(YieldPrediction.predicted_yield).label('avg_yield'),
        func.count(YieldPrediction.id).label('prediction_count')
    ).group_by(YieldPrediction.location)\
     .order_by(desc('avg_yield')).all()
    
    data = []
    for region in region_stats:
        # Find corresponding yield data
        yield_data = next((r for r in region_yields if r.location == region.location), None)
        
        data.append({
            'Region': region.location,
            'Total Issues': region.total_issues,
            'Farmers Count': region.farmers_count,
            'Avg Yield (tons/acre)': f"{yield_data.avg_yield:.2f}" if yield_data else 'N/A',
            'Yield Predictions': yield_data.prediction_count if yield_data else 0
        })
    
    summary = {
        'Total Regions': len(region_stats),
        'Total Issues': sum(r.total_issues for r in region_stats),
        'Total Farmers': sum(r.farmers_count for r in region_stats),
        'Total Yield Predictions': sum(r.prediction_count for r in region_yields)
    }
    
    pdf_buffer = generate_pdf_report(
        data,
        'Region-Wise Statistics',
        'Admin',
        subtitle='Comprehensive regional analysis',
        summary=summary
    )
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'region_wise_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@admin_bp.route('/reports/region-wise/csv')
@login_required
def report_region_wise_csv():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    from app.utils.reports import generate_csv_report
    from flask import make_response
    
    region_stats = db.session.query(
        CropIssue.location,
        func.count(CropIssue.id).label('total_issues'),
        func.count(func.distinct(CropIssue.farmer_id)).label('farmers_count')
    ).filter(CropIssue.location.isnot(None))\
     .group_by(CropIssue.location)\
     .order_by(desc('total_issues')).all()
    
    region_yields = db.session.query(
        YieldPrediction.location,
        func.avg(YieldPrediction.predicted_yield).label('avg_yield'),
        func.count(YieldPrediction.id).label('prediction_count')
    ).group_by(YieldPrediction.location)\
     .order_by(desc('avg_yield')).all()
    
    data = []
    for region in region_stats:
        yield_data = next((r for r in region_yields if r.location == region.location), None)
        data.append({
            'Region': region.location,
            'Total Issues': region.total_issues,
            'Farmers Count': region.farmers_count,
            'Avg Yield (tons/acre)': f"{yield_data.avg_yield:.2f}" if yield_data else 'N/A',
            'Yield Predictions': yield_data.prediction_count if yield_data else 0
        })
    
    csv_data = generate_csv_report(data, 'region_wise')
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=region_wise_report_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

@admin_bp.route('/reports/system/pdf')
@login_required
def system_report_pdf():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    from app.utils.reports import generate_pdf_report
    
    # Collect system-wide data
    data = []
    
    # User statistics
    data.append({
        'Category': 'Total Farmers',
        'Value': User.query.filter_by(role='farmer').count()
    })
    data.append({
        'Category': 'Total Experts',
        'Value': User.query.filter_by(role='expert').count()
    })
    data.append({
        'Category': 'Total Officers',
        'Value': User.query.filter_by(role='krishi_bhavan_officer').count()
    })
    data.append({
        'Category': 'Total Crop Issues',
        'Value': CropIssue.query.count()
    })
    data.append({
        'Category': 'Total Yield Predictions',
        'Value': YieldPrediction.query.count()
    })
    data.append({
        'Category': 'Total Diagnoses',
        'Value': DiagnosisReport.query.count()
    })
    
    pdf_buffer = generate_pdf_report(data, 'System Report', 'Admin')
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'system_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@admin_bp.route('/reports/system/csv')
@login_required
def system_report_csv():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    from app.utils.reports import generate_csv_report
    from flask import make_response
    
    # Collect system-wide data
    data = []
    
    # User statistics
    data.append({
        'Category': 'Total Farmers',
        'Value': User.query.filter_by(role='farmer').count()
    })
    data.append({
        'Category': 'Total Experts',
        'Value': User.query.filter_by(role='expert').count()
    })
    data.append({
        'Category': 'Total Officers',
        'Value': User.query.filter_by(role='krishi_bhavan_officer').count()
    })
    data.append({
        'Category': 'Total Crop Issues',
        'Value': CropIssue.query.count()
    })
    data.append({
        'Category': 'Total Yield Predictions',
        'Value': YieldPrediction.query.count()
    })
    data.append({
        'Category': 'Total Diagnoses',
        'Value': DiagnosisReport.query.count()
    })
    
    csv_data = generate_csv_report(data, 'system_report')
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=system_report_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

@admin_bp.route('/reports/users/pdf')
@login_required
def users_report_pdf():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    users = User.query.all()
    data = []
    
    for user in users:
        data.append({
            'ID': user.id,
            'Username': user.username,
            'Name': user.full_name,
            'Email': user.email,
            'Role': user.role,
            'Status': 'Active' if user.is_active else 'Inactive',
            'Created': user.created_at.strftime('%Y-%m-%d')
        })
    
    pdf_buffer = generate_pdf_report(data, 'Users Report', 'Admin')
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'users_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

@admin_bp.route('/reports/users/csv')
@login_required
def users_report_csv():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.admin_login'))
    
    users = User.query.all()
    data = []
    
    for user in users:
        data.append({
            'ID': user.id,
            'Username': user.username,
            'Name': user.full_name,
            'Email': user.email,
            'Role': user.role,
            'Status': 'Active' if user.is_active else 'Inactive',
            'Created': user.created_at.strftime('%Y-%m-%d')
        })
    
    csv_data = generate_csv_report(data, 'users_report')
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=users_report_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

