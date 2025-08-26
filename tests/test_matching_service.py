"""
Unit tests for Matching Service
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.matching_service import (
    MatchingService, 
    build_query_terms,
    FEDERAL_AVAILABLE
)


class TestBuildQueryTerms(unittest.TestCase):
    """Test query term building"""
    
    def test_build_query_terms_with_keywords(self):
        """Test query building with keywords"""
        tokens = {
            'keywords': ['education', 'youth', 'health'],
            'locations': ['San Francisco', 'CA'],
            'pcs_subject_codes': ['A01'],
            'pcs_population_codes': []
        }
        
        query_terms = build_query_terms(tokens)
        
        # Should include base RFP terms
        self.assertIn('RFP OR', query_terms['news_query'])
        self.assertIn('grant opportunity', query_terms['news_query'])
        
        # Should include top 2 keywords  
        self.assertIn('education', query_terms['news_query'])
        self.assertIn('youth', query_terms['news_query'])
        
        # Should have 45-day window
        start_date = datetime.strptime(query_terms['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(query_terms['end_date'], '%Y-%m-%d')
        self.assertEqual((end_date - start_date).days, 45)
        
        # Should set primary location
        self.assertEqual(query_terms['region'], 'San Francisco')
        
        # Should build transactions query
        self.assertIn('education', query_terms['transactions_query'])
        self.assertIn('San Francisco', query_terms['transactions_query'])
    
    def test_build_query_terms_minimal(self):
        """Test query building with minimal tokens"""
        tokens = {
            'keywords': [],
            'locations': [],
            'pcs_subject_codes': [],
            'pcs_population_codes': []
        }
        
        query_terms = build_query_terms(tokens)
        
        # Should still have base query
        self.assertIn('RFP', query_terms['news_query'])
        self.assertEqual(query_terms['region'], '')
        self.assertEqual(query_terms['transactions_query'], '')


class TestMatchingService(unittest.TestCase):
    """Test MatchingService functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tokens = {
            'pcs_subject_codes': ['A01', 'B02'],
            'pcs_population_codes': ['P01'],
            'locations': ['San Francisco', 'CA'],
            'keywords': ['education', 'youth', 'health']
        }
        
        self.sample_news_item = {
            'id': '123',
            'title': 'Education Grant RFP Available',
            'content': 'New grant opportunity for youth education programs in San Francisco',
            'publication_date': '2024-01-15',
            'rfp_mentioned': True,
            'grant_mentioned': True
        }
        
        # Use current date for federal item to pass recency filter
        current_date = datetime.now().strftime('%Y-%m-%d')
        self.sample_federal_item = {
            'opportunity_number': 'ED-2024-001',
            'title': 'Department of Education Youth Programs',
            'description': 'Federal funding for educational initiatives',
            'posted_date': current_date,
            'close_date': '2024-03-15',
            'award_ceiling': 50000,
            'eligibility': 'Nonprofit organizations including 501(c)(3)'
        }
        
        self.sample_snapshot = {
            'award_count': 25,
            'median_award': 75000,
            'recent_funders': ['Ford Foundation', 'Gates Foundation'],
            'query_used': 'education AND San Francisco'
        }
    
    @patch('app.services.matching_service.NewsClient')
    def test_news_feed_filtering(self, mock_news_client):
        """Test news feed filtering logic"""
        # Mock news client response
        mock_client = Mock()
        mock_news_client.return_value = mock_client
        mock_client.search.return_value = {
            'articles': [
                # Should be included - RFP mentioned
                {
                    'title': 'Grant RFP Available', 
                    'content': 'Apply now',
                    'rfp_mentioned': True,
                    'grant_mentioned': True
                },
                # Should be included - grant + action word
                {
                    'title': 'Grant News',
                    'content': 'Organizations can apply for funding',
                    'rfp_mentioned': False,
                    'grant_mentioned': True
                },
                # Should be excluded - grant but no action words
                {
                    'title': 'Grant Winner Announced',
                    'content': 'XYZ organization received funding',
                    'rfp_mentioned': False,
                    'grant_mentioned': True
                }
            ]
        }
        
        service = MatchingService()
        results = service.news_feed(self.tokens)
        
        # Should filter to 2 opportunity items
        self.assertEqual(len(results), 2)
        self.assertIn('RFP', results[0]['title'])
        self.assertIn('apply', results[1]['content'])
    
    @patch('app.services.matching_service.FEDERAL_AVAILABLE', True)
    @patch('app.services.matching_service.get_grants_gov_client')
    def test_federal_feed_available(self, mock_get_client):
        """Test federal feed when Grants.gov is available"""
        # Mock federal client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.search_opportunities.return_value = [self.sample_federal_item]
        
        service = MatchingService()
        results = service.federal_feed(self.tokens)
        
        # Should return federal opportunities
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['opportunity_number'], 'ED-2024-001')
        
        # Should have called with correct parameters
        mock_client.search_opportunities.assert_called_once()
        call_args = mock_client.search_opportunities.call_args[0][0]
        self.assertIn('education', call_args['keywords'])
    
    @patch('app.services.matching_service.FEDERAL_AVAILABLE', False)  
    def test_federal_feed_unavailable(self):
        """Test federal feed when Grants.gov is unavailable"""
        service = MatchingService()
        results = service.federal_feed(self.tokens)
        
        # Should return empty list
        self.assertEqual(results, [])
    
    @patch('app.services.matching_service.GrantsClient')
    def test_context_snapshot(self, mock_grants_client):
        """Test context snapshot generation"""
        # Mock grants client  
        mock_client = Mock()
        mock_grants_client.return_value = mock_client
        mock_client.snapshot_for.return_value = self.sample_snapshot
        
        service = MatchingService()
        result = service.context_snapshot(self.tokens)
        
        # Should include snapshot data
        self.assertEqual(result['award_count'], 25)
        self.assertEqual(result['median_award'], 75000)
        self.assertIn('query_used', result)
    
    def test_score_item_comprehensive(self):
        """Test comprehensive item scoring"""
        service = MatchingService()
        
        # Item with good matches
        item = {
            'title': 'Education Youth Grant',
            'description': 'Nonprofit organizations in San Francisco can apply',
            'content': 'Grant opportunity for youth education programs',
            'publication_date': datetime.now().strftime('%Y-%m-%d'),
            'award_ceiling': 75000,
            'eligibility': 'Open to 501(c)(3) nonprofit organizations',
            'close_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        }
        
        result = service.score_item(item, self.tokens, self.sample_snapshot)
        
        # Should have high score due to multiple matches
        self.assertGreater(result['score'], 60)
        
        # Should have detailed reasons
        self.assertIsInstance(result['reasons'], list)
        self.assertGreater(len(result['reasons']), 2)
        
        # Should identify keyword matches
        reason_text = ' '.join(result['reasons'])
        self.assertIn('education', reason_text.lower())
        
    def test_score_item_minimal_match(self):
        """Test scoring with minimal matches"""
        service = MatchingService()
        
        # Item with few matches
        item = {
            'title': 'Random Grant Announcement',
            'description': 'Some grant in another field',
            'publication_date': '2023-01-01'  # Old date
        }
        
        result = service.score_item(item, self.tokens, self.sample_snapshot)
        
        # Should have low score
        self.assertLess(result['score'], 30)
        self.assertIsInstance(result['reasons'], list)
    
    @patch('app.services.org_tokens.get_org_tokens')
    @patch('app.services.matching_service.NewsClient')
    @patch('app.services.matching_service.GrantsClient')
    def test_assemble_integration(self, mock_grants_client, mock_news_client, mock_get_tokens):
        """Test full assemble integration"""
        # Mock all dependencies
        mock_get_tokens.return_value = self.tokens
        
        mock_news = Mock()
        mock_news_client.return_value = mock_news
        mock_news.search.return_value = {'articles': [self.sample_news_item]}
        
        mock_grants = Mock()  
        mock_grants_client.return_value = mock_grants
        mock_grants.snapshot_for.return_value = self.sample_snapshot
        
        service = MatchingService()
        result = service.assemble(123, limit=10)
        
        # Should have all required sections
        self.assertIn('tokens', result)
        self.assertIn('context', result)
        self.assertIn('news', result)
        self.assertIn('federal', result)
        
        # News items should be scored
        if result['news']:
            self.assertIn('score', result['news'][0])
            self.assertIn('reasons', result['news'][0])
            self.assertIn('sourceNotes', result['news'][0])
        
        # Context should include source notes
        self.assertIn('sourceNotes', result['context'])
    
    def test_assemble_error_handling(self):
        """Test error handling in assemble"""
        service = MatchingService()
        
        # Should handle errors gracefully
        result = service.assemble(99999)  # Non-existent org
        
        self.assertIsInstance(result, dict)
        self.assertIn('tokens', result)
        self.assertIn('news', result)
        self.assertIn('federal', result)
        
        # Should return empty lists on error
        self.assertIsInstance(result['news'], list)
        self.assertIsInstance(result['federal'], list)


if __name__ == '__main__':
    unittest.main()