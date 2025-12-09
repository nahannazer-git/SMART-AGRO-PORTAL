import sys
sys.path.insert(0, r'c:\Users\nahan\Desktop\FARMERS PORTAL')
from app import create_app
from app.models import User, ChatMessage
from datetime import datetime

app = create_app()
with app.app_context():
    client = app.test_client()
    # Login as farmer and send message to expert
    login_data_farmer = {'username':'farmer_demo','password':'demo123'}
    resp = client.post('/auth/farmer/login', data=login_data_farmer, follow_redirects=True)
    print('Farmer login status:', resp.status_code)
    expert = User.query.filter_by(role='expert').first()
    if not expert:
        print('No expert found')
    else:
        expert_id = expert.id
        print('Expert id:', expert_id)
        send = client.post(f'/farmer/chat/{expert_id}', data={'message':'Message from farmer at '+datetime.utcnow().isoformat()}, follow_redirects=False)
        print('Farmer send status:', send.status_code, send.get_json())

    # Now login as expert and poll (use direct session injection for reliability in tests)
    client2 = app.test_client()
    expert_user = User.query.filter_by(username='expert_demo').first()
    # Inject login into session
    with client2.session_transaction() as sess:
        sess['_user_id'] = str(expert_user.id)
        sess['_fresh'] = True
    print('Expert user id from DB:', expert_user.id if expert_user else None)
    # Inspect latest message in DB
    latest = ChatMessage.query.order_by(ChatMessage.id.desc()).first()
    if latest:
        print('Latest message in DB -> id:', latest.id, 'farmer_id:', latest.farmer_id, 'expert_id:', latest.expert_id, 'sender_role:', latest.sender_role)
    # Poll (use farmer_id in URL)
    farmer_user = User.query.filter_by(username='farmer_demo').first()
    farmer_id = farmer_user.id if farmer_user else None
    poll = client2.get(f'/expert/chat/{farmer_id}/poll?last_message_id=0')
    print('Poll status:', poll.status_code)
    try:
        print('Poll json:', poll.get_json())
    except Exception as e:
        print('No JSON:', e)

    # Also fetch chat page rendered HTML
    page = client2.get(f'/expert/chat/{expert_id}')
    print('Chat page status:', page.status_code)
    # Print snippet of page where messages are rendered
    html = page.get_data(as_text=True)
    start = html.find('chatMessages')
    print(html[start:start+1000])
