"""
Test Grants.gov Client with fixtures
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import urllib.error

from app.services.grants_gov_client import GrantsGovClient

class TestGrantsGovClient(unittest.TestCase):
    
    def setUp(self):
        """Set up test client"""
        self.client = GrantsGovClient()
        
    @patch('urllib.request.urlopen')
    def test_search_opportunities_success(self, mock_urlopen):
        """Test successful opportunity search"""
        # Mock response
        mock_data = {
            "opportunities": [
                {
                    "opportunityNumber": "EPA-2024-001",
                    "title": "Environmental Grant",
                    "agency": "EPA",
                    "postedDate": "2024-01-01",
                    "closeDate": "2024-06-01",
                    "eligibility": "Nonprofits",
                    "awardFloor": 10000,
                    "awardCeiling": 100000
                },
                {
                    "opportunityNumber": "NSF-2024-002",
                    "title": "Science Research",
                    "agency": "NSF",
                    "postedDate": "2024-01-15",
                    "closeDate": "2024-07-01",
                    "eligibility": "Universities"
                    # No award amounts - should not invent them
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(mock_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Test search
        result = self.client.search_opportunities({"keyword": "environment"})
        
        # Verify results
        self.assertEqual(len(result), 2)
        
        # Check first opportunity
        opp1 = result[0]
        self.assertEqual(opp1["source"], "grants_gov")
        self.assertEqual(opp1["opp_number"], "EPA-2024-001")
        self.assertEqual(opp1["title"], "Environmental Grant")
        self.assertEqual(opp1["agency"], "EPA")
        self.assertEqual(opp1["award_floor"], 10000)
        self.assertEqual(opp1["award_ceiling"], 100000)
        self.assertIn("search-results-detail/EPA-2024-001", opp1["link"])
        
        # Check second opportunity - no award amounts
        opp2 = result[1]
        self.assertEqual(opp2["opp_number"], "NSF-2024-002")
        self.assertNotIn("award_floor", opp2)  # Should not invent amounts
        self.assertNotIn("award_ceiling", opp2)
        
    @patch('urllib.request.urlopen')
    def test_search_opportunities_error_handling(self, mock_urlopen):
        """Test error handling returns empty list"""
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 500, 'Server Error', {}, None)
        
        result = self.client.search_opportunities({"keyword": "test"})
        
        # Should return empty list, not crash
        self.assertEqual(result, [])
        
    @patch('urllib.request.urlopen')
    def test_search_opportunities_timeout(self, mock_urlopen):
        """Test timeout handling"""
        mock_urlopen.side_effect = TimeoutError("Connection timed out")
        
        result = self.client.search_opportunities({"keyword": "test"})
        
        # Should return empty list, not crash
        self.assertEqual(result, [])
        
    @patch('urllib.request.urlopen')
    def test_fetch_opportunity_success(self, mock_urlopen):
        """Test fetching detailed opportunity"""
        mock_data = {
            "title": "Detailed Grant Title",
            "agency": "Federal Agency",
            "description": "Full description of the grant",
            "eligibility": "Detailed eligibility requirements",
            "closeDate": "2024-12-31",
            "postedDate": "2024-01-01",
            "additionalInfo": "Extra information"
        }
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(mock_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.client.fetch_opportunity("TEST-2024-001")
        
        # Verify detailed fields
        self.assertEqual(result["source"], "grants_gov")
        self.assertEqual(result["opp_number"], "TEST-2024-001")
        self.assertEqual(result["title"], "Detailed Grant Title")
        self.assertEqual(result["agency"], "Federal Agency")
        self.assertEqual(result["description"], "Full description of the grant")
        self.assertEqual(result["eligibility_text"], "Detailed eligibility requirements")
        self.assertIn("search-results-detail/TEST-2024-001", result["link"])
        self.assertIn("additionalInfo", result["raw"])  # Raw data preserved
        
    @patch('urllib.request.urlopen')
    def test_fetch_opportunity_error_handling(self, mock_urlopen):
        """Test fetch error returns empty dict"""
        mock_urlopen.side_effect = urllib.error.HTTPError('url', 404, 'Not Found', {}, None)
        
        result = self.client.fetch_opportunity("INVALID-001")
        
        # Should return empty dict, not crash
        self.assertEqual(result, {})
        
    @patch('urllib.request.urlopen')
    def test_post_json_headers(self, mock_urlopen):
        """Test POST request headers"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"result": "ok"}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        self.client._post_json("test", {"param": "value"})
        
        # Check headers
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        
        self.assertEqual(request.headers['Content-type'], 'application/json')
        self.assertEqual(request.headers['Accept'], 'application/json')
        self.assertEqual(request.get_method(), 'POST')
        
    @patch('urllib.request.urlopen')
    def test_normalize_opportunity_missing_fields(self, mock_urlopen):
        """Test normalization with missing fields"""
        mock_data = {
            "opportunities": [
                {
                    # Missing opportunityNumber - should be skipped
                    "title": "No Number Grant"
                },
                {
                    "opportunityNumber": "VALID-001",
                    "title": "Valid Grant"
                    # Missing other fields - should use defaults
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(mock_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.client.search_opportunities({})
        
        # Should only return valid opportunity
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["opp_number"], "VALID-001")
        self.assertEqual(result[0]["agency"], "")  # Default empty string
        self.assertEqual(result[0]["eligibility_text"], "")

if __name__ == '__main__':
    unittest.main()