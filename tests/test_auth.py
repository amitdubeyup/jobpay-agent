import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token


class TestAuth:
    """Test authentication endpoints."""
    
    def test_login_success(self, client: TestClient, test_candidate_data):
        """Test successful login."""
        # First create a candidate
        response = client.post("/api/v1/users/candidates", json=test_candidate_data)
        assert response.status_code == 201
        
        # Now login
        login_data = {
            "username": test_candidate_data["user"]["email"],
            "password": test_candidate_data["user"]["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_refresh_token(self, client: TestClient, test_candidate_data):
        """Test token refresh."""
        # Create candidate and login
        client.post("/api/v1/users/candidates", json=test_candidate_data)
        
        login_data = {
            "username": test_candidate_data["user"]["email"],
            "password": test_candidate_data["user"]["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        tokens = login_response.json()
        
        # Refresh token
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_invalid_token(self, client: TestClient):
        """Test refresh with invalid token."""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
