import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token


class TestUsers:
    """Test user management endpoints."""
    
    def test_create_candidate(self, client: TestClient, test_candidate_data):
        """Test candidate creation."""
        response = client.post("/api/v1/users/candidates", json=test_candidate_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == test_candidate_data["user"]["email"]
        assert data["user"]["full_name"] == test_candidate_data["user"]["full_name"]
        assert data["skills"] == test_candidate_data["skills"]
        assert "id" in data
    
    def test_create_candidate_duplicate_email(self, client: TestClient, test_candidate_data):
        """Test candidate creation with duplicate email."""
        # Create first candidate
        client.post("/api/v1/users/candidates", json=test_candidate_data)
        
        # Try to create another with same email
        response = client.post("/api/v1/users/candidates", json=test_candidate_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_get_candidate_profile(self, client: TestClient, test_candidate_data):
        """Test getting candidate profile."""
        # Create candidate
        create_response = client.post("/api/v1/users/candidates", json=test_candidate_data)
        candidate = create_response.json()
        
        # Get access token
        access_token = create_access_token(data={"sub": str(candidate["user"]["id"])})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get profile
        response = client.get("/api/v1/users/candidates/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == test_candidate_data["user"]["email"]
    
    def test_update_candidate_profile(self, client: TestClient, test_candidate_data):
        """Test updating candidate profile."""
        # Create candidate
        create_response = client.post("/api/v1/users/candidates", json=test_candidate_data)
        candidate = create_response.json()
        
        # Get access token
        access_token = create_access_token(data={"sub": str(candidate["user"]["id"])})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Update profile
        update_data = {
            "location": "New York, NY",
            "skills": ["Python", "Django", "React"],
            "experience_years": 6
        }
        response = client.put("/api/v1/users/candidates/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["location"] == "New York, NY"
        assert data["skills"] == ["Python", "Django", "React"]
        assert data["experience_years"] == 6
    
    def test_create_employer(self, client: TestClient, test_employer_data):
        """Test employer creation."""
        response = client.post("/api/v1/users/employers", json=test_employer_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == test_employer_data["user"]["email"]
        assert data["company_name"] == test_employer_data["company_name"]
        assert "id" in data
    
    def test_get_employer_profile(self, client: TestClient, test_employer_data):
        """Test getting employer profile."""
        # Create employer
        create_response = client.post("/api/v1/users/employers", json=test_employer_data)
        employer = create_response.json()
        
        # Get access token
        access_token = create_access_token(data={"sub": str(employer["user"]["id"])})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get profile
        response = client.get("/api/v1/users/employers/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == test_employer_data["company_name"]
