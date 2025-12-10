import sys
sys.path.insert(0, r'c:\Users\nahan\Desktop\FARMERS PORTAL')
from app import create_app
from app.models import User, ChatMessage
from datetime import datetime

app = create_app()
with app.app_context():
    client = app.test_client()
    # Login as farmer_demo
    login_data = {'username':'farmer_demo','password':'demo123'}
    resp = client.post('/auth/farmer/login', data=login_data, follow_redirects=True)
    print('Login status code:', resp.status_code)

    # Find an expert id
    expert = User.query.filter_by(role='expert').first()
    if not expert:
        print('No expert found in DB')
    else:
        expert_id = expert.id
        print('Found expert id:', expert_id)
        # Count messages before
        farmer = User.query.filter_by(username='farmer_demo').first()
        before = ChatMessage.query.filter_by(farmer_id=farmer.id, expert_id=expert_id).count()
        print('Messages before:', before)
        # Send a message (farmer blueprint is registered at /farmer)
        resp2 = client.post(f'/farmer/chat/{expert_id}', data={'message':'Hello from test client at '+datetime.utcnow().isoformat()}, follow_redirects=False)
        print('Send message status:', resp2.status_code)
        try:
            print('Send message json prefix:', str(resp2.get_json())[:200])
        except Exception as e:
            print('No JSON response or error:', e)
        # DB count after
        after = ChatMessage.query.filter_by(farmer_id=farmer.id, expert_id=expert_id).count()
        print('Messages after:', after)
        # Unread count endpoint
        resp4 = client.get('/farmer/chat/unread-count')
        print('Unread count endpoint status:', resp4.status_code)
        print('Unread count json:', resp4.get_json())
        # Test logout (auth blueprint at /auth)
        resp_logout = client.get('/auth/logout', follow_redirects=False)
        print('Logout status:', resp_logout.status_code)
        # Check session cleared by accessing protected route
        resp_protected = client.get('/farmer/dashboard')
        print('Access protected after logout status (should redirect or 302):', resp_protected.status_code)
