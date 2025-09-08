import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token


class TestJobs:
    """Test job management endpoints."""
    
    def test_create_job(self, client: TestClient, test_employer_data, test_job_data):
        """Test job creation."""
        # Create employer
        employer_response = client.post("/api/v1/users/employers", json=test_employer_data)
        employer = employer_response.json()
        
        # Get access token
        access_token = create_access_token(data={"sub": str(employer["user"]["id"])})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Create job
        response = client.post("/api/v1/jobs", json=test_job_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == test_job_data["title"]
        assert data["company"] == test_job_data["company"]
        assert data["required_skills"] == test_job_data["required_skills"]
        assert "id" in data
    
    def test_get_job(self, client: TestClient, test_employer_data, test_job_data):
        """Test getting job by ID."""
        # Create employer and job
        employer_response = client.post("/api/v1/users/employers", json=test_employer_data)
        employer = employer_response.json()
        
        access_token = create_access_token(data={"sub": str(employer["user"]["id"])})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        job_response = client.post("/api/v1/jobs", json=test_job_data, headers=headers)
        job = job_response.json()
        
        # Get job
        response = client.get(f"/api/v1/jobs/{job['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job["id"]
        assert data["title"] == test_job_data["title"]
    
    def test_search_jobs(self, client: TestClient, test_employer_data, test_job_data):
        """Test job search."""
        # Create employer and job
        employer_response = client.post("/api/v1/users/employers", json=test_employer_data)
        employer = employer_response.json()
        
        access_token = create_access_token(data={"sub": str(employer["user"]["id"])})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        client.post("/api/v1/jobs", json=test_job_data, headers=headers)
        
        # Search jobs
        response = client.get("/api/v1/jobs?title=Python&location=San Francisco")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any(job["title"] == test_job_data["title"] for job in data)
    
    def test_update_job(self, client: TestClient, test_employer_data, test_job_data):
        """Test job update."""
        # Create employer and job
        employer_response = client.post("/api/v1/users/employers", json=test_employer_data)
        employer = employer_response.json()
        
        access_token = create_access_token(data={"sub": str(employer["user"]["id"])})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        job_response = client.post("/api/v1/jobs", json=test_job_data, headers=headers)
        job = job_response.json()
        
        # Update job
        update_data = {
            "title": "Lead Python Developer",
            "salary_min": 140000,
            "salary_max": 180000
        }
        response = client.put(f"/api/v1/jobs/{job['id']}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Lead Python Developer"
        assert data["salary_min"] == 140000
    
    def test_delete_job(self, client: TestClient, test_employer_data, test_job_data):
        """Test job deletion."""
        # Create employer and job
        employer_response = client.post("/api/v1/users/employers", json=test_employer_data)
        employer = employer_response.json()
        
        access_token = create_access_token(data={"sub": str(employer["user"]["id"])})
        headers = {"Authorization": f"Bearer {access_token}"}
        
        job_response = client.post("/api/v1/jobs", json=test_job_data, headers=headers)
        job = job_response.json()
        
        # Delete job
        response = client.delete(f"/api/v1/jobs/{job['id']}", headers=headers)
        
        assert response.status_code == 204
    
    def test_unauthorized_job_update(self, client: TestClient, test_employer_data, test_job_data):
        """Test that users can't update jobs they don't own."""
        # Create first employer and job
        employer_response1 = client.post("/api/v1/users/employers", json=test_employer_data)
        employer1 = employer_response1.json()
        
        access_token1 = create_access_token(data={"sub": str(employer1["user"]["id"])})
        headers1 = {"Authorization": f"Bearer {access_token1}"}
        
        job_response = client.post("/api/v1/jobs", json=test_job_data, headers=headers1)
        job = job_response.json()
        
        # Create second employer
        employer_data2 = test_employer_data.copy()
        employer_data2["user"]["email"] = "employer2@example.com"
        employer_response2 = client.post("/api/v1/users/employers", json=employer_data2)
        employer2 = employer_response2.json()
        
        access_token2 = create_access_token(data={"sub": str(employer2["user"]["id"])})
        headers2 = {"Authorization": f"Bearer {access_token2}"}
        
        # Try to update job with second employer's token
        update_data = {"title": "Unauthorized Update"}
        response = client.put(f"/api/v1/jobs/{job['id']}", json=update_data, headers=headers2)
        
        assert response.status_code == 403
