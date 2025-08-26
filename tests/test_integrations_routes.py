"""
Unit tests for integration health routes
"""
import unittest
from unittest.mock import Mock, patch
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


class TestIntegrationHealthRoutes(unittest.TestCase):
    """Test integration health endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_health_integrations_returns_required_keys(self):
        """Test /api/health/integrations returns required structure"""
        
        response = self.client.get('/api/health/integrations')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check main sections exist
        self.assertIn('candid', data)
        self.assertIn('grants_gov', data) 
        self.assertIn('routes', data)
        
        # Check Candid section structure
        candid = data['candid']
        required_candid_keys = [
            'essentials_client', 'news_client', 'grants_client', 'secrets_present'
        ]
        for key in required_candid_keys:
            self.assertIn(key, candid)
            self.assertIsInstance(candid[key], bool)
        
        # Check Grants.gov section
        grants_gov = data['grants_gov']
        self.assertIn('client_present', grants_gov)
        self.assertIsInstance(grants_gov['client_present'], bool)
        
        # Check routes section
        routes = data['routes']
        required_route_keys = [
            'matching', 'matching_detail', 'onboarding_manual',
            'onboarding_essentials_search', 'onboarding_essentials_apply'
        ]
        for key in required_route_keys:
            self.assertIn(key, routes)
            self.assertIsInstance(routes[key], bool)
    
    def test_health_integrations_detects_clients_correctly(self):
        """Test integration detection works for existing clients"""
        
        response = self.client.get('/api/health/integrations')
        data = json.loads(response.data)
        
        # Should detect existing Candid clients
        candid = data['candid']
        self.assertTrue(candid['essentials_client'])
        self.assertTrue(candid['news_client'])
        self.assertTrue(candid['grants_client'])
        
        # Should detect Grants.gov client
        self.assertTrue(data['grants_gov']['client_present'])
        
        # Should detect matching routes
        routes = data['routes']
        self.assertTrue(routes['matching'])
        self.assertTrue(routes['matching_detail'])
    
    @patch('app.services.candid_client.EssentialsClient')
    @patch('app.services.candid_client.NewsClient') 
    @patch('app.services.candid_client.GrantsClient')
    @patch('requests.get')
    @patch('requests.post')
    def test_health_ping_returns_correct_shape(self, mock_post, mock_get, mock_grants, mock_news, mock_essentials):
        """Test /api/health/ping returns expected structure"""
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        
        response = self.client.get('/api/health/ping')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check main structure
        self.assertIn('candid', data)
        self.assertIn('grants_gov', data)
        
        # Check Candid results structure
        candid = data['candid']
        for service in ['essentials', 'news', 'grants']:
            self.assertIn(service, candid)
            service_data = candid[service]
            self.assertIn('ok', service_data)
            self.assertIn('status', service_data)
            self.assertIsInstance(service_data['ok'], bool)
            self.assertIsInstance(service_data['status'], int)
        
        # Check Grants.gov structure
        grants_gov = data['grants_gov']
        self.assertIn('ok', grants_gov)
        self.assertIn('status', grants_gov)
        self.assertIsInstance(grants_gov['ok'], bool)
        self.assertIsInstance(grants_gov['status'], int)
    
    @patch('requests.get')
    def test_ping_handles_candid_errors_gracefully(self, mock_get):
        """Test ping handles API errors without crashing"""
        
        # Mock network error
        mock_get.side_effect = Exception("Network error")
        
        response = self.client.get('/api/health/ping')
        
        # Should still return 200 with error indicators
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should indicate failures
        candid = data['candid']
        for service in ['essentials', 'news', 'grants']:
            self.assertFalse(candid[service]['ok'])
            self.assertEqual(candid[service]['status'], 0)
    
    @patch('requests.post')
    def test_ping_handles_grants_gov_errors_gracefully(self, mock_post):
        """Test ping handles Grants.gov errors without crashing"""
        
        # Mock HTTP error
        mock_post.side_effect = Exception("HTTP error")
        
        response = self.client.get('/api/health/ping')
        
        # Should still return 200 with error indicators
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should indicate failure for Grants.gov
        grants_gov = data['grants_gov']
        self.assertFalse(grants_gov['ok'])
        self.assertEqual(grants_gov['status'], 0)
    
    @patch.dict('os.environ', {
        'CANDID_ESSENTIALS_KEY': 'test_key',
        'CANDID_NEWS_KEYS': 'key1,key2',
        'CANDID_GRANTS_KEYS': 'grants_key'
    })
    def test_integrations_detects_secrets_present(self):
        """Test integration status correctly detects secrets"""
        
        response = self.client.get('/api/health/integrations')
        data = json.loads(response.data)
        
        # Should detect all secrets are present
        self.assertTrue(data['candid']['secrets_present'])
    
    @patch.dict('os.environ', {}, clear=True)
    def test_integrations_detects_secrets_missing(self):
        """Test integration status correctly detects missing secrets"""
        
        response = self.client.get('/api/health/integrations')
        data = json.loads(response.data)
        
        # Should detect secrets are missing
        self.assertFalse(data['candid']['secrets_present'])
    
    @patch('requests.get')
    def test_ping_uses_correct_endpoints_and_headers(self, mock_get):
        """Test ping calls correct endpoints with proper headers"""
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        with patch.dict('os.environ', {
            'CANDID_ESSENTIALS_KEY': 'essentials_key',
            'CANDID_NEWS_KEYS': 'news_key1,news_key2',
            'CANDID_GRANTS_KEYS': 'grants_key'
        }):
            response = self.client.get('/api/health/ping')
            
            # Should have made calls to all Candid endpoints
            self.assertEqual(mock_get.call_count, 3)
            
            # Check essentials call
            essentials_call = None
            news_call = None
            grants_call = None
            
            for call in mock_get.call_args_list:
                url = call[0][0]
                if 'essentials' in url:
                    essentials_call = call
                elif 'news' in url:
                    news_call = call
                elif 'grants' in url:
                    grants_call = call
            
            # Verify essentials endpoint
            self.assertIsNotNone(essentials_call)
            self.assertIn('essentials/v1/organizations', essentials_call[0][0])
            self.assertEqual(essentials_call[1]['headers']['Subscription-Key'], 'essentials_key')
            
            # Verify news endpoint
            self.assertIsNotNone(news_call)
            self.assertIn('news/v1/search', news_call[0][0])
            self.assertEqual(news_call[1]['headers']['Subscription-Key'], 'news_key1')
            
            # Verify grants endpoint
            self.assertIsNotNone(grants_call)
            self.assertIn('grants/v1/transactions', grants_call[0][0])
            self.assertEqual(grants_call[1]['headers']['Subscription-Key'], 'grants_key')


if __name__ == '__main__':
    unittest.main()