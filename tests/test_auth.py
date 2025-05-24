"""
Authentication Tests
=================

Tests for authentication functionality.
"""

import pytest
from flask import session
from models.user import User

def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post('/login', json={
        'username': test_user.username,
        'password': 'password123'
    })
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['redirect'] == '/search'
    with client.session_transaction() as sess:
        assert sess['user_id'] == test_user.id

def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials."""
    response = client.post('/login', json={
        'username': test_user.username,
        'password': 'wrong_password'
    })
    assert response.status_code == 401
    assert 'error' in response.json

def test_login_rate_limit(client, test_user):
    """Test login rate limiting."""
    for _ in range(5):
        client.post('/login', json={
            'username': test_user.username,
            'password': 'wrong_password'
        })
    
    response = client.post('/login', json={
        'username': test_user.username,
        'password': 'password123'
    })
    assert response.status_code == 429
    assert 'error' in response.json

def test_register_success(client, db):
    """Test successful registration."""
    response = client.post('/register', data={
        'username': 'new_user',
        'email': 'new@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })
    assert response.status_code == 302
    assert response.location == '/social/feed'
    
    user = User.query.filter_by(username='new_user').first()
    assert user is not None
    assert user.email == 'new@example.com'

def test_register_weak_password(client):
    """Test registration with weak password."""
    response = client.post('/register', data={
        'username': 'new_user',
        'email': 'new@example.com',
        'password': 'weak',
        'confirm_password': 'weak'
    })
    assert response.status_code == 400
    assert b'Password must be at least 8 characters long' in response.data

def test_register_duplicate_username(client, test_user):
    """Test registration with existing username."""
    response = client.post('/register', data={
        'username': test_user.username,
        'email': 'another@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    })
    assert response.status_code == 400
    assert b'Username or email already exists' in response.data

def test_logout(auth_client):
    """Test logout functionality."""
    response = auth_client.get('/logout')
    assert response.status_code == 302
    assert response.location == '/'
    with auth_client.session_transaction() as sess:
        assert 'user_id' not in sess

@pytest.mark.integration
def test_login_session_persistence(auth_client):
    """Test session persistence after login."""
    response = auth_client.get('/account')
    assert response.status_code == 200

@pytest.mark.integration
def test_protected_route_access(auth_client):
    """Test access to protected routes."""
    response = auth_client.get('/account')
    assert response.status_code == 200

def test_protected_route_unauthorized(client):
    """Test unauthorized access to protected routes."""
    response = client.get('/account')
    assert response.status_code == 302
    assert response.location.startswith('/login') 