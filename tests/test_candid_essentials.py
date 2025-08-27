"""
Tests for Candid Essentials API client
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from app.services.candid_essentials import (
    CandidEssentialsClient,
    search_by_ein,
    search_by_name,
    extract_tokens
)


class TestCandidEssentialsClient:
    """Test Candid Essentials API client"""
    
    def test_headers_includes_subscription_key(self):
        """Test that headers include the Subscription-Key"""
        client = CandidEssentialsClient()
        
        # Mock the environment variable
        with patch.dict(os.environ, {"CANDID_ESSENTIALS_KEY": "test-key-123"}):
            headers = client.headers()
            
            assert "Subscription-Key" in headers
            assert headers["Subscription-Key"] == "test-key-123"
            assert headers["Accept"] == "application/json"
            assert headers["Content-Type"] == "application/json"
    
    @patch("requests.post")
    def test_search_by_ein_success(self, mock_post):
        """Test successful EIN search returns first record"""
        client = CandidEssentialsClient()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": [
                {
                    "ein": "12-3456789",
                    "name": "Test Organization",
                    "mission": "Test mission"
                },
                {
                    "ein": "98-7654321",
                    "name": "Another Org"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Test search
        with patch.dict(os.environ, {"CANDID_ESSENTIALS_KEY": "test-key"}):
            result = client.search_by_ein("12-3456789")
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL
        assert call_args[0][0] == "https://api.candid.org/essentials/v3"
        
        # Check headers
        assert "headers" in call_args[1]
        assert call_args[1]["headers"]["Subscription-Key"] == "test-key"
        
        # Check payload
        assert "json" in call_args[1]
        assert call_args[1]["json"]["filters"]["ein"] == "123456789"  # Cleaned
        assert call_args[1]["json"]["limit"] == 1
        
        # Check result
        assert result is not None
        assert result["ein"] == "12-3456789"
        assert result["name"] == "Test Organization"
    
    @patch("requests.post")
    def test_search_by_name_empty_results(self, mock_post):
        """Test name search returns None if empty results"""
        client = CandidEssentialsClient()
        
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": []
        }
        mock_post.return_value = mock_response
        
        # Test search
        with patch.dict(os.environ, {"CANDID_ESSENTIALS_KEY": "test-key"}):
            result = client.search_by_name("Nonexistent Organization")
        
        # Verify result is None
        assert result is None
    
    @patch("requests.post")
    def test_search_by_name_with_results(self, mock_post):
        """Test name search returns first matching record"""
        client = CandidEssentialsClient()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": [
                {
                    "ein": "12-3456789",
                    "name": "Pink Lemonade Foundation",
                    "website": "https://pinklemonade.org"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Test search
        with patch.dict(os.environ, {"CANDID_ESSENTIALS_KEY": "test-key"}):
            result = client.search_by_name("Pink Lemonade")
        
        # Verify request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["filters"]["name"] == "Pink Lemonade"
        
        # Check result
        assert result is not None
        assert result["name"] == "Pink Lemonade Foundation"
    
    @patch("requests.post")
    def test_auth_error_returns_none(self, mock_post):
        """Test 401/403/429 errors return None"""
        client = CandidEssentialsClient()
        
        # Test each auth error code
        for status_code in [401, 403, 429]:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_post.return_value = mock_response
            
            with patch.dict(os.environ, {"CANDID_ESSENTIALS_KEY": "test-key"}):
                result = client.search_by_ein("12-3456789")
            
            assert result is None
    
    @patch("requests.post")
    def test_network_error_returns_none(self, mock_post):
        """Test network errors return None"""
        client = CandidEssentialsClient()
        
        # Mock network error
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        with patch.dict(os.environ, {"CANDID_ESSENTIALS_KEY": "test-key"}):
            result = client.search_by_ein("12-3456789")
        
        assert result is None
    
    def test_extract_tokens_with_full_record(self):
        """Test extract_tokens returns arrays/None correctly"""
        client = CandidEssentialsClient()
        
        # Full record with all fields
        record = {
            "pcs_subject_codes": ["EDU", "HEALTH", "ARTS"],
            "pcs_population_codes": ["CHILD", "SENIOR"],
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "mission": "To help communities thrive",
            "website": "https://example.org"
        }
        
        result = client.extract_tokens(record)
        
        assert result["pcs_subject_codes"] == ["EDU", "HEALTH", "ARTS"]
        assert result["pcs_population_codes"] == ["CHILD", "SENIOR"]
        assert "New York, NY" in result["locations"]
        assert "USA" in result["locations"]
        assert result["mission"] == "To help communities thrive"
        assert result["website"] == "https://example.org"
    
    def test_extract_tokens_with_missing_fields(self):
        """Test extract_tokens handles missing fields gracefully"""
        client = CandidEssentialsClient()
        
        # Minimal record
        record = {
            "name": "Test Org"
        }
        
        result = client.extract_tokens(record)
        
        assert result["pcs_subject_codes"] == []
        assert result["pcs_population_codes"] == []
        assert result["locations"] == []
        assert result["mission"] is None
        assert result["website"] is None
    
    def test_extract_tokens_with_nested_address(self):
        """Test extract_tokens handles nested address object"""
        client = CandidEssentialsClient()
        
        record = {
            "address": {
                "city": "San Francisco",
                "state": "CA"
            }
        }
        
        result = client.extract_tokens(record)
        assert "San Francisco, CA" in result["locations"]
    
    def test_extract_tokens_with_empty_record(self):
        """Test extract_tokens handles empty/None record"""
        client = CandidEssentialsClient()
        
        # Empty dict
        result = client.extract_tokens({})
        assert result["pcs_subject_codes"] == []
        assert result["pcs_population_codes"] == []
        assert result["locations"] == []
        assert result["mission"] is None
        assert result["website"] is None
        
        # None
        result = client.extract_tokens(None)
        assert result["pcs_subject_codes"] == []
        assert result["pcs_population_codes"] == []
        assert result["locations"] == []
        assert result["mission"] is None
        assert result["website"] is None
    
    def test_convenience_functions(self):
        """Test module-level convenience functions"""
        with patch.object(CandidEssentialsClient, 'search_by_ein') as mock_ein:
            mock_ein.return_value = {"ein": "12-3456789"}
            result = search_by_ein("12-3456789")
            assert result["ein"] == "12-3456789"
            mock_ein.assert_called_once_with("12-3456789", 1)
        
        with patch.object(CandidEssentialsClient, 'search_by_name') as mock_name:
            mock_name.return_value = {"name": "Test Org"}
            result = search_by_name("Test Org", limit=5)
            assert result["name"] == "Test Org"
            mock_name.assert_called_once_with("Test Org", 5)
        
        with patch.object(CandidEssentialsClient, 'extract_tokens') as mock_extract:
            mock_extract.return_value = {"mission": "Test"}
            result = extract_tokens({"test": "data"})
            assert result["mission"] == "Test"
            mock_extract.assert_called_once_with({"test": "data"})