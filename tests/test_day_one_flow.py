"""
Day-One User Flow Tests
Tests the complete user journey from EIN lookup to grant analysis
"""
import pytest
import json
from unittest.mock import Mock, patch
from app import app, db
from app.models import Organization, Grant


class TestDayOneFlow:
    """Test complete user flow from EIN lookup to writing tools"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    @pytest.fixture
    def mock_org_data(self):
        """Sample organization data from Essentials lookup"""
        return {
            'ein': '123456789',
            'organization_name': 'Test Community Foundation',
            'city': 'Los Angeles',
            'state': 'CA',
            'pcs_subject_codes': ['EDUCATION', 'YOUTH_DEVELOPMENT'],
            'pcs_population_codes': ['LOW_INCOME', 'MINORITIES'],
            'mission': 'Supporting underserved communities through education and youth programs'
        }
    
    @pytest.fixture
    def sample_grants(self):
        """Sample grant opportunities"""
        return [
            {
                'title': 'Education Innovation Grant',
                'agency': 'Department of Education', 
                'opportunity_number': 'ED-2025-001',
                'score': 85,
                'award_ceiling': 250000,
                'posted_date': '2025-08-01'
            },
            {
                'title': 'Youth Development RFP',
                'source': 'Foundation Center',
                'rfp_mentioned': True,
                'score': 78,
                'publication_date': '2025-08-15'
            }
        ]
    
    def test_ein_lookup_fills_profile(self, client, mock_org_data):
        """Test: Search/paste EIN fills profile with subject, population, location"""
        with patch('app.services.candid_client.EssentialsClient') as mock_essentials:
            # Mock Essentials API response
            mock_client = Mock()
            mock_client.search_org.return_value = mock_org_data
            mock_client.extract_tokens.return_value = {
                'pcs_subject_codes': ['EDUCATION', 'YOUTH_DEVELOPMENT'],
                'pcs_population_codes': ['LOW_INCOME', 'MINORITIES'],
                'locations': ['Los Angeles', 'CA']
            }
            mock_essentials.return_value = mock_client
            
            # Test EIN lookup endpoint
            response = client.post('/api/profile/lookup-ein', 
                                 json={'ein': '123456789'})
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify profile data populated
            assert data['organization_name'] == 'Test Community Foundation'
            assert data['city'] == 'Los Angeles'
            assert data['state'] == 'CA'
            assert 'EDUCATION' in data.get('pcs_subject_codes', [])
            assert 'LOW_INCOME' in data.get('pcs_population_codes', [])
    
    def test_discover_shows_scored_opportunities(self, client, sample_grants):
        """Test: Open Discover shows Open Calls and Federal items with scores"""
        with patch('app.services.matching_service.MatchingService') as mock_service:
            # Mock matching service response
            mock_instance = Mock()
            mock_instance.assemble.return_value = {
                'tokens': {'keywords': ['education'], 'locations': ['CA']},
                'context': {'median_award': 150000, 'recent_funders': ['Gates Foundation']},
                'news': [sample_grants[1]],  # Open Calls
                'federal': [sample_grants[0]]  # Federal opportunities
            }
            mock_service.return_value = mock_instance
            
            # Test matching endpoint
            response = client.get('/api/matching?orgId=1&limit=10')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify Open Calls from news feed
            assert len(data['news']) == 1
            assert data['news'][0]['title'] == 'Youth Development RFP'
            assert data['news'][0]['rfp_mentioned'] == True
            
            # Verify Federal items with scores
            assert len(data['federal']) == 1
            assert data['federal'][0]['score'] == 85
            assert data['federal'][0]['opportunity_number'] == 'ED-2025-001'
            
            # Verify context with median award and recent funders
            assert data['context']['median_award'] == 150000
            assert 'Gates Foundation' in data['context']['recent_funders']
    
    def test_grant_detail_shows_proof_card(self, client):
        """Test: Open grant shows details and proof card with median award"""
        with patch('app.services.grants_gov_client.get_grants_gov_client') as mock_client:
            # Mock grant detail response
            mock_instance = Mock()
            mock_instance.fetch_opportunity.return_value = {
                'opportunity_number': 'ED-2025-001',
                'title': 'Education Innovation Grant',
                'description': 'Supporting innovative education programs',
                'eligibility': 'Nonprofit organizations, 501(c)(3)',
                'award_ceiling': 250000,
                'deadline': '2025-12-15',
                'sourceNotes': {
                    'api': 'grants.gov',
                    'endpoint': 'fetchOpportunity',
                    'opportunityNumber': 'ED-2025-001'
                }
            }
            mock_client.return_value = mock_instance
            
            # Test detail endpoint
            response = client.get('/api/matching/detail/grants-gov/ED-2025-001')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify grant details
            assert data['title'] == 'Education Innovation Grant'
            assert data['eligibility'] == 'Nonprofit organizations, 501(c)(3)'
            assert data['award_ceiling'] == 250000
            
            # Verify proof card information (sourceNotes)
            assert data['sourceNotes']['api'] == 'grants.gov'
            assert data['sourceNotes']['opportunityNumber'] == 'ED-2025-001'
    
    def test_save_grant_to_tracker(self, client):
        """Test: Save grant to the tracker"""
        grant_data = {
            'title': 'Education Innovation Grant',
            'funder': 'Department of Education',
            'opportunity_number': 'ED-2025-001',
            'amount_max': 250000,
            'due_date': '2025-12-15',
            'status': 'Discovery'
        }
        
        # Test grant creation
        response = client.post('/api/grants', 
                              json=grant_data,
                              headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify grant saved correctly
        assert data['title'] == 'Education Innovation Grant'
        assert data['status'] == 'Discovery'
        assert data['opportunity_number'] == 'ED-2025-001'
    
    def test_writing_tool_with_source_notes(self, client):
        """Test: Generate pitch/case with Source Notes from matching context"""
        with patch('app.services.matching_service.MatchingService') as mock_service:
            # Mock matching service for context
            mock_instance = Mock()
            mock_instance.assemble.return_value = {
                'context': {
                    'median_award': 175000,
                    'recent_funders': ['Gates Foundation', 'Ford Foundation'],
                    'sourceNotes': {
                        'api': 'candid.grants',
                        'query': 'education AND california'
                    }
                }
            }
            mock_service.return_value = mock_instance
            
            with patch('openai.OpenAI') as mock_openai:
                # Mock OpenAI response
                mock_client = Mock()
                mock_response = Mock()
                mock_response.choices = [Mock(message=Mock(content='Generated case for support content'))]
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_client
                
                # Test case for support generation
                response = client.post('/api/writing/case-for-support',
                                     json={'organization_id': 1})
                
                assert response.status_code == 200
                data = response.get_json()
                
                # Verify document generated
                assert 'content' in data
                assert data['funding_context_included'] == True
                
                # Verify source notes included in quality indicators
                quality = data.get('quality_indicators', {})
                assert quality.get('funding_market_intelligence') == True
    
    def test_dashboard_shows_award_norms(self, client):
        """Test: Dashboard tiles show award norms and recent funders"""
        with patch('app.services.matching_service.MatchingService') as mock_service:
            # Mock matching service response
            mock_instance = Mock()
            mock_instance.assemble.return_value = {
                'context': {
                    'median_award': 185000,
                    'recent_funders': ['Gates Foundation', 'Ford Foundation', 'Kellogg Foundation'],
                    'award_count': 47
                },
                'news': [{
                    'title': 'Community Grant RFP',
                    'score': 82,
                    'publication_date': '2025-08-20'
                }],
                'federal': [{
                    'title': 'Federal Education Grant',
                    'score': 88,
                    'opportunity_number': 'ED-2025-002'
                }]
            }
            mock_service.return_value = mock_instance
            
            # Test matching endpoint (used by dashboard)
            response = client.get('/api/matching?orgId=1&limit=10')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify award norms available for dashboard
            context = data['context']
            assert context['median_award'] == 185000
            assert context['award_count'] == 47
            assert len(context['recent_funders']) == 3
            
            # Verify Open Calls for dashboard display
            assert len(data['news']) == 1
            assert data['news'][0]['score'] == 82
            
            # Verify High Matching Federal for dashboard
            assert len(data['federal']) == 1
            assert data['federal'][0]['score'] == 88


class TestEndToEndSmoke:
    """Comprehensive smoke tests for all components"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    def test_api_endpoints_accessible(self, client):
        """Test all key endpoints are accessible"""
        endpoints = [
            ('/api/matching?orgId=1', 200),
            ('/api/matching/detail/grants-gov/TEST-123', 200),
            ('/api/profile', 200),
            ('/api/grants', 200)
        ]
        
        for endpoint, expected_status in endpoints:
            response = client.get(endpoint)
            assert response.status_code == expected_status, f"Endpoint {endpoint} failed"
    
    def test_api_response_structure(self, client):
        """Test API responses have correct structure"""
        # Test matching API structure
        response = client.get('/api/matching?orgId=1')
        assert response.status_code == 200
        
        data = response.get_json()
        required_keys = ['tokens', 'context', 'news', 'federal']
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"
        
        # Test context structure
        context = data['context']
        context_keys = ['award_count', 'median_award', 'recent_funders']
        for key in context_keys:
            assert key in context, f"Missing context key: {key}"
    
    def test_data_quality_validation(self, client):
        """Test data quality requirements"""
        response = client.get('/api/matching?orgId=1')
        data = response.get_json()
        context = data['context']
        
        # Award count must be non-negative integer
        assert isinstance(context['award_count'], int)
        assert context['award_count'] >= 0
        
        # Median award must be None or number (no zeros unless API returned zeros)
        median = context['median_award']
        assert median is None or isinstance(median, (int, float))
        
        # Recent funders must be list of 0-5 strings
        funders = context['recent_funders']
        assert isinstance(funders, list)
        assert len(funders) <= 5
        assert all(isinstance(f, str) for f in funders)
    
    def test_news_quality_filters(self, client):
        """Test news filtering requirements"""
        with patch('app.services.candid_client.NewsClient') as mock_news:
            # Mock news response with various types
            mock_client = Mock()
            mock_client.search.return_value = [
                {'rfp_mentioned': True, 'title': 'RFP Announcement', 'content': 'Grant opportunity available'},
                {'rfp_mentioned': False, 'grant_mentioned': True, 'content': 'Applications are being accepted', 'title': 'Grant Available'},
                {'rfp_mentioned': False, 'staff_change_mentioned': True, 'content': 'New CEO appointed', 'title': 'Leadership Change'},
                {'rfp_mentioned': False, 'grant_mentioned': True, 'content': 'Applications due soon', 'title': 'Grant Deadline'}
            ]
            mock_news.return_value = mock_client
            
            response = client.get('/api/matching?orgId=1')
            data = response.get_json()
            
            # Should filter properly - RFP items and grant+action words, exclude pure staff changes
            news_items = data.get('news', [])
            
            for item in news_items:
                # Each item should either have RFP mentioned OR contain action words
                if not item.get('rfp_mentioned', False):
                    content_lower = (item.get('content', '') + ' ' + item.get('title', '')).lower()
                    action_words = ['apply', 'application', 'accepting', 'deadline']
                    assert any(word in content_lower for word in action_words), f"Item lacks RFP or action words: {item}"


if __name__ == '__main__':
    pytest.main([__file__])