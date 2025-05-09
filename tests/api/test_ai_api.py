"""
Tests for the AI API endpoints.
"""

import json
import pytest
from unittest.mock import patch


class TestAIApi:
    """Test class for AI API endpoints."""
    
    @patch('app.api.ai.extract_grant_info')
    def test_extract_from_text_success(self, mock_extract, client):
        """Test successful grant information extraction from text."""
        # Setup the mock to return a predefined response
        mock_data = {
            "title": "Test Grant Program",
            "funder": "Test Foundation",
            "description": "This is a test grant program",
            "amount": 50000.0,
            "due_date": "2025-12-31",
            "eligibility": "Nonprofit organizations",
            "focus_areas": ["education", "health"]
        }
        mock_extract.return_value = mock_data
        
        # Make a request to the endpoint
        response = client.post(
            '/api/ai/extract-from-text',
            json={"text": "This is a test grant description text."}
        )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check that the expected data is returned
        assert data == mock_data
        
        # Verify the mock was called correctly
        mock_extract.assert_called_once_with("This is a test grant description text.")
    
    def test_extract_from_text_missing_text(self, client):
        """Test extraction with missing text."""
        # Make a request without text
        response = client.post('/api/ai/extract-from-text', json={})
        
        # Check that the response is a bad request
        assert response.status_code == 400
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check that the error message is as expected
        assert "error" in data
        assert "Text is required" in data["error"]
    
    @patch('app.api.ai.extract_grant_info')
    def test_extract_from_text_service_error(self, mock_extract, client):
        """Test extraction when the service raises an exception."""
        # Setup the mock to raise an exception
        mock_extract.side_effect = Exception("Test service error")
        
        # Make a request to the endpoint
        response = client.post(
            '/api/ai/extract-from-text',
            json={"text": "This is a test grant description text."}
        )
        
        # Check that the response is a server error
        assert response.status_code == 500
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check that the error message is as expected
        assert "error" in data
        assert "Failed to extract grant information" in data["error"]
    
    @patch('app.api.ai.extract_grant_info_from_url')
    def test_extract_from_url_success(self, mock_extract_url, client):
        """Test successful grant information extraction from URL."""
        # Setup the mock to return a predefined response
        mock_data = {
            "title": "Web Grant Program",
            "funder": "Web Foundation",
            "description": "This is a web-based grant program",
            "amount": 75000.0,
            "due_date": "2025-10-15",
            "eligibility": "Registered nonprofits",
            "focus_areas": ["technology", "education"]
        }
        mock_extract_url.return_value = mock_data
        
        test_url = "https://example.com/grants/test"
        
        # Make a request to the endpoint
        response = client.post(
            '/api/ai/extract-from-url',
            json={"url": test_url}
        )
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check that the expected data is returned
        assert data == mock_data
        
        # Verify the mock was called correctly
        mock_extract_url.assert_called_once_with(test_url)
    
    def test_extract_from_url_missing_url(self, client):
        """Test URL extraction with missing URL."""
        # Make a request without URL
        response = client.post('/api/ai/extract-from-url', json={})
        
        # Check that the response is a bad request
        assert response.status_code == 400
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check that the error message is as expected
        assert "error" in data
        assert "URL is required" in data["error"]
    
    @patch('app.api.ai.openai')
    def test_api_status_configured(self, mock_openai, client):
        """Test API status endpoint when API key is configured."""
        # Mock the openai module to indicate it's configured
        mock_openai.__bool__.return_value = True
        
        # Make a request to the status endpoint
        response = client.get('/api/ai/status')
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check that the API is reported as configured
        assert data["api_key_configured"] is True
        assert "properly configured" in data["message"]
    
    @patch('app.api.ai.openai', None)
    def test_api_status_not_configured(self, client):
        """Test API status endpoint when API key is not configured."""
        # Make a request to the status endpoint
        response = client.get('/api/ai/status')
        
        # Check that the response is successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check that the API is reported as not configured
        assert data["api_key_configured"] is False
        assert "not configured" in data["message"]