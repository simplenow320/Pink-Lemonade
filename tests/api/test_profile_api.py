"""
Tests for the Profile API endpoints.
"""

import json
import os
import pytest


def test_get_profile_success(client, monkeypatch):
    """Test successful profile retrieval."""
    # Mock profile data
    test_profile = {
        "mission": "Test mission statement",
        "focus_areas": ["education", "health"],
        "funding_priorities": ["youth programs", "community development"]
    }
    
    # Mock os.path.exists to return True
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    
    # Mock open to return our test profile
    mock_file = pytest.MockFixture()
    mock_file.read.return_value = json.dumps(test_profile)
    
    monkeypatch.setattr("builtins.open", lambda path, mode: mock_file)
    monkeypatch.setattr(json, "load", lambda f: test_profile)
    
    # Make a request to the endpoint
    response = client.get('/api/profile')
    
    # Check response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the profile data is correct
    assert "mission" in data
    assert "focus_areas" in data
    assert "funding_priorities" in data
    assert data["mission"] == test_profile["mission"]
    assert data["focus_areas"] == test_profile["focus_areas"]
    assert data["funding_priorities"] == test_profile["funding_priorities"]


def test_get_profile_no_file(client, monkeypatch):
    """Test profile retrieval when file doesn't exist."""
    # Mock os.path.exists to return False
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    
    # Make a request to the endpoint
    response = client.get('/api/profile')
    
    # Check response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that empty profile is returned
    assert "mission" in data
    assert "focus_areas" in data
    assert "funding_priorities" in data
    assert data["mission"] == ""
    assert data["focus_areas"] == []
    assert data["funding_priorities"] == []


def test_update_profile_success(client, monkeypatch):
    """Test successful profile update."""
    # Test profile data to update
    updated_profile = {
        "mission": "Updated mission statement",
        "focus_areas": ["education", "environment"],
        "funding_priorities": ["innovation", "sustainability"]
    }
    
    # Mock file writing
    mock_file = pytest.MockFixture()
    monkeypatch.setattr("builtins.open", lambda path, mode: mock_file)
    monkeypatch.setattr(json, "dump", lambda data, f, indent: None)
    
    # Make a request to update the profile
    response = client.post(
        '/api/profile',
        data=json.dumps(updated_profile),
        content_type='application/json'
    )
    
    # Check response is successful
    assert response.status_code == 200
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that the updated profile is returned
    assert "mission" in data
    assert "focus_areas" in data
    assert "funding_priorities" in data
    assert data["mission"] == updated_profile["mission"]
    assert data["focus_areas"] == updated_profile["focus_areas"]
    assert data["funding_priorities"] == updated_profile["funding_priorities"]


def test_update_profile_missing_fields(client):
    """Test profile update with missing required fields."""
    # Incomplete profile data
    incomplete_profile = {
        "mission": "Incomplete mission statement"
        # Missing focus_areas and funding_priorities
    }
    
    # Make a request to update the profile
    response = client.post(
        '/api/profile',
        data=json.dumps(incomplete_profile),
        content_type='application/json'
    )
    
    # Check response indicates bad request
    assert response.status_code == 400
    
    # Parse the JSON response
    data = json.loads(response.data)
    
    # Check that error message indicates missing fields
    assert "error" in data
    assert "Missing required field" in data["error"]