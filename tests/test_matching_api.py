"""
Unit tests for Matching API
"""
import unittest
from unittest.mock import patch, Mock
import json

from app import create_app


class TestMatchingAPI(unittest.TestCase):
    """Test Matching API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Sample matching results
        self.mock_results = {
            'tokens': {
                'pcs_subject_codes': ['A01'],
                'pcs_population_codes': ['P01'],
                'locations': ['San Francisco'],
                'keywords': ['education', 'youth']
            },
            'context': {
                'award_count': 15,
                'median_award': 50000,
                'recent_funders': ['Ford Foundation'],
                'sourceNotes': {
                    'api': 'candid.grants',
                    'endpoint': 'transactions',
                    'query': 'education AND San Francisco'
                }
            },
            'news': [
                {
                    'id': '123',
                    'title': 'Education Grant Opportunity',
                    'content': 'New funding available',
                    'publication_date': '2024-01-15',
                    'score': 85,
                    'reasons': ['Subject match: education'],
                    'sourceNotes': {
                        'api': 'candid.news',
                        'query': 'RFP OR grant opportunity',
                        'window': '45d'
                    }
                }
            ],
            'federal': [
                {
                    'opportunity_number': 'ED-2024-001',
                    'title': 'Department of Education Grant',
                    'description': 'Federal education funding',
                    'posted_date': '2024-01-10',
                    'score': 78,
                    'reasons': ['Keyword match: education'],
                    'sourceNotes': {
                        'api': 'grants.gov',
                        'endpoint': 'search2',
                        'window': '45d'
                    }
                }
            ]
        }
        
        # Sample opportunity detail
        self.mock_opportunity = {
            'opportunity_number': 'ED-2024-001',
            'title': 'Department of Education Grant',
            'description': 'Detailed description of federal education funding opportunity',
            'posted_date': '2024-01-10',
            'close_date': '2024-03-15',
            'award_ceiling': 100000,
            'eligibility': 'Nonprofit organizations including 501(c)(3) entities'
        }
    
    @patch('app.api.matching.MatchingService')
    def test_get_matching_opportunities_success(self, mock_service_class):
        """Test successful matching opportunities retrieval"""
        # Mock the service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.assemble.return_value = self.mock_results
        
        # Make request
        response = self.client.get('/api/matching?orgId=123')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        
        # Check required keys exist
        self.assertIn('tokens', data)
        self.assertIn('context', data)
        self.assertIn('news', data)
        self.assertIn('federal', data)
        
        # Verify tokens structure
        tokens = data['tokens']
        self.assertIn('pcs_subject_codes', tokens)
        self.assertIn('keywords', tokens)
        self.assertIn('locations', tokens)
        
        # Verify context structure
        context = data['context']
        self.assertIn('award_count', context)
        self.assertIn('sourceNotes', context)
        
        # Verify news array
        self.assertIsInstance(data['news'], list)
        if data['news']:
            news_item = data['news'][0]
            self.assertIn('score', news_item)
            self.assertIn('reasons', news_item)
            self.assertIn('sourceNotes', news_item)
        
        # Verify federal array
        self.assertIsInstance(data['federal'], list)
        if data['federal']:
            federal_item = data['federal'][0]
            self.assertIn('score', federal_item)
            self.assertIn('sourceNotes', federal_item)
        
        # Verify service was called correctly
        mock_service.assemble.assert_called_once_with(123, 25)
    
    @patch('app.api.matching.MatchingService')
    def test_get_matching_opportunities_with_limit(self, mock_service_class):
        """Test matching opportunities with custom limit"""
        # Mock the service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.assemble.return_value = self.mock_results
        
        # Make request with limit
        response = self.client.get('/api/matching?orgId=456&limit=10')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Verify service was called with correct limit
        mock_service.assemble.assert_called_once_with(456, 10)
    
    def test_get_matching_opportunities_missing_org_id(self):
        """Test error when orgId is missing"""
        response = self.client.get('/api/matching')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('orgId parameter required', data['error'])
    
    def test_get_matching_opportunities_invalid_org_id(self):
        """Test error when orgId is invalid"""
        response = self.client.get('/api/matching?orgId=invalid')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('must be a number', data['error'])
    
    def test_get_matching_opportunities_invalid_limit(self):
        """Test error when limit is out of bounds"""
        # Test limit too low
        response = self.client.get('/api/matching?orgId=123&limit=0')
        self.assertEqual(response.status_code, 400)
        
        # Test limit too high
        response = self.client.get('/api/matching?orgId=123&limit=200')
        self.assertEqual(response.status_code, 400)
    
    @patch('app.api.matching.MatchingService')
    def test_get_matching_opportunities_service_error(self, mock_service_class):
        """Test handling of service errors"""
        # Mock service to raise exception
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.assemble.side_effect = Exception('Service error')
        
        # Make request
        response = self.client.get('/api/matching?orgId=123')
        
        # Verify error response
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Internal server error')
    
    @patch('app.api.matching.get_grants_gov_client')
    def test_get_grants_gov_detail_success(self, mock_get_client):
        """Test successful grants.gov opportunity detail retrieval"""
        # Mock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.fetch_opportunity.return_value = self.mock_opportunity
        
        # Make request
        response = self.client.get('/api/matching/detail/grants-gov/ED-2024-001')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        
        # Check required fields
        self.assertEqual(data['opportunity_number'], 'ED-2024-001')
        self.assertIn('title', data)
        self.assertIn('description', data)
        self.assertIn('sourceNotes', data)
        
        # Verify source notes
        source_notes = data['sourceNotes']
        self.assertEqual(source_notes['api'], 'grants.gov')
        self.assertEqual(source_notes['endpoint'], 'fetchOpportunity')
        self.assertEqual(source_notes['opportunityNumber'], 'ED-2024-001')
        
        # Verify client was called correctly
        mock_client.fetch_opportunity.assert_called_once_with('ED-2024-001')
    
    @patch('app.api.matching.get_grants_gov_client')
    def test_get_grants_gov_detail_not_found(self, mock_get_client):
        """Test grants.gov opportunity not found"""
        # Mock client to return None
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.fetch_opportunity.return_value = None
        
        # Make request
        response = self.client.get('/api/matching/detail/grants-gov/INVALID-001')
        
        # Verify not found response
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Opportunity not found')
    
    def test_get_grants_gov_detail_invalid_number(self):
        """Test grants.gov detail with invalid opportunity number"""
        # Test empty opportunity number
        response = self.client.get('/api/matching/detail/grants-gov/')
        self.assertEqual(response.status_code, 404)  # Flask returns 404 for missing path param
        
        # Test whitespace-only opportunity number
        response = self.client.get('/api/matching/detail/grants-gov/%20%20')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid opportunity number')
    
    @patch('app.api.matching.get_grants_gov_client')
    def test_get_grants_gov_detail_service_unavailable(self, mock_get_client):
        """Test grants.gov service unavailable"""
        # Mock client to raise exception
        mock_get_client.side_effect = Exception('Service unavailable')
        
        # Make request
        response = self.client.get('/api/matching/detail/grants-gov/ED-2024-001')
        
        # Verify service unavailable response
        self.assertEqual(response.status_code, 503)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Grants.gov service unavailable')
    
    @patch('app.api.matching.get_grants_gov_client')
    def test_get_grants_gov_detail_client_error(self, mock_get_client):
        """Test grants.gov client error during fetch"""
        # Mock client that raises exception during fetch
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.fetch_opportunity.side_effect = Exception('Client error')
        
        # Make request
        response = self.client.get('/api/matching/detail/grants-gov/ED-2024-001')
        
        # Verify error response
        self.assertEqual(response.status_code, 500)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Internal server error')


if __name__ == '__main__':
    unittest.main()