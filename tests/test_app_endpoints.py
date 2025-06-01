import pytest
from app import create_app
from extensions import db

@pytest.fixture
def client():
    app = create_app('testing')  # Make sure you have a 'testing' config
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def register_user(client, username, email, password):
    data = {
        'username': username,
        'email': email,
        'password': password,
        'password2': password,
    }
    return client.post('/auth/register', data=data, follow_redirects=True)

def login_user(client, username, password):
    return client.post('/auth/login', json={'username': username, 'password': password})

def logout_user(client):
    return client.post('/auth/logout')

def test_registration_and_login_flow(client):
    resp = register_user(client, 'testuser', 'test@example.com', 'Testpass123!')
    assert resp.status_code in (200, 201)
    assert b'success' in resp.data or b'user' in resp.data

    resp = login_user(client, 'testuser', 'Testpass123!')
    assert resp.status_code == 200
    assert b'success' in resp.data or b'user' in resp.data

    resp = client.get('/auth_status')
    assert resp.status_code == 200
    assert b'authenticated' in resp.data

def test_profile_fetch(client):
    register_user(client, 'profileuser', 'profile@example.com', 'Testpass123!')
    login_user(client, 'profileuser', 'Testpass123!')
    resp = client.get('/api/users/current')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['user']['username'] == 'profileuser'

def test_feed_fetch(client):
    register_user(client, 'feeduser', 'feed@example.com', 'Testpass123!')
    login_user(client, 'feeduser', 'Testpass123!')
    resp = client.get('/social/feed/')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'posts' in data

def test_create_post(client):
    register_user(client, 'poster', 'poster@example.com', 'Testpass123!')
    login_user(client, 'poster', 'Testpass123!')
    resp = client.post('/social/feed/create_post', json={'content': 'Hello world!'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True

def test_search(client):
    register_user(client, 'searcher', 'searcher@example.com', 'Testpass123!')
    login_user(client, 'searcher', 'Testpass123!')
    resp = client.get('/api/search')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'results' in data

def test_logout(client):
    register_user(client, 'logoutuser', 'logout@example.com', 'Testpass123!')
    login_user(client, 'logoutuser', 'Testpass123!')
    resp = logout_user(client)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True 