# Farmer Module Models
from app.models.user import db
from datetime import datetime

class CropIssue(db.Model):
    __tablename__ = 'crop_issues'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)
    crop_variety = db.Column(db.String(100))
    planting_date = db.Column(db.Date)
    issue_description = db.Column(db.Text, nullable=False)
    symptoms = db.Column(db.Text)  # JSON string of selected symptoms
    image_path = db.Column(db.String(255))
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, reviewed, resolved
    ai_prediction = db.Column(db.Text)  # JSON string of AI disease prediction
    expert_response = db.Column(db.Text)
    expert_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    farmer = db.relationship('User', foreign_keys=[farmer_id], backref='crop_issues')
    expert = db.relationship('User', foreign_keys=[expert_id])
    
    def __repr__(self):
        return f'<CropIssue {self.id} - {self.crop_type}>'

class YieldPrediction(db.Model):
    __tablename__ = 'yield_predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)
    crop_variety = db.Column(db.String(100))
    soil_type = db.Column(db.String(50), nullable=False)
    irrigation_type = db.Column(db.String(50), nullable=False)
    fertilizer_type = db.Column(db.String(50), nullable=False)
    planting_date = db.Column(db.Date, nullable=False)
    expected_harvest_date = db.Column(db.Date)
    temperature = db.Column(db.Float)  # Auto-fetched
    rainfall = db.Column(db.Float)  # Auto-fetched
    farm_size = db.Column(db.Float, nullable=False)  # in acres
    location = db.Column(db.String(200), nullable=False)
    predicted_yield = db.Column(db.Float)  # AI prediction in tons/acre
    confidence_score = db.Column(db.Float)
    ai_model_used = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    farmer = db.relationship('User', backref='yield_predictions')
    
    def __repr__(self):
        return f'<YieldPrediction {self.id} - {self.crop_type}>'

class Notice(db.Model):
    __tablename__ = 'notices'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # subsidy, scheme, alert, general
    priority = db.Column(db.String(20), default='normal')  # high, normal, low
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Krishi Bhavan Officer
    target_audience = db.Column(db.String(50), default='all')  # all, farmers, experts
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime)
    
    officer = db.relationship('User', backref='notices')
    
    def __repr__(self):
        return f'<Notice {self.id} - {self.title}>'

class ProductRequest(db.Model):
    __tablename__ = 'product_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_type = db.Column(db.String(50), nullable=False)  # seed, fertilizer, pesticide, equipment
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20), default='kg')  # kg, liter, piece, etc.
    purpose = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected, distributed
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Krishi Bhavan Officer
    approval_date = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    farmer = db.relationship('User', foreign_keys=[farmer_id], backref='product_requests')
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<ProductRequest {self.id} - {self.product_name}>'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expert_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.Text, nullable=False)
    sender_role = db.Column(db.String(20), nullable=False)  # farmer, expert
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    related_issue_id = db.Column(db.Integer, db.ForeignKey('crop_issues.id'))
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    farmer = db.relationship('User', foreign_keys=[farmer_id], backref='chat_messages')
    expert = db.relationship('User', foreign_keys=[expert_id])
    related_issue = db.relationship('CropIssue', backref='chat_messages')
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'

