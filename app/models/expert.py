# Expert Module Models
from app.models.user import db
from datetime import datetime

class DiagnosisReport(db.Model):
    __tablename__ = 'diagnosis_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    crop_issue_id = db.Column(db.Integer, db.ForeignKey('crop_issues.id'), nullable=False, unique=True)
    expert_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    disease_identified = db.Column(db.String(200))
    severity = db.Column(db.String(20))  # Low, Medium, High, Critical
    treatment_plan = db.Column(db.Text, nullable=False)
    preventive_measures = db.Column(db.Text)
    recommended_products = db.Column(db.Text)  # JSON string
    ai_prediction_used = db.Column(db.Boolean, default=False)
    confidence_level = db.Column(db.String(20))  # High, Medium, Low
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    crop_issue = db.relationship('CropIssue', backref='diagnosis_report', uselist=False)
    expert = db.relationship('User', backref='diagnosis_reports')
    
    def __repr__(self):
        return f'<DiagnosisReport {self.id} for Issue {self.crop_issue_id}>'

class ExpertRating(db.Model):
    __tablename__ = 'expert_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    expert_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    crop_issue_id = db.Column(db.Integer, db.ForeignKey('crop_issues.id'))
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    expert = db.relationship('User', foreign_keys=[expert_id], backref='ratings_received')
    farmer = db.relationship('User', foreign_keys=[farmer_id], backref='ratings_given')
    crop_issue = db.relationship('CropIssue', backref='ratings')
    
    def __repr__(self):
        return f'<ExpertRating {self.id} - {self.rating} stars>'

