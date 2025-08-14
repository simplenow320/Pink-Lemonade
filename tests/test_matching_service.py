"""
Test Matching Service
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services import matching_service

class TestMatchingService(unittest.TestCase):
    
    def test_build_tokens_with_org(self):
        """Test building tokens from organization"""
        with patch('app.services.matching_service.db') as mock_db:
            # Mock organization
            mock_org = MagicMock()
            mock_org.focus_areas = "education, health"
            mock_org.keywords = "youth, community"
            mock_org.state = "Illinois"
            mock_org.populations_served = "children, families"
            
            mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_org
            
            tokens = matching_service.build_tokens(1)
            
            self.assertIn("education", tokens["keywords"])
            self.assertIn("health", tokens["keywords"])
            self.assertIn("youth", tokens["keywords"])
            self.assertEqual(tokens["geo"], "Illinois")
            self.assertIn("children", tokens["populations"])
            
    def test_build_tokens_no_org(self):
        """Test building tokens with missing org"""
        with patch('app.services.matching_service.db') as mock_db:
            mock_db.session.query.return_value.filter_by.return_value.first.return_value = None
            
            tokens = matching_service.build_tokens(999)
            
            # Should return safe defaults
            self.assertEqual(tokens["keywords"], ["nonprofit", "community"])
            self.assertEqual(tokens["geo"], "United States")
            self.assertEqual(tokens["populations"], [])
    
    @patch('app.services.matching_service.get_candid_client')
    def test_news_feed(self, mock_get_client):
        """Test news feed retrieval"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock search results
        mock_client.search_news.return_value = {
            "articles": [
                {
                    "title": "New Grant Opportunity",
                    "url": "https://example.com/grant",
                    "publisher": "Foundation News",
                    "published_date": "2024-01-15",
                    "summary": "Grant for education"
                }
            ]
        }
        
        tokens = {"keywords": ["education"], "geo": "US"}
        results = matching_service.news_feed(tokens)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "candid_news")
        self.assertEqual(results[0]["title"], "New Grant Opportunity")
        self.assertIn("summary", results[0])
        
    @patch('app.services.matching_service.get_grants_gov_client')
    def test_federal_feed(self, mock_get_client):
        """Test federal opportunities feed"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock search results
        mock_client.search_opportunities.return_value = [
            {
                "source": "grants_gov",
                "opp_number": "EPA-2024-001",
                "title": "Environmental Grant",
                "agency": "EPA",
                "close_date": "06/01/2024"
            },
            {
                "source": "grants_gov",
                "opp_number": "NSF-2024-002",
                "title": "Science Grant",
                "agency": "NSF",
                "close_date": "05/01/2024"
            }
        ]
        
        tokens = {"keywords": ["environment"]}
        results = matching_service.federal_feed(tokens)
        
        self.assertEqual(len(results), 2)
        # Should be sorted by closing date
        self.assertEqual(results[0]["opp_number"], "NSF-2024-002")  # Closes first
        self.assertEqual(results[1]["opp_number"], "EPA-2024-001")
        
    @patch('app.services.matching_service.transactions_snapshot')
    def test_context_snapshot(self, mock_snapshot):
        """Test context snapshot retrieval"""
        mock_snapshot.return_value = {
            "award_count": 10,
            "median_award": 50000,
            "recent_funders": ["Foundation A", "Foundation B"],
            "source_notes": "Based on 10 transactions"
        }
        
        tokens = {"keywords": ["education"], "geo": "Chicago"}
        result = matching_service.context_snapshot(tokens)
        
        mock_snapshot.assert_called_once_with("education", "Chicago")
        self.assertEqual(result["award_count"], 10)
        self.assertEqual(result["median_award"], 50000)
        
    def test_score_item_keyword_match(self):
        """Test scoring with keyword matches"""
        item = {
            "title": "Education Grant for Youth Programs",
            "eligibility_text": "Nonprofits eligible"
        }
        tokens = {"keywords": ["education", "youth"], "geo": ""}
        snapshot = None
        
        result = matching_service.score_item(item, tokens, snapshot)
        
        # Should have keyword and nonprofit eligibility points
        self.assertGreater(result["score"], 0)
        self.assertIn("Keywords matched", result["reasons"][0])
        self.assertIn("Nonprofit eligible", result["reasons"])
        
    def test_score_item_geo_match(self):
        """Test scoring with geography match"""
        item = {
            "title": "Grant",
            "agency": "Illinois State Agency",
            "eligibility_text": ""
        }
        tokens = {"keywords": [], "geo": "Illinois"}
        
        result = matching_service.score_item(item, tokens, None)
        
        self.assertGreater(result["score"], 0)
        self.assertIn("Geography match", str(result["reasons"]))
        
    def test_score_item_award_alignment(self):
        """Test scoring with award amount alignment"""
        item = {
            "title": "Grant",
            "award_floor": 40000,
            "award_ceiling": 60000
        }
        tokens = {"keywords": []}
        snapshot = {"median_award": 50000}
        
        result = matching_service.score_item(item, tokens, snapshot)
        
        self.assertGreater(result["score"], 0)
        self.assertIn("Award range aligns", str(result["reasons"]))
        
    def test_score_item_recency_news(self):
        """Test scoring news item recency"""
        recent_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        item = {
            "title": "Grant",
            "published_at": recent_date
        }
        tokens = {"keywords": []}
        
        result = matching_service.score_item(item, tokens, None)
        
        self.assertGreater(result["score"], 0)
        self.assertIn("Recent", str(result["reasons"]))
        
    def test_score_item_closing_soon(self):
        """Test scoring federal opportunity closing soon"""
        close_date = (datetime.now() + timedelta(days=30)).strftime("%m/%d/%Y")
        item = {
            "title": "Grant",
            "close_date": close_date
        }
        tokens = {"keywords": []}
        
        result = matching_service.score_item(item, tokens, None)
        
        self.assertGreater(result["score"], 0)
        self.assertIn("Closing soon", str(result["reasons"]))
        
    def test_score_item_flags(self):
        """Test scoring flags for missing data"""
        item = {}  # Missing title
        tokens = {}  # Missing keywords
        
        result = matching_service.score_item(item, tokens, None)
        
        self.assertIn("Missing title", result["flags"])
        self.assertIn("No org keywords", result["flags"])
        
    @patch('app.services.matching_service.federal_feed')
    @patch('app.services.matching_service.news_feed')
    @patch('app.services.matching_service.context_snapshot')
    def test_assemble_results(self, mock_snapshot, mock_news, mock_federal):
        """Test assembling all results"""
        mock_federal.return_value = [
            {"title": "Federal Grant", "close_date": "06/01/2024"}
        ]
        mock_news.return_value = [
            {"title": "News Item", "published_at": "2024-01-15"}
        ]
        mock_snapshot.return_value = {
            "award_count": 5,
            "median_award": 25000
        }
        
        tokens = {"keywords": ["test"]}
        results = matching_service.assemble_results(tokens)
        
        self.assertIn("federal", results)
        self.assertIn("news", results)
        self.assertIn("context", results)
        
        # Check scoring was applied
        self.assertIn("score", results["federal"][0])
        self.assertIn("reasons", results["federal"][0])
        self.assertIn("flags", results["federal"][0])
        
    def test_no_invented_fields(self):
        """Test that no data is invented"""
        item = {
            "title": "Test Grant"
            # No amounts provided
        }
        tokens = {"keywords": ["test"]}
        snapshot = {"median_award": 50000}
        
        result = matching_service.score_item(item, tokens, snapshot)
        
        # Should not invent award amounts
        self.assertNotIn("award_floor", item)
        self.assertNotIn("award_ceiling", item)
        
        # Score should still be computed
        self.assertIsInstance(result["score"], int)
        self.assertLessEqual(result["score"], 100)

if __name__ == '__main__':
    unittest.main()