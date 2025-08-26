"""
Unit tests for Candid API clients
"""
import unittest
from unittest.mock import patch, Mock, MagicMock
import requests
from app.services.candid_client import NewsClient, GrantsClient, EssentialsClient


class TestNewsClient(unittest.TestCase):
    """Test NewsClient functionality"""
    
    @patch('app.services.candid_client.RotatingKeyPool')
    @patch('requests.get')
    def test_search_success(self, mock_get, mock_pool):
        """Test successful news search"""
        # Setup mock pool
        mock_pool_instance = Mock()
        mock_pool_instance.next.return_value = 'test-key'
        mock_pool.return_value = mock_pool_instance
        
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': '123',
                    'title': 'Test Grant News',
                    'url': 'http://example.com/news',
                    'publication_date': '2024-01-01',
                    'rfp_mentioned': True,
                    'grant_mentioned': True,
                    'content': 'Test content'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = NewsClient()
        results = client.search('test query')
        
        # Verify request was made with correct headers
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['headers']['Accept'], 'application/json')
        self.assertEqual(kwargs['headers']['Subscription-Key'], 'test-key')
        
        # Verify results formatting
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['source'], 'candid_news')
        self.assertEqual(results[0]['title'], 'Test Grant News')
        self.assertEqual(results[0]['rfp_mentioned'], True)
    
    @patch('app.services.candid_client.RotatingKeyPool')
    @patch('requests.get')
    def test_search_with_filters(self, mock_get, mock_pool):
        """Test news search with filters"""
        # Setup mocks
        mock_pool_instance = Mock()
        mock_pool_instance.next.return_value = 'test-key'
        mock_pool.return_value = mock_pool_instance
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response
        
        client = NewsClient()
        client.search('test', start_date='2024-01-01', pcs_subject_codes=['A01'])
        
        # Verify params were passed correctly
        args, kwargs = mock_get.call_args
        self.assertIn('start_date', kwargs['params'])
        self.assertIn('pcs_subject_codes', kwargs['params'])
        self.assertEqual(kwargs['params']['pcs_subject_codes'], 'A01')
    
    @patch('app.services.candid_client.RotatingKeyPool')
    @patch('requests.get')
    def test_authentication_error_retry(self, mock_get, mock_pool):
        """Test retry on 401 authentication error"""
        # Setup mock pool
        mock_pool_instance = Mock()
        mock_pool_instance.next.side_effect = ['key1', 'key2']
        mock_pool_instance.on_unauthorized_or_rate_limit.return_value = True
        mock_pool.return_value = mock_pool_instance
        
        # First call returns 401, second succeeds
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {'data': []}
        
        mock_get.side_effect = [mock_response_401, mock_response_200]
        
        client = NewsClient()
        results = client.search('test')
        
        # Should have made 2 requests (retry on 401)
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(results, [])
    
    @patch('app.services.candid_client.RotatingKeyPool')
    @patch('requests.get')
    def test_rate_limit_error_retry(self, mock_get, mock_pool):
        """Test retry on 429 rate limit error"""
        # Setup mock pool
        mock_pool_instance = Mock()
        mock_pool_instance.next.side_effect = ['key1', 'key2']
        mock_pool_instance.on_unauthorized_or_rate_limit.return_value = True
        mock_pool.return_value = mock_pool_instance
        
        # First call returns 429, second succeeds
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {'data': []}
        
        mock_get.side_effect = [mock_response_429, mock_response_200]
        
        client = NewsClient()
        results = client.search('test')
        
        # Should have made 2 requests (retry on 429)
        self.assertEqual(mock_get.call_count, 2)


