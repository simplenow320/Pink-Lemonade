"""
Test Matching API endpoints
"""
import unittest
from unittest.mock import patch, MagicMock
import json

from app import create_app

class TestMatchingAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test client"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
    @patch('app.api.matching.matching_service.build_tokens')
    @patch('app.api.matching.matching_service.assemble_results')
    def test_get_matching_results_success(self, mock_assemble, mock_build):
        """Test successful matching results retrieval"""
        # Mock tokens
        mock_build.return_value = {
            "keywords": ["education", "youth"],
            "geo": "Chicago",
            "populations": ["children"]
        }
        
        # Mock results
        mock_assemble.return_value = {
            "federal": [
                {
                    "title": "Education Grant",
                    "agency": "Dept of Education",
                    "close_date": "06/01/2024",
                    "score": 85,
                    "reasons": ["Keywords matched: 2"],
                    "link": "https://grants.gov/...",
                    "flags": []
                }
            ],
            "news": [
                {
                    "title": "New RFP Released",
                    "publisher": "Foundation News",
                    "published_at": "2024-01-15",
                    "url": "https://example.com",
                    "score": 72,
                    "reasons": ["Recent: 5 days old"],
                    "flags": []
                }
            ],
            "context": {
                "award_count": 10,
                "median_award": 50000,
                "recent_funders": ["Foundation A"],
                "source_notes": "Based on 10 transactions"
            }
        }
        
        # Make request
        response = self.client.get('/api/matching?orgId=1&limit=10')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify structure
        self.assertIn("federal", data)
        self.assertIn("news", data)
        self.assertIn("context", data)
        
        # Verify federal item
        federal_item = data["federal"][0]
        self.assertEqual(federal_item["title"], "Education Grant")
        self.assertIn("sourceNotes", federal_item)
        self.assertEqual(federal_item["sourceNotes"]["api"], "grants.gov")
        self.assertIn("keyword", federal_item["sourceNotes"])
        
        # Verify news item
        news_item = data["news"][0]
        self.assertEqual(news_item["title"], "New RFP Released")
        self.assertIn("sourceNotes", news_item)
        self.assertEqual(news_item["sourceNotes"]["api"], "candid.news")
        self.assertIn("query", news_item["sourceNotes"])
        
        # Verify context
        context = data["context"]
        self.assertEqual(context["award_count"], 10)
        self.assertIn("sourceNotes", context)
        self.assertEqual(context["sourceNotes"]["api"], "candid.grants")
        
    def test_get_matching_results_no_org_id(self):
        """Test matching results without orgId"""
        response = self.client.get('/api/matching')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertIn("orgId", data["error"])
        
    @patch('app.api.matching.matching_service.build_tokens')
    @patch('app.api.matching.matching_service.assemble_results')
    def test_get_matching_results_with_limit(self, mock_assemble, mock_build):
        """Test matching results with limit"""
        mock_build.return_value = {"keywords": ["test"]}
        
        # Return more results than limit
        mock_assemble.return_value = {
            "federal": [{"title": f"Grant {i}"} for i in range(30)],
            "news": [{"title": f"News {i}"} for i in range(30)],
            "context": None
        }
        
        response = self.client.get('/api/matching?orgId=1&limit=5')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should be limited to 5 each
        self.assertEqual(len(data["federal"]), 5)
        self.assertEqual(len(data["news"]), 5)
        
    @patch('app.api.matching.matching_service.build_tokens')
    @patch('app.api.matching.matching_service.assemble_results')
    def test_cache_hit(self, mock_assemble, mock_build):
        """Test that cache is used on second call"""
        mock_build.return_value = {"keywords": ["test"]}
        mock_assemble.return_value = {
            "federal": [],
            "news": [],
            "context": None
        }
        
        # First call
        response1 = self.client.get('/api/matching?orgId=1')
        self.assertEqual(response1.status_code, 200)
        
        # Second call - should hit cache
        response2 = self.client.get('/api/matching?orgId=1')
        self.assertEqual(response2.status_code, 200)
        
        # assemble_results should only be called once
        self.assertEqual(mock_assemble.call_count, 1)
        
        # Force refresh
        response3 = self.client.get('/api/matching?orgId=1&refresh=1')
        self.assertEqual(response3.status_code, 200)
        
        # Now should be called twice
        self.assertEqual(mock_assemble.call_count, 2)
        
    @patch('app.api.matching.get_grants_gov_client')
    def test_get_opportunity_detail_success(self, mock_get_client):
        """Test fetching opportunity details"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_client.fetch_opportunity.return_value = {
            "source": "grants_gov",
            "opp_number": "EPA-2024-001",
            "title": "Environmental Grant",
            "agency": "EPA",
            "description": "Full description",
            "eligibility_text": "Nonprofits eligible",
            "close_date": "06/01/2024",
            "link": "https://grants.gov/...",
            "raw": {"additional": "data"}
        }
        
        response = self.client.get('/api/matching/detail/grants-gov/EPA-2024-001')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify response
        self.assertEqual(data["opp_number"], "EPA-2024-001")
        self.assertEqual(data["title"], "Environmental Grant")
        self.assertIn("sourceNotes", data)
        self.assertEqual(data["sourceNotes"]["api"], "grants.gov")
        self.assertEqual(data["sourceNotes"]["opportunityNumber"], "EPA-2024-001")
        
    @patch('app.api.matching.get_grants_gov_client')
    def test_get_opportunity_detail_not_found(self, mock_get_client):
        """Test opportunity detail not found"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.fetch_opportunity.return_value = {}
        
        response = self.client.get('/api/matching/detail/grants-gov/INVALID-001')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
        
    def test_clear_cache(self):
        """Test cache clearing endpoint"""
        response = self.client.post('/api/matching/cache/clear')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("message", data)
        self.assertIn("Cache cleared", data["message"])
        self.assertIn("items_cleared", data)
        
    @patch('app.api.matching.matching_service.build_tokens')
    @patch('app.api.matching.matching_service.assemble_results')
    def test_source_notes_present(self, mock_assemble, mock_build):
        """Test that source notes are always present"""
        mock_build.return_value = {"keywords": ["test"], "geo": "US"}
        mock_assemble.return_value = {
            "federal": [{"title": "Grant"}],
            "news": [{"title": "News"}],
            "context": {"award_count": 5}
        }
        
        response = self.client.get('/api/matching?orgId=1')
        data = json.loads(response.data)
        
        # All items should have source notes
        for item in data["federal"]:
            self.assertIn("sourceNotes", item)
            self.assertIn("api", item["sourceNotes"])
            
        for item in data["news"]:
            self.assertIn("sourceNotes", item)
            self.assertIn("api", item["sourceNotes"])
            
        if data["context"]:
            self.assertIn("sourceNotes", data["context"])
            self.assertIn("api", data["context"]["sourceNotes"])

if __name__ == '__main__':
    unittest.main()