# Admin Module Models
from app.models.user import db
from datetime import datetime

class MLDataset(db.Model):
    __tablename__ = 'ml_datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    dataset_type = db.Column(db.String(50), nullable=False)  # disease, yield, general
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_count = db.Column(db.Integer)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    uploader = db.relationship('User', backref='uploaded_datasets')
    
    def __repr__(self):
        return f'<MLDataset {self.id} - {self.name}>'

class ModelTraining(db.Model):
    __tablename__ = 'model_trainings'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(200), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # disease, yield
    dataset_id = db.Column(db.Integer, db.ForeignKey('ml_datasets.id'))
    training_status = db.Column(db.String(20), default='pending', nullable=False)  # pending, training, completed, failed
    accuracy = db.Column(db.Float)
    loss = db.Column(db.Float)
    training_duration = db.Column(db.Integer)  # in seconds
    epochs = db.Column(db.Integer)
    batch_size = db.Column(db.Integer)
    trained_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_path = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    
    dataset = db.relationship('MLDataset', backref='trainings')
    trainer = db.relationship('User', backref='model_trainings')
    
    def __repr__(self):
        return f'<ModelTraining {self.id} - {self.model_name}>'

class ModelPerformance(db.Model):
    __tablename__ = 'model_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(50), nullable=False)  # disease, yield
    model_version = db.Column(db.String(50), nullable=False)
    total_predictions = db.Column(db.Integer, default=0)
    correct_predictions = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float)
    avg_confidence = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ModelPerformance {self.id} - {self.model_type}>'

