import sys
sys.path.insert(0, r'c:\Users\nahan\Desktop\FARMERS PORTAL')
from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    client = app.test_client()

    # Test as anonymous
    resp = client.get('/auth/whoami')
    print('Anonymous whoami:', resp.status_code, resp.get_json())

    # Login as farmer_demo via session injection
    farmer = User.query.filter_by(username='farmer_demo').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(farmer.id)
        sess['_fresh'] = True
    resp2 = client.get('/auth/whoami')
    print('Farmer whoami:', resp2.status_code, resp2.get_json())

    # Now test as expert via new client and session injection
    client2 = app.test_client()
    expert = User.query.filter_by(username='expert_demo').first()
    with client2.session_transaction() as sess:
        sess['_user_id'] = str(expert.id)
        sess['_fresh'] = True
    resp3 = client2.get('/auth/whoami')
    print('Expert whoami:', resp3.status_code, resp3.get_json())
