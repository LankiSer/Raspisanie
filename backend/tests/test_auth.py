"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_organization(client: AsyncClient):
    """Test organization registration."""
    response = await client.post("/api/v1/auth/register", json={
        "organization_name": "New Test University",
        "email": "newadmin@test.edu",
        "password": "newpass123",
        "locale": "ru",
        "tz": "Europe/Moscow"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "newadmin@test.edu"
    assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_admin_user):
    """Test registration with duplicate email."""
    response = await client.post("/api/v1/auth/register", json={
        "organization_name": "Duplicate Org",
        "email": test_admin_user.email,
        "password": "newpass123"
    })
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_admin_user):
    """Test successful login."""
    response = await client.post("/api/v1/auth/login", json={
        "email": test_admin_user.email,
        "password": "testpass"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_admin_user.email


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_admin_user):
    """Test login with invalid credentials."""
    response = await client.post("/api/v1/auth/login", json={
        "email": test_admin_user.email,
        "password": "wrongpass"
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_non_existent_user(client: AsyncClient):
    """Test login with non-existent user."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@test.edu",
        "password": "testpass"
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, admin_auth_headers):
    """Test getting current user info."""
    response = await client.get("/api/v1/auth/me", headers=admin_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "user_id" in data
    assert "email" in data
    assert "role" in data
    assert "org_id" in data


@pytest.mark.asyncio
async def test_get_current_user_without_auth(client: AsyncClient):
    """Test getting current user without authentication."""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token."""
    response = await client.get(
        "/api/v1/auth/me", 
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
