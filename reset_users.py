
from app import create_app, db
from app.models import User

app = create_app()

def reset_passwords():
    with app.app_context():
        usernames = ['farmer_demo', 'expert_demo', 'admin_demo', 'officer_demo']
        updated_count = 0
        
        for username in usernames:
            user = User.query.filter_by(username=username).first()
            if user:
                user.set_password('demo123')
                updated_count += 1
                print(f"Updated password for {username}")
            else:
                print(f"User {username} not found. (Use seed_demo_users.py to create)")
        
        if updated_count > 0:
            db.session.commit()
            print(f"Successfully updated passwords for {updated_count} users.")

if __name__ == '__main__':
    reset_passwords()
