import sys
sys.path.insert(0, r'c:\Users\nahan\Desktop\FARMERS PORTAL')
from app import create_app
from app.models import User, ChatMessage
from datetime import datetime

app = create_app()
with app.app_context():
    # Farmer session
    farmer_client = app.test_client()
    farmer_login = {'username':'farmer_demo','password':'demo123'}
    r = farmer_client.post('/auth/farmer/login', data=farmer_login, follow_redirects=True)
    print('Farmer login status:', r.status_code)

    expert = User.query.filter_by(role='expert').first()
    farmer = User.query.filter_by(username='farmer_demo').first()
    if not expert or not farmer:
        print('Expert or farmer not found')
    else:
        # Farmer sends a message
        send_resp = farmer_client.post(f'/farmer/chat/{expert.id}', data={'message':'E2E Test message '+datetime.utcnow().isoformat()}, follow_redirects=False)
        print('Farmer send status:', send_resp.status_code, send_resp.get_json())

        # Expert session (separate client to simulate real browser cookies)
        expert_client = app.test_client()
        expert_login = {'username':'expert_demo','password':'demo123'}
        r2 = expert_client.post('/auth/expert/login', data=expert_login, follow_redirects=True)
        print('Expert login status:', r2.status_code)

        # whoami check
        who = expert_client.get('/auth/whoami')
        print('Expert whoami:', who.status_code, who.get_json())

        # Poll for new messages as expert for that farmer
        poll = expert_client.get(f'/expert/chat/{farmer.id}/poll?last_message_id=0')
        print('Poll status:', poll.status_code)
        try:
            print('Poll JSON:', poll.get_json())
        except Exception as e:
            print('Poll no JSON:', e)

        # Fetch chat page HTML as expert
        page = expert_client.get(f'/expert/chat/{farmer.id}')
        print('Expert chat page status:', page.status_code)
        # Print a snippet around chatMessages container
        html = page.get_data(as_text=True)
        idx = html.find('chatMessages')
        print(html[idx:idx+400])
