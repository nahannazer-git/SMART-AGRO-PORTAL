import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import db, create_app
from app.models.user import User

app = create_app()
with app.app_context():
    farmer = User.query.filter_by(id=1).first()
    if farmer:
        print(f'Farmer ID 1: {farmer.full_name}')
    else:
        print('Farmer ID 1 not found')
    
    # List all users
    users = User.query.all()
    print(f'\nAll users in database:')
    for u in users:
        print(f'  ID {u.id}: {u.full_name} ({u.role})')
