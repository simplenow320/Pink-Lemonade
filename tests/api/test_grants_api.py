"""
Tests for the Grants API endpoints.
"""

import json
from datetime import date, timedelta
import pytest
from app.models.grant import Grant


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