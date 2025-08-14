"""
Test Candid Client with monkeypatched requests
"""
import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import json
import os
from datetime import datetime, timedelta

# Set test environment variables
os.environ['CANDID_GRANTS_KEYS'] = 'test_key1,test_key2'
os.environ['CANDID_NEWS_KEYS'] = 'news_key1,news_key2'

from app.services.candid_client import CandidClient, RotatingKeyPool

class TestCandidClient(unittest.TestCase):
    
    def setUp(self):
        """Set up test client"""
        self.client = CandidClient()
        
    def test_rotating_key_pool(self):
        """Test key rotation"""
        pool = RotatingKeyPool('CANDID_GRANTS_KEYS')
        
        # Test rotation
        self.assertEqual(pool.get_next_key(), 'test_key1')
        self.assertEqual(pool.get_next_key(), 'test_key2')
        self.assertEqual(pool.get_next_key(), 'test_key1')  # Back to start
        
    @patch('urllib.request.urlopen')
    def test_correct_headers(self, mock_urlopen):
        """Test that correct headers are set"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"articles": []}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Make request
        self.client.search_news("test")
        
        # Check headers in request
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        
        self.assertEqual(request.headers['Accept'], 'application/json')
        self.assertIn('news_key', request.headers['Subscription-key'])
        
    @patch('urllib.request.urlopen')
    def test_key_rotation_on_401(self, mock_urlopen):
        """Test key rotation on 401 error"""
        # First call: 401 error
        # Second call: success
        error = urllib.error.HTTPError('url', 401, 'Unauthorized', {}, None)
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"data": "success"}).encode('utf-8')
        
        mock_urlopen.side_effect = [error, MagicMock(__enter__=lambda s: mock_response, __exit__=lambda *args: None)]
        
        result = self.client.get_json("http://test.com", {}, service="news")
        
        # Should have tried twice
        self.assertEqual(mock_urlopen.call_count, 2)
        
        # Check different keys were used
        first_key = mock_urlopen.call_args_list[0][0][0].headers['Subscription-key']
        second_key = mock_urlopen.call_args_list[1][0][0].headers['Subscription-key']
        self.assertNotEqual(first_key, second_key)
        
    @patch('urllib.request.urlopen')
    def test_key_rotation_on_429(self, mock_urlopen):
        """Test key rotation on 429 rate limit"""
        # First call: 429 error
        # Second call: success
        error = urllib.error.HTTPError('url', 429, 'Too Many Requests', {}, None)
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"data": "success"}).encode('utf-8')
        
        mock_urlopen.side_effect = [error, MagicMock(__enter__=lambda s: mock_response, __exit__=lambda *args: None)]
        
        result = self.client.get_json("http://test.com", {}, service="grants")
        
        # Should have tried twice
        self.assertEqual(mock_urlopen.call_count, 2)
        
    @patch('urllib.request.urlopen')
    def test_cache_hit(self, mock_urlopen):
        """Test cache hit on second identical call"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"data": "test"}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # First call - should hit API
        result1 = self.client.search_news("test", page=1)
        self.assertEqual(mock_urlopen.call_count, 1)
        
        # Second identical call - should hit cache
        result2 = self.client.search_news("test", page=1)
        self.assertEqual(mock_urlopen.call_count, 1)  # Still 1, not 2
        
        # Results should be identical
        self.assertEqual(result1, result2)
        
    @patch('urllib.request.urlopen')
    def test_search_news_params(self, mock_urlopen):
        """Test search_news with all parameters"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"articles": []}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        self.client.search_news("nonprofit", start_date="2024-01-01", region="US", page=2, size=50)
        
        # Check URL params
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        url = request.full_url
        
        self.assertIn("query=nonprofit", url)
        self.assertIn("start_date=2024-01-01", url)
        self.assertIn("region=US", url)
        self.assertIn("page=2", url)
        self.assertIn("page_size=50", url)
        
    @patch('urllib.request.urlopen')
    def test_search_transactions_params(self, mock_urlopen):
        """Test search_transactions parameters"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"transactions": []}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        self.client.search_transactions("education AND chicago", page=3, size=100)
        
        # Check URL params
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        url = request.full_url
        
        self.assertIn("query=education+AND+chicago", url)
        self.assertIn("page=3", url)
        self.assertIn("page_size=100", url)
        
    def test_cache_expiry(self):
        """Test that cache expires after TTL"""
        # Set cache with short TTL
        self.client._set_cache("test_url", {"param": "value"}, {"data": "test"}, ttl_seconds=1)
        
        # Should be in cache
        cached = self.client._get_from_cache("test_url", {"param": "value"})
        self.assertIsNotNone(cached)
        
        # Manually expire by setting past time
        key = self.client._cache_key("test_url", {"param": "value"})
        expires_at = datetime.now() - timedelta(seconds=1)
        self.client.cache[key] = (expires_at, {"data": "test"})
        
        # Should not be in cache
        cached = self.client._get_from_cache("test_url", {"param": "value"})
        self.assertIsNone(cached)

if __name__ == '__main__':
    unittest.main()