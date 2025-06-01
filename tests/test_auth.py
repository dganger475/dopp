"""
Authentication Tests
=================

Tests for user authentication functionality.
"""

import pytest
from flask import session, url_for
from models.user import User

def test_login_success(client, test_user, test_user_data):
    """Test successful login."""
    response = client.post('/auth/login', json={
        'username': test_user.username,
        'password': test_user_data['password']
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401

def test_login_rate_limit(client):
    """Test login rate limiting."""
    for _ in range(5):
        response = client.post('/auth/login', json={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401
    
    response = client.post('/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrongpassword'
    })
    assert response.status_code == 429

def test_register_success(client):
    """Test successful user registration."""
    response = client.post('/auth/register', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'StrongPass123!'
    })
    assert response.status_code == 302
    assert response.location == '/auth/login'

def test_register_weak_password(client):
    """Test registration with weak password."""
    response = client.post('/auth/register', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'weak'
    })
    assert response.status_code == 400
    assert 'password' in response.json['errors']

def test_register_duplicate_username(client, test_user):
    """Test registration with existing username."""
    response = client.post('/auth/register', json={
        'username': test_user.username,
        'email': 'different@example.com',
        'password': 'StrongPass123!'
    })
    assert response.status_code == 400
    assert 'username' in response.json['errors']

def test_logout(client, auth_client):
    """Test logout functionality."""
    response = auth_client.get('/auth/logout')
    assert response.status_code == 302
    assert response.location == '/auth/login'

def test_protected_route_unauthorized(client):
    """Test unauthorized access to protected routes."""
    response = client.get('/auth/account')
    assert response.status_code == 401

@pytest.mark.integration
def test_auth_flow(client):
    """Test complete authentication flow."""
    # Register
    response = client.post('/auth/register', json={
        'username': 'testflow',
        'email': 'testflow@example.com',
        'password': 'StrongPass123!'
    })
    assert response.status_code == 302
    
    # Login
    response = client.post('/auth/login', json={
        'username': 'testflow',
        'password': 'StrongPass123!'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
    
    # Access protected route
    response = client.get('/auth/account')
    assert response.status_code == 200
    
    # Logout
    response = client.get('/auth/logout')
    assert response.status_code == 302
    
    # Try accessing protected route again
    response = client.get('/auth/account')
    assert response.status_code == 302 