# Krishi Bhavan Officer Module Models
from app.models.user import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    product_type = db.Column(db.String(50), nullable=False)  # seed, fertilizer, pesticide, equipment
    description = db.Column(db.Text)
    image_path = db.Column(db.String(255))
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    unit = db.Column(db.String(20), default='kg')  # kg, liter, piece, packet, bag
    price_per_unit = db.Column(db.Float, default=0.0)  # Free products have price = 0
    is_free = db.Column(db.Boolean, default=True, nullable=False)
    category = db.Column(db.String(50))  # government_subsidy, free_distribution, etc.
    supplier = db.Column(db.String(200))
    expiry_date = db.Column(db.Date)  # For products with expiry
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref='created_products')
    
    def __repr__(self):
        return f'<Product {self.id} - {self.name}>'

class ProductStockHistory(db.Model):
    __tablename__ = 'product_stock_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)  # Positive for addition, negative for deduction
    previous_stock = db.Column(db.Integer, nullable=False)
    new_stock = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200))  # restock, distribution, adjustment, etc.
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    product = db.relationship('Product', backref='stock_history')
    changer = db.relationship('User', backref='stock_changes')
    
    def __repr__(self):
        return f'<ProductStockHistory {self.id} - Product {self.product_id}>'

