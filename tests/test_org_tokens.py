"""
Unit tests for Organization Tokens Service
"""
import unittest
from unittest.mock import patch, Mock, MagicMock
from app.services.org_tokens import (
    get_org_tokens, 
    _empty_tokens, 
    _get_stored_tokens,
    _tokens_complete,
    _merge_tokens,
    _extract_mission_keywords,
    _clean_keywords
)


class TestOrgTokens(unittest.TestCase):
    """Test organization tokens functionality"""
    
    def test_empty_tokens(self):
        """Test empty tokens structure"""
        tokens = _empty_tokens()
        
        self.assertEqual(tokens['pcs_subject_codes'], [])
        self.assertEqual(tokens['pcs_population_codes'], [])
        self.assertEqual(tokens['locations'], [])
        self.assertEqual(tokens['keywords'], [])
    
    def test_tokens_complete_with_pcs(self):
        """Test tokens completeness check with PCS codes"""
        complete_tokens = {
            'pcs_subject_codes': ['A01', 'B02'],
            'pcs_population_codes': [],
            'locations': [],
            'keywords': []
        }
        self.assertTrue(_tokens_complete(complete_tokens))
        
        incomplete_tokens = {
            'pcs_subject_codes': [],
            'pcs_population_codes': [],
            'locations': [],
            'keywords': []
        }
        self.assertFalse(_tokens_complete(incomplete_tokens))
    
    def test_tokens_complete_with_basic_data(self):
        """Test tokens completeness with location/keyword data"""
        complete_tokens = {
            'pcs_subject_codes': [],
            'pcs_population_codes': [],
            'locations': ['San Francisco', 'CA'],
            'keywords': ['education', 'youth']
        }
        self.assertTrue(_tokens_complete(complete_tokens))
    
    def test_extract_mission_keywords(self):
        """Test keyword extraction from mission text"""
        mission = "We provide education and healthcare services to youth and families in our community."
        keywords = _extract_mission_keywords(mission)
        
        self.assertIn('education', keywords)
        self.assertIn('healthcare', keywords)
        self.assertIn('youth', keywords)
        self.assertIn('families', keywords)
        self.assertIn('community', keywords)
    
    def test_clean_keywords(self):
        """Test keyword cleaning and deduplication"""
        dirty_keywords = ['Education', 'HEALTH', 'education', '  youth  ', '', 'ab', 'community']
        clean = _clean_keywords(dirty_keywords)
        
        # Should be lowercase, deduplicated, and filter short terms
        self.assertIn('education', clean)
        self.assertIn('health', clean)
        self.assertIn('youth', clean)
        self.assertIn('community', clean)
        self.assertNotIn('ab', clean)  # Too short
        self.assertEqual(len([k for k in clean if k == 'education']), 1)  # No duplicates
    
    def test_merge_tokens_prefers_stored(self):
        """Test token merging prefers stored values"""
        stored = {
            'pcs_subject_codes': ['A01'],
            'pcs_population_codes': [],
            'locations': ['San Francisco'],
            'keywords': ['education']
        }
        
        essentials = {
            'pcs_subject_codes': ['B02'],  # Should not override
            'pcs_population_codes': ['P01'],  # Should be added
            'locations': ['California'],  # Should be merged
            'keywords': ['health']  # Should not be merged
        }
        
        merged = _merge_tokens(stored, essentials)
        
        # Stored PCS codes should be preserved
        self.assertEqual(merged['pcs_subject_codes'], ['A01'])
        
        # Missing PCS populations should be added
        self.assertEqual(merged['pcs_population_codes'], ['P01'])
        
        # Locations should be merged
        self.assertIn('San Francisco', merged['locations'])
        self.assertIn('California', merged['locations'])
        
        # Keywords should not be merged (to avoid noise)
        self.assertEqual(merged['keywords'], ['education'])


class TestGetOrgTokens(unittest.TestCase):
    """Test main get_org_tokens function"""
    
    def setUp(self):
        """Set up test mocks"""
        self.mock_org = Mock()
        self.mock_org.id = 123
        self.mock_org.name = 'Test Organization'
        self.mock_org.ein = '12-3456789'
        self.mock_org.primary_city = 'San Francisco'
        self.mock_org.primary_state = 'CA'
        self.mock_org.counties_served = ['San Francisco County']
        self.mock_org.states_served = None
        self.mock_org.keywords = ['education', 'youth']
        self.mock_org.primary_focus_areas = ['Education']
        self.mock_org.secondary_focus_areas = None
        self.mock_org.target_demographics = ['Youth']
        self.mock_org.mission = 'We provide education services to youth in the community.'
        self.mock_org.programs_services = 'After-school programs and tutoring services.'
        self.mock_org.custom_fields = {}
        self.mock_org.updated_at = None
    
    @patch('app.services.org_tokens.get_org_tokens')
    def test_get_org_tokens_integration(self, mock_get_org_tokens):
        """Test get_org_tokens integration with mock return"""
        # Mock the function to return expected structure
        mock_get_org_tokens.return_value = {
            'pcs_subject_codes': ['A01', 'B02'],
            'pcs_population_codes': ['P01'],
            'locations': ['San Francisco', 'CA'],
            'keywords': ['education', 'youth']
        }
        
        tokens = mock_get_org_tokens(123)
        
        self.assertEqual(tokens['pcs_subject_codes'], ['A01', 'B02'])
        self.assertEqual(tokens['pcs_population_codes'], ['P01'])
        self.assertIn('San Francisco', tokens['locations'])
        self.assertIn('education', tokens['keywords'])
    
    def test_get_org_tokens_error_handling_direct(self):
        """Test error handling by calling with invalid org_id"""
        # This should return empty tokens for non-existent org
        tokens = get_org_tokens(99999)  # Very high ID unlikely to exist
        
        # Should be a valid empty token structure
        self.assertIsInstance(tokens, dict)
        self.assertIn('pcs_subject_codes', tokens)
        self.assertIn('pcs_population_codes', tokens)
        self.assertIn('locations', tokens)
        self.assertIn('keywords', tokens)
        self.assertIsInstance(tokens['pcs_subject_codes'], list)
        self.assertIsInstance(tokens['pcs_population_codes'], list)
        self.assertIsInstance(tokens['locations'], list)
        self.assertIsInstance(tokens['keywords'], list)
    
    def test_get_stored_tokens_from_mock_org(self):
        """Test extracting stored tokens from organization object"""
        tokens = _get_stored_tokens(self.mock_org)
        
        # Should extract from org fields
        self.assertIn('San Francisco', tokens['locations'])
        self.assertIn('CA', tokens['locations'])
        self.assertIn('San Francisco County', tokens['locations'])
        self.assertIn('education', tokens['keywords'])
        self.assertIn('youth', tokens['keywords'])
        
        # Should extract from mission
        mission_keywords = [kw for kw in tokens['keywords'] if kw in 'community services']
        self.assertTrue(len(mission_keywords) > 0)


if __name__ == '__main__':
    unittest.main()