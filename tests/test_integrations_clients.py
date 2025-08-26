"""
Unit tests for integration clients with mocked HTTP
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import requests


class TestEssentialsClient(unittest.TestCase):
    """Test Essentials API Client with mocked HTTP"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_response_data = {
            'data': [{
                'organization_name': 'Test Foundation',
                'ein': '123456789',
                'city': 'New York',
                'state': 'NY',
                'pcs_subject_codes': ['EDUCATION', 'HEALTH'],
                'pcs_population_codes': ['CHILDREN', 'LOW_INCOME']
            }]
        }
    
    @patch('requests.get')
    @patch.dict(os.environ, {'CANDID_ESSENTIALS_KEY': 'test_key'})
    def test_search_org_correct_headers_and_url(self, mock_get):
        """Test EssentialsClient uses correct base URL and headers"""
        from app.services.candid_client import EssentialsClient
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_response_data
        mock_get.return_value = mock_response
        
        client = EssentialsClient()
        result = client.search_org('Test Foundation')
        
        # Verify URL
        expected_url = 'https://api.candid.org/essentials/v1/organizations/search'
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], expected_url)
        
        # Verify headers include Subscription-Key
        headers = call_args[1]['headers']
        self.assertIn('Subscription-Key', headers)
        self.assertEqual(headers['Subscription-Key'], 'test_key')
        self.assertEqual(headers['Accept'], 'application/json')
        
        # Verify params
        params = call_args[1]['params']
        self.assertIn('query', params)
        self.assertEqual(params['query'], 'Test Foundation')
        
        # Verify result is first record
        expected_result = self.mock_response_data['data'][0]
        self.assertEqual(result, expected_result)
    
    @patch('requests.get')
    @patch.dict(os.environ, {'CANDID_ESSENTIALS_KEY': 'test_key'})
    def test_search_org_by_ein(self, mock_get):
        """Test EIN search uses ein parameter"""
        from app.services.candid_client import EssentialsClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_response_data
        mock_get.return_value = mock_response
        
        client = EssentialsClient()
        client.search_org('12-3456789')  # EIN format
        
        # Verify EIN parameter used
        params = mock_get.call_args[1]['params']
        self.assertIn('ein', params)
        self.assertEqual(params['ein'], '12-3456789')
        self.assertNotIn('query', params)
    
    @patch('requests.get')
    @patch.dict(os.environ, {'CANDID_ESSENTIALS_KEY': 'test_key'})
    def test_search_org_handles_4xx(self, mock_get):
        """Test client handles 4xx responses gracefully"""
        from app.services.candid_client import EssentialsClient
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        client = EssentialsClient()
        result = client.search_org('Nonexistent Org')
        
        # Should return None instead of crashing
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {})
    def test_search_org_no_key(self):
        """Test client handles missing API key"""
        from app.services.candid_client import EssentialsClient
        
        client = EssentialsClient()
        result = client.search_org('Test Foundation')
        
        # Should return None when no key available
        self.assertIsNone(result)
    
    def test_extract_tokens(self):
        """Test extract_tokens parses record correctly"""
        from app.services.candid_client import EssentialsClient
        
        client = EssentialsClient()
        record = {
            'pcs_subject_codes': ['EDUCATION', 'HEALTH'],
            'pcs_population_codes': ['CHILDREN', 'SENIORS'],
            'city': 'Boston',
            'state': 'MA',
            'country': 'USA'
        }
        
        result = client.extract_tokens(record)
        
        expected_subjects = ['EDUCATION', 'HEALTH']
        expected_populations = ['CHILDREN', 'SENIORS']
        expected_locations = {'Boston', 'MA', 'USA'}
        
        self.assertEqual(result['pcs_subject_codes'], expected_subjects)
        self.assertEqual(result['pcs_population_codes'], expected_populations)
        self.assertEqual(set(result['locations']), expected_locations)


