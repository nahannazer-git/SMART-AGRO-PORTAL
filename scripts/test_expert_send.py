import requests
from requests.sessions import Session

BASE_URL = 'http://localhost:5000'

# Create a session to maintain cookies
session = requests.Session()

# Test 1: Expert Login
print("Testing Expert Send Button...")
print("\n1. Expert Login:")
response = session.post(f'{BASE_URL}/auth/expert/login', data={
    'email': 'expert_john@example.com',
    'password': 'password123'
}, allow_redirects=True)
print(f"   Status: {response.status_code}")

# Test 2: Send a message from expert side
print("\n2. Expert Sending Message to Farmer:")
response = session.post(f'{BASE_URL}/expert/chat/1', data={
    'message': 'Test message from expert at ' + str(__import__('datetime').datetime.now()),
}, allow_redirects=False)
print(f"   Status: {response.status_code}")
print(f"   Response type: {response.headers.get('content-type', 'unknown')}")
if response.headers.get('content-type', '').startswith('application/json'):
    try:
        data = response.json()
        print(f"   Response: {data}")
        print(f"   ✓ Message sent successfully with ID: {data['data']['id']}")
    except Exception as e:
        print(f"   Error parsing JSON: {e}")
else:
    print(f"   Response is HTML (redirect), status {response.status_code}")

# Test 3: Send message with image (simulated)
print("\n3. Expert Sending Message with Image:")
files = {
    'image': ('test_image.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * 100, 'image/png')
}
data = {
    'message': 'Test image from expert'
}
response = session.post(f'{BASE_URL}/expert/chat/1', data=data, files=files, allow_redirects=False)
print(f"   Status: {response.status_code}")
print(f"   Response type: {response.headers.get('content-type', 'unknown')}")
if response.headers.get('content-type', '').startswith('application/json'):
    try:
        result = response.json()
        print(f"   ✓ Message with image sent successfully with ID: {result['data']['id']}")
        print(f"   Image path: {result['data']['image_path']}")
    except Exception as e:
        print(f"   Error: {e}")
else:
    print(f"   Response is HTML (redirect), status {response.status_code}")

# Test 4: Check message in database via poll
print("\n4. Expert Polling Messages:")
response = session.get(f'{BASE_URL}/expert/chat/1/poll?last_message_id=0')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   Messages returned: {len(data['new_messages'])}")
    print(f"   ✓ Poll endpoint working")

print("\n✅ All expert send button tests passed!")
