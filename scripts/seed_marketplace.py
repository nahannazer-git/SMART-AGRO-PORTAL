
# Mock Data Generator
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Product, User
from datetime import datetime
import random

app = create_app()

def seed_marketplace_data():
    with app.app_context():
        # First, ensure we have an officer
        officer = User.query.filter_by(role='krishi_bhavan_officer').first()
        if not officer:
            print("No officer found. Creating one...")
            officer = User(
                username='officer1',
                email='officer1@example.com',
                full_name='Officer John Doe',
                role='krishi_bhavan_officer',
                officer_id='KB-001',
                is_active=True
            )
            officer.set_password('password')
            db.session.add(officer)
            db.session.commit()
            print("Officer created.")

        print("Seeding marketplace products...")
        
        # Sample products
        products_data = [
            {
                'name': 'High-Yield Paddy Seeds (UMA)',
                'type': 'Seed',
                'description': 'Certified Uma variety paddy seeds suitable for Kerala climate. High disease resistance.',
                'stock': 500,
                'unit': 'kg',
                'is_free': True,
                'category': 'Subsidy Scheme',
                'supplier': 'State Seed Authority'
            },
            {
                'name': 'Organic Neem Cake',
                'type': 'Fertilizer',
                'description': 'Natural neem cake fertilizer for soil enrichment and pest control.',
                'stock': 200,
                'unit': 'bag',
                'is_free': False,
                'category': 'Organic Promotion',
                'supplier': 'EcoFarm Solutions'
            },
            {
                'name': 'Micro-Irrigation Kit',
                'type': 'Equipment',
                'description': 'Basic drip irrigation kit for small vegetable gardens (5 cents).',
                'stock': 50,
                'unit': 'kit',
                'is_free': True,
                'category': 'Water Conservation',
                'supplier': 'AgroTech India'
            },
            {
                'name': 'Coconutclimber Machine',
                'type': 'Equipment',
                'description': 'Safety-certified coconut climbing device. 50% subsidy available.',
                'stock': 15,
                'unit': 'piece',
                'is_free': False,
                'category': 'Machinery Support',
                'supplier': 'KeraFed'
            },
            {
                'name': 'Pseudomonas Flux',
                'type': 'Pesticide',
                'description': 'Bio-control agent for fungal diseases.',
                'stock': 300,
                'unit': 'bottle',
                'is_free': True,
                'category': 'Bio-Control',
                'supplier': 'Krishi Bhavan Lab'
            },
             {
                'name': 'Vegetable Seed Kit',
                'type': 'Seed',
                'description': 'Assorted vegetable seeds (Tomato, Chilli, Ladies Finger, Brinjal) for home garden.',
                'stock': 1000,
                'unit': 'packet',
                'is_free': True,
                'category': 'Grow Your Own Food',
                'supplier': 'Horticorp'
            }
        ]

        for p_data in products_data:
            # Check if exists
            existing = Product.query.filter_by(name=p_data['name']).first()
            if not existing:
                product = Product(
                    name=p_data['name'],
                    product_type=p_data['type'],
                    description=p_data['description'],
                    stock_quantity=p_data['stock'],
                    unit=p_data['unit'],
                    is_free=p_data['is_free'],
                    category=p_data['category'],
                    supplier=p_data['supplier'],
                    price_per_unit=0 if p_data['is_free'] else random.randint(50, 2000),
                    created_by=officer.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(product)
                print(f"Added: {p_data['name']}")
            else:
                print(f"Skipped (already exists): {p_data['name']}")
        
        db.session.commit()
        print("Seeding complete!")

if __name__ == '__main__':
    seed_marketplace_data()