class TestNewsClient(unittest.TestCase):
    """Test News API Client with mocked HTTP"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_response_data = {
            'data': [{
                'id': '123',
                'title': 'Grant RFP Available',
                'content': 'New funding opportunity',
                'publication_date': '2024-01-15',
                'rfp_mentioned': True,
                'grant_mentioned': True
            }]
        }
    
    @patch('requests.get')
    @patch.dict(os.environ, {'CANDID_NEWS_KEYS': 'key1,key2'})
    def test_search_correct_endpoint_and_params(self, mock_get):
        """Test NewsClient uses correct endpoint and params"""
        from app.services.candid_client import NewsClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_response_data
        mock_get.return_value = mock_response
        
        client = NewsClient()
        result = client.search(
            query='RFP',
            start_date='2024-01-01',
            pcs_subject_codes=['EDUCATION'],
            region='California'
        )
        
        # Verify URL
        expected_url = 'https://api.candid.org/news/v1/search'
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], expected_url)
        
        # Verify headers
        headers = call_args[1]['headers']
        self.assertIn('Subscription-Key', headers)
        self.assertEqual(headers['Accept'], 'application/json')
        
        # Verify params
        params = call_args[1]['params']
        self.assertEqual(params['query'], 'RFP')
        self.assertEqual(params['start_date'], '2024-01-01')
        self.assertEqual(params['pcs_subject_codes'], 'EDUCATION')
        self.assertEqual(params['region'], 'California')
    
    @patch('requests.get')
    @patch.dict(os.environ, {'CANDID_NEWS_KEYS': 'key1,key2'})
    def test_rfp_mentioned_field_present(self, mock_get):
        """Test rfp_mentioned field is preserved when provided"""
        from app.services.candid_client import NewsClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_response_data
        mock_get.return_value = mock_response
        
        client = NewsClient()
        result = client.search('test')
        
        # Verify rfp_mentioned field preserved
        self.assertTrue(result[0]['rfp_mentioned'])
        self.assertTrue(result[0]['grant_mentioned'])
    
    @patch('requests.get')
    @patch.dict(os.environ, {'CANDID_NEWS_KEYS': 'key1,key2'})
    def test_key_rotation_on_429(self, mock_get):
        """Test key rotation on 429 rate limit"""
        from app.services.candid_client import NewsClient
        
        # First call returns 429, second call returns 200
        response_429 = Mock()
        response_429.status_code = 429
        
        response_200 = Mock()
        response_200.status_code = 200
        response_200.json.return_value = self.mock_response_data
        
        mock_get.side_effect = [response_429, response_200]
        
        client = NewsClient()
        result = client.search('test')
        
        # Should have made 2 calls due to retry
        self.assertEqual(mock_get.call_count, 2)
        
        # Should return successful result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'Grant RFP Available')


class TestGrantsClient(unittest.TestCase):
    """Test Grants API Client with mocked HTTP"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_transactions_data = {
            'data': [
                {'amount': 50000, 'funder_name': 'Ford Foundation'},
                {'amount': 75000, 'funder_name': 'Gates Foundation'},
                {'amount': 100000, 'funder_name': 'Carnegie Corporation'}
            ]
        }
    
    @patch('requests.get')
    @patch.dict(os.environ, {'CANDID_GRANTS_KEYS': 'grants_key1'})
    def test_transactions_correct_endpoint(self, mock_get):
        """Test transactions uses correct endpoint"""
        from app.services.candid_client import GrantsClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_transactions_data
        mock_get.return_value = mock_response
        
        client = GrantsClient()
        result = client.transactions('education AND Michigan')
        
        # Verify URL
        expected_url = 'https://api.candid.org/grants/v1/transactions'
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], expected_url)
        
        # Verify params
        params = call_args[1]['params']
        self.assertEqual(params['query'], 'education AND Michigan')
        
        # Verify headers
        headers = call_args[1]['headers']
        self.assertIn('Subscription-Key', headers)
        
        # Verify result format
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['amount'], 50000)
    
    def test_snapshot_for_computes_median_correctly(self):
        """Test snapshot_for computes median correctly"""
        from app.services.candid_client import GrantsClient
        
        with patch.object(GrantsClient, 'transactions') as mock_transactions:
            mock_transactions.return_value = [
                {'amount': 25000, 'funder_name': 'Foundation A'},
                {'amount': 50000, 'funder_name': 'Foundation B'},  # This should be median
                {'amount': 75000, 'funder_name': 'Foundation C'}
            ]
            
            client = GrantsClient()
            result = client.snapshot_for('education', 'Michigan')
            
            # Verify median calculation
            self.assertEqual(result['median_award'], 50000)
            self.assertEqual(result['award_count'], 3)
            self.assertIn('Foundation A', result['recent_funders'])
            self.assertEqual(result['query_used'], 'education Michigan')
    
    def test_snapshot_for_returns_none_if_no_amounts(self):
        """Test snapshot_for returns None median if no valid amounts"""
        from app.services.candid_client import GrantsClient
        
        with patch.object(GrantsClient, 'transactions') as mock_transactions:
            # Return transactions with no valid amounts
            mock_transactions.return_value = [
                {'funder_name': 'Foundation A'},  # No amount field
                {'amount': None, 'funder_name': 'Foundation B'},  # Null amount
                {'amount': 'invalid', 'funder_name': 'Foundation C'}  # Invalid amount
            ]
            
            client = GrantsClient()
            result = client.snapshot_for('education', 'Michigan')
            
            # Should return None median when no valid amounts
            self.assertIsNone(result['median_award'])
            self.assertEqual(result['award_count'], 3)  # But still count records


