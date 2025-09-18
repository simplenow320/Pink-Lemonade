"""
Test configuration file for pytest
"""

import pytest
import os
import json
from datetime import datetime, date
from typing import Dict, Any, List, Generator
from unittest.mock import Mock, patch

from app import create_app, db
from app.models.grant import Grant
from app.models.organization import Organization
from app.models.narrative import Narrative
from app.models.scraper import ScraperSource, ScraperHistory
from app.services.apiManager import APIManager, CircuitBreaker, RateLimiter, CacheManager
from app.config.apiConfig import APIConfig

# Import our test fixtures
from .fixtures.api_responses import *
from .fixtures.mock_server import MockAPIServer, CircuitBreakerTestHelper, RateLimitTestHelper, CacheTestHelper

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create the app with test config
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SCHEDULER_ENABLED': False,  # Disable scheduler for tests
    })

    # Set up application context
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        # Clean up after test
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def sample_grant_data() -> Dict[str, Any]:
    """Sample grant data for testing."""
    return {
        'title': 'Test Grant',
        'funder': 'Test Foundation',
        'description': 'This is a test grant description',
        'amount': 10000.0,
        'due_date': date.today().isoformat(),
        'eligibility': 'Nonprofit organizations',
        'website': 'https://example.com/grant',
        'status': 'Not Started',
        'focus_areas': ['education', 'health'],
        'contact_info': 'grants@example.com'
    }

@pytest.fixture
def sample_organization_data() -> Dict[str, Any]:
    """Sample organization data for testing."""
    return {
        'name': 'Test Organization',
        'mission': 'Advancing education and health in communities',
        'website': 'https://testorg.org',
        'location': {'city': 'Test City', 'state': 'Test State', 'zip': '12345'},
        'founding_year': 2010,
        'team': [
            {'name': 'Jane Doe', 'role': 'Executive Director'},
            {'name': 'John Smith', 'role': 'Program Director'}
        ],
        'focus_areas': ['education', 'health'],
        'keywords': ['youth', 'community', 'education'],
        'past_programs': [
            {
                'name': 'Summer Learning Program',
                'year': 2023,
                'description': 'Educational program for underserved youth',
                'outcomes': 'Served 200 students with 90% improvement in literacy'
            }
        ],
        'financials': {
            'annual_budget': 500000,
            'funding_sources': ['donations', 'grants']
        },
        'case_for_support': 'Our organization has a proven track record of success...'
    }

@pytest.fixture
def db_grant(app, sample_grant_data) -> Grant:
    """Create a grant in the database for testing."""
    due_date = datetime.fromisoformat(sample_grant_data['due_date']).date() if isinstance(sample_grant_data['due_date'], str) else sample_grant_data['due_date']
    
    grant = Grant(
        title=sample_grant_data['title'],
        funder=sample_grant_data['funder'],
        description=sample_grant_data['description'],
        amount=sample_grant_data['amount'],
        due_date=due_date,
        eligibility=sample_grant_data['eligibility'],
        website=sample_grant_data['website'],
        status=sample_grant_data['status'],
        focus_areas=sample_grant_data['focus_areas'],
        contact_info=sample_grant_data['contact_info']
    )
    
    db.session.add(grant)
    db.session.commit()
    
    return grant

@pytest.fixture
def db_organization(app, sample_organization_data) -> Organization:
    """Create an organization in the database for testing."""
    org = Organization(
        name=sample_organization_data['name'],
        mission=sample_organization_data['mission'],
        website=sample_organization_data['website'],
        location=sample_organization_data['location'],
        founding_year=sample_organization_data['founding_year'],
        team=sample_organization_data['team'],
        focus_areas=sample_organization_data['focus_areas'],
        keywords=sample_organization_data['keywords'],
        past_programs=sample_organization_data['past_programs'],
        financials=sample_organization_data['financials'],
        case_for_support=sample_organization_data['case_for_support']
    )
    
    db.session.add(org)
    db.session.commit()
    
    return org

@pytest.fixture
def db_narrative(app, db_grant) -> Narrative:
    """Create a narrative in the database for testing."""
    narrative = Narrative(
        grant_id=db_grant.id,
        content="This is a sample grant narrative for testing purposes."
    )
    
    db.session.add(narrative)
    db.session.commit()
    
    return narrative

@pytest.fixture
def db_scraper_source(app) -> ScraperSource:
    """Create a scraper source in the database for testing."""
    source = ScraperSource(
        name="Test Source",
        url="https://example.com/grants",
        selector_config={
            "title": ".grant-title",
            "description": ".grant-description"
        },
        is_active=True
    )
    
    db.session.add(source)
    db.session.commit()
    
    return source

