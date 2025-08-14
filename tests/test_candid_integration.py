"""
Test Candid API Integration
"""
import os
import json
import unittest
from unittest.mock import patch, MagicMock
from app.services.candid_client import CandidClient, KeyRotator, SimpleCache

class TestCandidIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        os.environ['CANDID_GRANTS_KEYS'] = 'test_key1,test_key2'
        os.environ['CANDID_NEWS_KEYS'] = 'news_key1,news_key2'
        
    def test_key_rotation(self):
        """Test key rotation logic"""
        keys = ['key1', 'key2', 'key3']
        rotator = KeyRotator(keys)
        
        # Test round-robin
        self.assertEqual(rotator.get_next_key(), 'key1')
        self.assertEqual(rotator.get_next_key(), 'key2')
        self.assertEqual(rotator.get_next_key(), 'key3')
        self.assertEqual(rotator.get_next_key(), 'key1')  # Back to start
        
        # Mark a key as failed
        rotator.mark_failed('key2')
        
        # Should skip failed key
        rotator.current_index = 0
        self.assertEqual(rotator.get_next_key(), 'key1')
        self.assertEqual(rotator.get_next_key(), 'key3')  # Skips key2
        
    def test_cache(self):
        """Test simple cache functionality"""
        cache = SimpleCache()
        
        # Test set and get
        cache.set('test_key', 'test_value', ttl=5)
        self.assertEqual(cache.get('test_key'), 'test_value')
        
        # Test missing key
        self.assertIsNone(cache.get('missing_key'))
        
        # Test TTL expiry (mock time)
        from datetime import datetime, timedelta
        cache.set('expiring_key', 'value', ttl=1)
        
        # Manually expire by setting past time
        cache.cache['expiring_key'] = ('value', datetime.now() - timedelta(seconds=2))
        self.assertIsNone(cache.get('expiring_key'))
        
    def test_client_initialization(self):
        """Test Candid client initialization"""
        client = CandidClient()
        
        # Check keys loaded
        self.assertEqual(len(client.grants_keys), 2)
        self.assertEqual(len(client.news_keys), 2)
        self.assertEqual(client.grants_keys[0], 'test_key1')
        
    @patch('urllib.request.urlopen')
    def test_search_grants(self, mock_urlopen):
        """Test grant search with mocked response"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            'grants': [
                {'title': 'Test Grant', 'amount': 50000}
            ]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        client = CandidClient()
        result = client.search_grants('education', limit=5)
        
        # Verify result
        self.assertIn('grants', result)
        self.assertEqual(len(result['grants']), 1)
        self.assertEqual(result['grants'][0]['title'], 'Test Grant')
        
    @patch('urllib.request.urlopen')
    def test_rate_limit_handling(self, mock_urlopen):
        """Test handling of rate limit errors"""
        from urllib.error import HTTPError
        
        # Mock 429 rate limit error
        mock_urlopen.side_effect = HTTPError(
            url='test', code=429, msg='Too Many Requests', 
            hdrs={}, fp=None
        )
        
        client = CandidClient()
        result = client.search_grants('test', limit=1)
        
        # Should handle error gracefully
        self.assertIn('error', result)
        self.assertIn('grants', result)
        self.assertEqual(result['grants'], [])
        
    def test_status_endpoint(self):
        """Test status checking without real API calls"""
        client = CandidClient()
        
        # Mock the search methods to avoid real API calls
        with patch.object(client, 'search_grants', return_value={'grants': []}):
            with patch.object(client, 'search_news', return_value={'articles': []}):
                status = client.test_connection()
        
        # Verify status structure
        self.assertIn('grants_api', status)
        self.assertIn('news_api', status)
        self.assertTrue(status['grants_api']['configured'])
        self.assertTrue(status['news_api']['configured'])
        self.assertEqual(status['grants_api']['key_count'], 2)
        
    def tearDown(self):
        """Clean up environment"""
        if 'CANDID_GRANTS_KEYS' in os.environ:
            del os.environ['CANDID_GRANTS_KEYS']
        if 'CANDID_NEWS_KEYS' in os.environ:
            del os.environ['CANDID_NEWS_KEYS']

if __name__ == '__main__':
    unittest.main()