#!/usr/bin/env python3
"""
Demo User Seeding Script
Creates demo users for all 4 roles with consistent credentials for testing
"""


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User

def seed_demo_users():
    app = create_app()
    
    with app.app_context():
        # Check if demo users already exist
        if User.query.filter_by(username='farmer_demo').first():
            print("❌ Demo users already exist. Skipping seeding.")
            return
        
        # Common password for all demo users
        demo_password = "demo123"
        
        demo_users = [
            {
                'username': 'farmer_demo',
                'email': 'farmer@demo.com',
                'full_name': 'Demo Farmer',
                'phone': '9876543210',
                'address': 'Farm Village, Kerala',
                'role': 'farmer',
                'farm_size': 5.0,
                'farm_location': 'Kottayam, Kerala'
            },
            {
                'username': 'expert_demo',
                'email': 'expert@demo.com',
                'full_name': 'Dr. Demo Expert',
                'phone': '9876543211',
                'address': 'Agricultural Institute, Delhi',
                'role': 'expert',
                'expertise_area': 'Crop Disease Management',
                'qualifications': 'PhD in Plant Pathology',
                'years_of_experience': 10
            },
            {
                'username': 'admin_demo',
                'email': 'admin@demo.com',
                'full_name': 'Admin User',
                'phone': '9876543212',
                'address': 'Admin Office, Delhi',
                'role': 'admin'
            },
            {
                'username': 'officer_demo',
                'email': 'officer@demo.com',
                'full_name': 'Krishi Officer',
                'phone': '9876543213',
                'address': 'Krishi Bhavan, Mumbai',
                'role': 'krishi_bhavan_officer',
                'officer_id': 'KBO001',
                'designation': 'Agricultural Officer',
                'department': 'Agricultural Extension'
            }
        ]
        
        try:
            for user_data in demo_users:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    full_name=user_data['full_name'],
                    phone=user_data['phone'],
                    address=user_data['address'],
                    role=user_data['role'],
                    is_active=True
                )
                
                # Add role-specific fields
                if user_data['role'] == 'farmer':
                    user.farm_size = user_data.get('farm_size')
                    user.farm_location = user_data.get('farm_location')
                elif user_data['role'] == 'expert':
                    user.expertise_area = user_data.get('expertise_area')
                    user.qualifications = user_data.get('qualifications')
                    user.years_of_experience = user_data.get('years_of_experience')
                elif user_data['role'] == 'krishi_bhavan_officer':
                    user.officer_id = user_data.get('officer_id')
                    user.designation = user_data.get('designation')
                    user.department = user_data.get('department')
                
                # Set password
                user.set_password(demo_password)
                
                db.session.add(user)
            
            db.session.commit()
            
            print("✅ Demo users created successfully!\n")
            print("=" * 60)
            print("DEMO LOGIN CREDENTIALS")
            print("=" * 60)
            print(f"Password for all users: {demo_password}\n")
            
            for user_data in demo_users:
                role = user_data['role'].replace('_', ' ').title()
                print(f"🔐 {role}")
                print(f"   Username: {user_data['username']}")
                print(f"   Email: {user_data['email']}")
                print(f"   Password: {demo_password}\n")
            
            print("=" * 60)
            print("\n✨ All demo users ready for testing!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating demo users: {str(e)}")
            raise

if __name__ == '__main__':
    seed_demo_users()
