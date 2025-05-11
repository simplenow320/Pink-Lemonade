"""
Tests for the Grants API endpoints.
"""

import json
from datetime import date, timedelta
import pytest
from app.models.grant import Grant
from app.models.organization import Organization


def test_get_grants_success(client, db_grant):
    """Test successful grants retrieval."""
    # Make a request to the endpoint
    response = client.get('/api/grants')
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the grant is in the response
    assert len(data) == 1
    assert data[0]['id'] == db_grant.id
    assert data[0]['title'] == db_grant.title
    assert data[0]['funder'] == db_grant.funder


def test_get_grants_filter_by_status(client, app, db_grant):
    """Test grants filtering by status."""
    # Create another grant with a different status
    with app.app_context():
        new_grant = Grant(
            title="Another Test Grant",
            funder="Another Foundation",
            description="This is another test grant",
            amount=20000.0,
            due_date=date.today() + timedelta(days=30),
            status="In Progress"
        )
        app.db.session.add(new_grant)
        app.db.session.commit()
    
    # Test filtering by the original grant's status
    response = client.get(f'/api/grants?status={db_grant.status}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['id'] == db_grant.id
    
    # Test filtering by the new grant's status
    response = client.get('/api/grants?status=In Progress')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['title'] == "Another Test Grant"


def test_get_grants_sorting(client, app, db_grant):
    """Test grants sorting."""
    # Create another grant with a later due date
    with app.app_context():
        new_grant = Grant(
            title="Future Grant",
            funder="Future Foundation",
            description="This is a future grant",
            amount=30000.0,
            due_date=date.today() + timedelta(days=60),
            status="Not Started"
        )
        app.db.session.add(new_grant)
        app.db.session.commit()
    
    # Test sorting by due_date ascending (default)
    response = client.get('/api/grants')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['title'] == db_grant.title  # Earlier due date first
    
    # Test sorting by due_date descending
    response = client.get('/api/grants?sort_by=due_date&sort_dir=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['title'] == "Future Grant"  # Later due date first


def test_get_grants_invalid_sort(client):
    """Test grants with invalid sort parameter."""
    response = client.get('/api/grants?sort_by=invalid_field')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid sort_by parameter' in data['error']
    
    # Test invalid sort direction
    response = client.get('/api/grants?sort_dir=invalid')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid sort_dir parameter' in data['error']


def test_add_grant_success(client):
    """Test successful grant creation."""
    # Create test grant data
    grant_data = {
        'title': 'New Test Grant',
        'funder': 'New Test Foundation',
        'description': 'This is a test grant description for a new grant',
        'amount': 15000.0,
        'due_date': date.today().isoformat(),
        'eligibility': 'All nonprofit organizations',
        'website': 'https://example.com/new-grant',
        'focus_areas': ['education', 'technology'],
        'contact_info': 'newtestgrant@example.com'
    }
    
    # Make a request to create the grant
    response = client.post(
        '/api/grants',
        data=json.dumps(grant_data),
        content_type='application/json'
    )
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the response has the expected fields
    assert 'id' in data
    assert 'title' in data
    assert 'funder' in data
    assert 'description' in data
    assert 'amount' in data
    assert 'due_date' in data
    assert 'eligibility' in data
    assert 'website' in data
    assert 'focus_areas' in data
    assert 'contact_info' in data
    
    # Check that the values match what we sent
    assert data['title'] == grant_data['title']
    assert data['funder'] == grant_data['funder']
    assert data['description'] == grant_data['description']
    assert data['amount'] == grant_data['amount']
    assert data['eligibility'] == grant_data['eligibility']
    assert data['website'] == grant_data['website']
    assert data['focus_areas'] == grant_data['focus_areas']
    assert data['contact_info'] == grant_data['contact_info']


def test_add_grant_missing_required_fields(client):
    """Test grant creation with missing required fields."""
    # Create incomplete test grant data (missing required 'funder')
    incomplete_grant_data = {
        'title': 'Incomplete Test Grant',
        # Missing 'funder' field which is required
        'description': 'This is a test with missing fields'
    }
    
    # Make a request to create the grant
    response = client.post(
        '/api/grants',
        data=json.dumps(incomplete_grant_data),
        content_type='application/json'
    )
    
    # Check that the response indicates a bad request
    assert response.status_code == 400
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check error message
    assert 'error' in data
    assert 'required' in data['error'].lower()


def test_update_grant_status_success(client, db_grant):
    """Test successful grant status update."""
    # New status data
    status_data = {
        'status': 'In Progress'
    }
    
    # Make a request to update the grant status
    response = client.put(
        f'/api/grants/{db_grant.id}/status',
        data=json.dumps(status_data),
        content_type='application/json'
    )
    
    # Check that the response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the grant status was updated
    assert 'id' in data
    assert 'status' in data
    assert data['id'] == db_grant.id
    assert data['status'] == status_data['status']


def test_update_grant_status_invalid_status(client, db_grant):
    """Test grant status update with invalid status value."""
    # Invalid status data
    invalid_status_data = {
        'status': 'Invalid Status'
    }
    
    # Make a request to update the grant status
    response = client.put(
        f'/api/grants/{db_grant.id}/status',
        data=json.dumps(invalid_status_data),
        content_type='application/json'
    )
    
    # Check that the response indicates a bad request
    assert response.status_code == 400
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check error message
    assert 'error' in data
    assert 'Invalid status' in data['error']


def test_update_grant_status_not_found(client):
    """Test grant status update for non-existent grant."""
    # Status data
    status_data = {
        'status': 'In Progress'
    }
    
    # Use a non-existent grant ID
    non_existent_id = 9999
    
    # Make a request to update the grant status
    response = client.put(
        f'/api/grants/{non_existent_id}/status',
        data=json.dumps(status_data),
        content_type='application/json'
    )
    
    # Check that the response indicates not found
    assert response.status_code == 404
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check error message
    assert 'error' in data
    assert 'not found' in data['error'].lower()