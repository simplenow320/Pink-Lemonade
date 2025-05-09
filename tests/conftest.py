"""
Test configuration file for pytest
"""

import pytest
import os
import json
from datetime import datetime, date
from typing import Dict, Any, List, Generator

from app import create_app, db
from app.models.grant import Grant
from app.models.organization import Organization
from app.models.narrative import Narrative
from app.models.scraper import ScraperSource, ScraperHistory

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