class TestGrantsClient(unittest.TestCase):
    """Test GrantsClient functionality"""
    
    @patch('app.services.candid_client.RotatingKeyPool')
    @patch('requests.get')
    def test_transactions_success(self, mock_get, mock_pool):
        """Test successful transactions search"""
        # Setup mocks
        mock_pool_instance = Mock()
        mock_pool_instance.next.return_value = 'test-grants-key'
        mock_pool.return_value = mock_pool_instance
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': '456',
                    'funder_name': 'Test Foundation',
                    'amount': 50000,
                    'recipient_name': 'Test Nonprofit'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = GrantsClient()
        results = client.transactions('education grants')
        
        # Verify request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['headers']['Subscription-Key'], 'test-grants-key')
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['funder_name'], 'Test Foundation')
    
    @patch('app.services.candid_client.RotatingKeyPool')
    @patch('requests.get')
    def test_snapshot_for_with_amounts(self, mock_get, mock_pool):
        """Test snapshot calculation with grant amounts"""
        # Setup mocks
        mock_pool_instance = Mock()
        mock_pool_instance.next.return_value = 'test-key'
        mock_pool.return_value = mock_pool_instance
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'funder_name': 'Foundation A', 'amount': 10000},
                {'funder_name': 'Foundation B', 'amount': 20000}, 
                {'funder_name': 'Foundation C', 'amount': 30000},
                {'funder_name': 'Foundation A', 'award_amount': 15000}  # Different field name
            ]
        }
        mock_get.return_value = mock_response
        
        client = GrantsClient()
        snapshot = client.snapshot_for('education', 'california')
        
        # Verify snapshot calculation
        self.assertEqual(snapshot['award_count'], 4)
        self.assertEqual(snapshot['median_award'], 17500)  # Median of [10000, 15000, 20000, 30000]
        self.assertEqual(len(snapshot['recent_funders']), 3)  # Unique funders
        self.assertIn('Foundation A', snapshot['recent_funders'])
    
    @patch('app.services.candid_client.RotatingKeyPool')
    @patch('requests.get')
    def test_snapshot_for_no_amounts(self, mock_get, mock_pool):
        """Test snapshot with no valid amounts"""
        # Setup mocks
        mock_pool_instance = Mock()
        mock_pool_instance.next.return_value = 'test-key'
        mock_pool.return_value = mock_pool_instance
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'funder_name': 'Foundation A'},  # No amount
                {'funder_name': 'Foundation B', 'amount': 'undisclosed'}  # Invalid amount
            ]
        }
        mock_get.return_value = mock_response
        
        client = GrantsClient()
        snapshot = client.snapshot_for('arts', 'texas')
        
        # Verify snapshot with no amounts
        self.assertEqual(snapshot['award_count'], 2)
        self.assertIsNone(snapshot['median_award'])
        self.assertEqual(len(snapshot['recent_funders']), 2)


class TestEssentialsClient(unittest.TestCase):
    """Test EssentialsClient functionality"""
    
    @patch('os.environ.get')
    @patch('requests.get')
    def test_search_org_by_name(self, mock_get, mock_env):
        """Test organization search by name"""
        # Setup environment mock
        mock_env.return_value = 'test-essentials-key'
        
        # Setup response mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': '789',
                    'name': 'Test Organization',
                    'ein': '12-3456789',
                    'city': 'San Francisco',
                    'state': 'CA',
                    'pcs_subject_codes': ['A01', 'B02']
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = EssentialsClient()
        result = client.search_org('Test Organization')
        
        # Verify request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['headers']['Subscription-Key'], 'test-essentials-key')
        self.assertEqual(kwargs['params']['query'], 'Test Organization')
        
        # Verify result
        self.assertEqual(result['name'], 'Test Organization')
        self.assertEqual(result['ein'], '12-3456789')
    
    @patch('os.environ.get')
    @patch('requests.get')
    def test_search_org_by_ein(self, mock_get, mock_env):
        """Test organization search by EIN"""
        mock_env.return_value = 'test-key'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'ein': '12-3456789'}]}
        mock_get.return_value = mock_response
        
        client = EssentialsClient()
        client.search_org('12-3456789')
        
        # Should use EIN parameter for 9-digit input
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['ein'], '12-3456789')
        self.assertNotIn('query', kwargs['params'])
    
    @patch('os.environ.get')
    def test_no_api_key(self, mock_env):
        """Test client behavior with no API key"""
        mock_env.return_value = None
        
        client = EssentialsClient()
        result = client.search_org('test')
        
        # Should return None when no key available
        self.assertIsNone(result)
    
    @patch('os.environ.get')
    @patch('requests.get')
    def test_api_error_handling(self, mock_get, mock_env):
        """Test graceful error handling"""
        mock_env.return_value = 'test-key'
        
        # Simulate API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        client = EssentialsClient()
        result = client.search_org('test')
        
        # Should return None on errors, not crash
        self.assertIsNone(result)
    
    def test_extract_tokens(self):
        """Test token extraction from organization record"""
        client = EssentialsClient()
        
        record = {
            'pcs_subject_codes': ['A01', 'B02'],
            'pcs_population_codes': ['P01'], 
            'city': 'San Francisco',
            'state': 'California',
            'country': 'United States'
        }
        
        tokens = client.extract_tokens(record)
        
        self.assertEqual(tokens['pcs_subject_codes'], ['A01', 'B02'])
        self.assertEqual(tokens['pcs_population_codes'], ['P01'])
        self.assertIn('San Francisco', tokens['locations'])
        self.assertIn('California', tokens['locations'])
        self.assertIn('United States', tokens['locations'])
    
    def test_extract_tokens_empty_record(self):
        """Test token extraction from empty record"""
        client = EssentialsClient()
        tokens = client.extract_tokens(None)
        
        self.assertEqual(tokens['pcs_subject_codes'], [])
        self.assertEqual(tokens['pcs_population_codes'], [])
        self.assertEqual(tokens['locations'], [])


if __name__ == '__main__':
    unittest.main()