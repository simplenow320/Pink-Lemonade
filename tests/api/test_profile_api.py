"""
Tests for the Organization API endpoints.
"""

import json
import pytest
from app.models.organization import Organization


def test_get_organization_success(client, db_organization):
    """Test successful organization retrieval."""
    # Make a request to the endpoint
    response = client.get('/api/organization')
    
    # Check response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the organization data is correct
    assert 'id' in data
    assert 'name' in data
    assert 'mission' in data
    assert 'focus_areas' in data
    assert data['id'] == db_organization.id
    assert data['name'] == db_organization.name
    assert data['mission'] == db_organization.mission
    assert data['focus_areas'] == db_organization.focus_areas


def test_get_organization_not_found(client, app):
    """Test organization retrieval when not found."""
    # Ensure no organization exists
    with app.app_context():
        Organization.query.delete()
        db.session.commit()
    
    # Make a request to the endpoint
    response = client.get('/api/organization')
    
    # Check response indicates not found
    assert response.status_code == 404
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check error message
    assert 'error' in data
    assert 'not found' in data['error'].lower()


def test_update_organization_success(client, db_organization):
    """Test successful organization update."""
    # Organization data to update
    updated_org = {
        'name': 'Updated Organization Name',
        'mission': 'Updated mission statement',
        'focus_areas': ['education', 'environment', 'technology'],
        'website': 'https://updated-org.org'
    }
    
    # Make a request to update the organization
    response = client.put(
        '/api/organization',
        data=json.dumps(updated_org),
        content_type='application/json'
    )
    
    # Check response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the updated organization data is returned
    assert 'id' in data
    assert 'name' in data
    assert 'mission' in data
    assert 'focus_areas' in data
    assert 'website' in data
    assert data['id'] == db_organization.id
    assert data['name'] == updated_org['name']
    assert data['mission'] == updated_org['mission']
    assert data['focus_areas'] == updated_org['focus_areas']
    assert data['website'] == updated_org['website']


def test_update_organization_create_new(client, app):
    """Test organization update creating a new organization when none exists."""
    # Ensure no organization exists
    with app.app_context():
        Organization.query.delete()
        db.session.commit()
    
    # Organization data to create
    new_org = {
        'name': 'New Organization',
        'mission': 'New mission statement',
        'focus_areas': ['education', 'health'],
        'website': 'https://new-org.org'
    }
    
    # Make a request to create the organization
    response = client.put(
        '/api/organization',
        data=json.dumps(new_org),
        content_type='application/json'
    )
    
    # Check response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the new organization data is returned
    assert 'id' in data
    assert 'name' in data
    assert 'mission' in data
    assert 'focus_areas' in data
    assert 'website' in data
    assert data['name'] == new_org['name']
    assert data['mission'] == new_org['mission']
    assert data['focus_areas'] == new_org['focus_areas']
    assert data['website'] == new_org['website']


def test_seed_organization_success(client, app):
    """Test seeding organization with sample data."""
    # Ensure no organization exists
    with app.app_context():
        Organization.query.delete()
        db.session.commit()
    
    # Make a request to seed the organization
    response = client.post('/api/organization/seed')
    
    # Check response is created
    assert response.status_code == 201
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the response has the expected structure
    assert 'message' in data
    assert 'data' in data
    assert 'id' in data['data']
    assert 'name' in data['data']
    assert 'mission' in data['data']
    assert 'focus_areas' in data['data']


def test_seed_organization_already_exists(client, db_organization):
    """Test seeding organization when one already exists."""
    # Make a request to seed the organization
    response = client.post('/api/organization/seed')
    
    # Check response indicates bad request
    assert response.status_code == 400
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check error message
    assert 'error' in data
    assert 'already exists' in data['error'].lower()