@pytest.fixture
def mock_openai_response() -> Dict[str, Any]:
    """Mock OpenAI API response for testing."""
    return {
        "id": "chatcmpl-123456789",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-4o",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "title": "Test Grant",
                        "funder": "Test Foundation",
                        "description": "This is a test grant description",
                        "amount": 10000.0,
                        "due_date": "2025-12-31",
                        "eligibility": "Nonprofit organizations",
                        "website": "https://example.com/grant",
                        "focus_areas": ["education", "health"],
                        "contact_info": "grants@example.com"
                    })
                },
                "finish_reason": "stop",
                "index": 0
            }
        ]
    }

# API Testing Fixtures

@pytest.fixture
def clean_environment():
    """Clean environment variables for testing credential scenarios"""
    original_env = {}
    # List of all API-related environment variables
    api_env_vars = [
        'SAM_GOV_API_KEY', 'SAM_API_KEY', 'SAMGOV_KEY',
        'MICHIGAN_SOCRATA_API_KEY', 'SOCRATA_APP_TOKEN', 'MICHIGAN_API_KEY',
        'ZYTE_API_KEY', 'SCRAPINGHUB_API_KEY', 'ZYTE_KEY',
        'GOVINFO_API_KEY', 'GOVINFO_KEY',
        'CANDID_API_KEY', 'FDO_API_KEY', 'GRANTWATCH_API_KEY',
        'HHS_GRANTS_API_KEY', 'ED_GRANTS_API_KEY', 'NSF_API_KEY'
    ]
    
    # Save original values and clear
    for var in api_env_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    # Restore original values
    for var, value in original_env.items():
        os.environ[var] = value

@pytest.fixture
def mock_api_server():
    """Mock API server for testing HTTP requests"""
    server = MockAPIServer()
    with patch('app.services.apiManager.requests.request', side_effect=server.mock_request):
        yield server
    server.reset()

@pytest.fixture
def api_manager():
    """APIManager instance for testing"""
    return APIManager()

@pytest.fixture
def api_config():
    """APIConfig instance for testing"""
    return APIConfig()

@pytest.fixture
def circuit_breaker_helper():
    """Helper for circuit breaker testing"""
    return CircuitBreakerTestHelper()

@pytest.fixture
def rate_limit_helper():
    """Helper for rate limit testing"""
    return RateLimitTestHelper()

@pytest.fixture
def cache_helper():
    """Helper for cache testing"""
    return CacheTestHelper()

@pytest.fixture
def sample_circuit_breaker():
    """Sample circuit breaker for testing"""
    return CircuitBreaker("test_source", failure_threshold=3, cooldown_minutes=5)

@pytest.fixture
def sample_rate_limiter():
    """Sample rate limiter for testing"""
    return RateLimiter()

@pytest.fixture
def sample_cache_manager():
    """Sample cache manager for testing"""
    return CacheManager()

@pytest.fixture
def mock_successful_response():
    """Mock successful API response"""
    response = Mock()
    response.status_code = 200
    response.headers = {'Content-Type': 'application/json'}
    response.json.return_value = get_mock_response("grants_gov", "success")
    response.text = json.dumps(get_mock_response("grants_gov", "success"))
    return response

@pytest.fixture
def mock_error_response():
    """Mock error API response"""
    response = Mock()
    response.status_code = 401
    response.headers = {'Content-Type': 'application/json'}
    response.json.return_value = {"error": "Unauthorized", "message": "Invalid API key"}
    response.text = json.dumps({"error": "Unauthorized", "message": "Invalid API key"})
    return response

@pytest.fixture
def mock_rate_limit_response():
    """Mock rate limit error response"""
    response = Mock()
    response.status_code = 429
    response.headers = {
        'Content-Type': 'application/json',
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '0',
        'X-RateLimit-Reset': '3600'
    }
    response.json.return_value = {"error": "Rate limit exceeded", "message": "Too many requests"}
    response.text = json.dumps({"error": "Rate limit exceeded", "message": "Too many requests"})
    return response

@pytest.fixture(params=[
    'grants_gov', 'federal_register', 'govinfo',
    'sam_gov_opportunities', 'foundation_directory', 'candid'
])
def api_source(request):
    """Parametrized fixture for testing different API sources"""
    return request.param

@pytest.fixture(params=[
    ('missing_credentials', None),
    ('invalid_credentials', 'invalid-key-123'),
    ('valid_credentials', 'valid-test-key-456')
])
def credential_scenario(request):
    """Parametrized fixture for testing different credential scenarios"""
    scenario_type, credential_value = request.param
    return {
        'type': scenario_type,
        'value': credential_value,
        'description': f"Testing {scenario_type.replace('_', ' ')}"
    }