class TestGrantsGovClient(unittest.TestCase):
    """Test Grants.gov API Client with mocked HTTP"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_search_response = {
            'oppHits': [{
                'oppNumber': 'ED-2024-001',
                'title': 'Education Grant',
                'description': 'Federal education funding',
                'openDate': '2024-01-01',
                'awardCeiling': 100000
            }]
        }
        
        self.mock_opportunity_response = {
            'oppNumber': 'ED-2024-001',
            'title': 'Education Grant',
            'description': 'Detailed description',
            'eligibility': 'Nonprofit organizations',
            'awardCeiling': 100000,
            'closeDate': '2024-03-15'
        }
    
    @patch('urllib.request.urlopen')
    def test_search_opportunities_posts_to_search2(self, mock_urlopen):
        """Test search_opportunities posts to correct endpoint"""
        from app.services.grants_gov_client import GrantsGovClient
        import json
        
        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(self.mock_search_response).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        client = GrantsGovClient()
        result = client.search_opportunities({'keywords': ['education']})
        
        # Verify URL
        mock_urlopen.assert_called_once()
        request = mock_urlopen.call_args[0][0]
        expected_url = 'https://api.grants.gov/v1/api/search2'
        self.assertEqual(request.full_url, expected_url)
        
        # Verify method is POST
        self.assertEqual(request.get_method(), 'POST')
        
        # Verify headers
        headers = request.headers
        self.assertEqual(headers['Content-type'], 'application/json')
        
        # Verify payload structure
        data = json.loads(request.data.decode('utf-8'))
        self.assertIn('keyword', data)
        self.assertEqual(data['keyword'], 'education')
        
        # Verify returns list
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
    
    @patch('urllib.request.urlopen')
    def test_fetch_opportunity_posts_to_fetch_endpoint(self, mock_urlopen):
        """Test fetch_opportunity posts to fetchOpportunity endpoint"""
        from app.services.grants_gov_client import GrantsGovClient
        import json
        
        # Mock response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(self.mock_opportunity_response).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        client = GrantsGovClient()
        result = client.fetch_opportunity('ED-2024-001')
        
        # Verify URL
        request = mock_urlopen.call_args[0][0]
        expected_url = 'https://api.grants.gov/v1/api/fetchOpportunity'
        self.assertEqual(request.full_url, expected_url)
        
        # Verify method is POST
        self.assertEqual(request.get_method(), 'POST')
        
        # Verify payload contains opportunity number
        data = json.loads(request.data.decode('utf-8'))
        self.assertIn('opportunityNumber', data)
        self.assertEqual(data['opportunityNumber'], 'ED-2024-001')
        
        # Verify returns dict
        self.assertIsInstance(result, dict)
        # Result may have different structure, check if it's a valid dict


if __name__ == '__main__':
    unittest.main()