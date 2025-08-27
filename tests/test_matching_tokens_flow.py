"""
Test matching service uses org tokens including PCS codes
"""
import unittest
from unittest.mock import patch, MagicMock
from app.services.matching_service import MatchingService, build_query_terms


class TestMatchingTokensFlow(unittest.TestCase):
    """Test matching service properly uses PCS codes from get_org_tokens"""
    
    def setUp(self):
        self.service = MatchingService()
    
    @patch('app.services.matching_service.get_org_tokens')
    @patch('app.services.candid_client.NewsClient.search')
    def test_news_feed_receives_pcs_codes(self, mock_news_search, mock_get_tokens):
        """Test News API receives PCS codes when available"""
        # Stub get_org_tokens with PCS codes
        mock_get_tokens.return_value = {
            'keywords': ['education', 'youth'],
            'locations': ['Chicago', 'Illinois'],
            'pcs_subject_codes': ['ED', 'YD'],
            'pcs_population_codes': ['CH', 'YA'],
            'mission': 'Test mission'
        }
        
        # Mock news search response
        mock_news_search.return_value = []
        
        # Call news_feed with tokens
        tokens = mock_get_tokens.return_value
        self.service.news_feed(tokens)
        
        # Assert News API was called with PCS codes
        mock_news_search.assert_called_once()
        call_args = mock_news_search.call_args[1]
        self.assertEqual(call_args['pcs_subject_codes'], ['ED', 'YD'])
        self.assertEqual(call_args['pcs_population_codes'], ['CH', 'YA'])
        self.assertEqual(call_args['region'], 'Chicago')
    
    @patch('app.services.matching_service.get_org_tokens')
    @patch('app.services.candid_client.NewsClient.search')
    def test_news_feed_fallback_without_pcs(self, mock_news_search, mock_get_tokens):
        """Test News API works without PCS codes"""
        # Stub get_org_tokens without PCS codes
        mock_get_tokens.return_value = {
            'keywords': ['education', 'youth'],
            'locations': ['Chicago', 'Illinois'],
            'pcs_subject_codes': [],
            'pcs_population_codes': [],
            'mission': 'Test mission'
        }
        
        # Mock news search response
        mock_news_search.return_value = []
        
        # Call news_feed with tokens
        tokens = mock_get_tokens.return_value
        self.service.news_feed(tokens)
        
        # Assert News API was called with empty PCS lists
        mock_news_search.assert_called_once()
        call_args = mock_news_search.call_args[1]
        self.assertEqual(call_args['pcs_subject_codes'], [])
        self.assertEqual(call_args['pcs_population_codes'], [])
        self.assertEqual(call_args['region'], 'Chicago')
    
    @patch('app.services.matching_service.get_org_tokens')
    @patch('app.services.candid_client.GrantsClient.snapshot_for')
    def test_context_snapshot_uses_location(self, mock_snapshot, mock_get_tokens):
        """Test Grants API snapshot uses location from tokens"""
        # Stub get_org_tokens
        mock_get_tokens.return_value = {
            'keywords': ['education'],
            'locations': ['Chicago', 'Illinois'],
            'pcs_subject_codes': ['ED'],
            'pcs_population_codes': ['CH'],
            'mission': 'Test mission'
        }
        
        # Mock snapshot response
        mock_snapshot.return_value = {
            'award_count': 10,
            'median_award': 50000
        }
        
        # Call context_snapshot
        tokens = mock_get_tokens.return_value
        self.service.context_snapshot(tokens)
        
        # Assert snapshot_for was called with location
        mock_snapshot.assert_called_once()
        call_args = mock_snapshot.call_args[0]  # Get positional args
        # snapshot_for(query, location)
        self.assertEqual(call_args[1], 'Chicago')  # Location parameter
    
    def test_build_query_terms_with_pcs(self):
        """Test query builder with PCS codes present"""
        tokens = {
            'keywords': ['education', 'youth'],
            'locations': ['Chicago', 'Illinois'],
            'pcs_subject_codes': ['ED', 'YD'],
            'pcs_population_codes': ['CH', 'YA'],
            'mission': 'Test mission'
        }
        
        result = build_query_terms(tokens)
        
        # Assert location is used
        self.assertEqual(result['region'], 'Chicago')
        # Assert keywords are in news query
        self.assertIn('education', result['news_query'])
        # Assert keywords for transactions (PCS codes don't go in text query)
        self.assertIn('education', result['transactions_query'])
        self.assertIn('Chicago', result['transactions_query'])
    
    def test_build_query_terms_without_pcs(self):
        """Test query builder without PCS codes"""
        tokens = {
            'keywords': ['education', 'youth'],
            'locations': ['Chicago', 'Illinois'],
            'pcs_subject_codes': [],
            'pcs_population_codes': [],
            'mission': 'Test mission'
        }
        
        result = build_query_terms(tokens)
        
        # Should still work with keywords only
        self.assertEqual(result['region'], 'Chicago')
        self.assertIn('education', result['news_query'])
        self.assertIn('education', result['transactions_query'])
    
    @patch('app.services.matching_service.get_org_tokens')
    @patch('app.services.matching_service.MatchingService.news_feed')
    @patch('app.services.matching_service.MatchingService.context_snapshot')
    @patch('app.services.matching_service.MatchingService.federal_feed')
    def test_assemble_passes_tokens_to_all_methods(self, mock_federal, mock_context, mock_news, mock_get_tokens):
        """Test assemble calls get_org_tokens and passes tokens to all methods"""
        # Stub get_org_tokens with PCS codes
        mock_get_tokens.return_value = {
            'keywords': ['education'],
            'locations': ['Chicago'],
            'pcs_subject_codes': ['ED'],
            'pcs_population_codes': ['CH'],
            'mission': 'Test mission'
        }
        
        # Mock method responses
        mock_news.return_value = []
        mock_federal.return_value = []
        mock_context.return_value = {'award_count': 0}
        
        # Call assemble
        result = self.service.assemble(org_id=1, limit=25)
        
        # Assert get_org_tokens was called with org_id
        mock_get_tokens.assert_called_once_with(1)
        
        # Assert all methods received tokens
        tokens = mock_get_tokens.return_value
        mock_news.assert_called_once_with(tokens)
        mock_context.assert_called_once_with(tokens)
        mock_federal.assert_called_once_with(tokens)
        
        # Assert result includes tokens
        self.assertEqual(result['tokens'], tokens)


if __name__ == '__main__':
    unittest.main()