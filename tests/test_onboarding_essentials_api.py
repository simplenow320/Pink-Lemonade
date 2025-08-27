"""
Tests for Candid Essentials integration in onboarding API
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from app.api.onboarding import onboarding_bp
from app.models import db, Organization


def create_test_app():
    """Create a test Flask app"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    app.register_blueprint(onboarding_bp)
    
    with app.app_context():
        db.create_all()
    
    return app


class TestOnboardingEssentialsAPI:
    """Test Candid Essentials API endpoints"""
    
    def test_lookup_by_ein_returns_200_with_tokens(self):
        """Test lookup by EIN returns 200 with tokens when client returns a record"""
        app = create_test_app()
        
        with app.test_client() as client:
            with patch('app.api.onboarding.search_by_ein') as mock_search:
                # Mock successful EIN search
                mock_record = {
                    "ein": "12-3456789",
                    "name": "Test Foundation",
                    "mission": "To help communities",
                    "website": "https://test.org"
                }
                mock_search.return_value = mock_record
                
                with patch('app.api.onboarding.extract_tokens') as mock_extract:
                    mock_tokens = {
                        "pcs_subject_codes": ["EDU", "HEALTH"],
                        "pcs_population_codes": ["CHILD"],
                        "locations": ["New York, NY"],
                        "mission": "To help communities",
                        "website": "https://test.org"
                    }
                    mock_extract.return_value = mock_tokens
                    
                    # Test with EIN query
                    response = client.get('/api/onboarding/essentials/lookup?query=12-3456789')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert "record" in data
                    assert "tokens" in data
                    assert data["record"]["ein"] == "12-3456789"
                    assert data["tokens"]["pcs_subject_codes"] == ["EDU", "HEALTH"]
                    
                    # Verify search_by_ein was called
                    mock_search.assert_called_once_with("12-3456789")
    
    def test_lookup_by_name_returns_404_when_no_match(self):
        """Test lookup by name returns 404 when no match"""
        app = create_test_app()
        
        with app.test_client() as client:
            with patch('app.api.onboarding.search_by_name') as mock_search:
                # Mock no results
                mock_search.return_value = None
                
                response = client.get('/api/onboarding/essentials/lookup?query=Nonexistent%20Org')
                
                assert response.status_code == 404
                data = json.loads(response.data)
                assert data["error"] == "not_found"
                
                # Verify search_by_name was called (not EIN)
                mock_search.assert_called_once_with("Nonexistent Org")
    
    def test_apply_only_copies_selected_fields(self):
        """Test apply only copies fields where apply[field]==true and leaves others intact"""
        app = create_test_app()
        
        with app.test_client() as client:
            with app.app_context():
                # Create an organization with existing data
                org = Organization(
                    id=1,
                    name="Existing Org",
                    mission="Existing mission",
                    website="https://existing.org"
                )
                db.session.add(org)
                db.session.commit()
                
                # Mock extract_tokens
                with patch('app.api.onboarding.extract_tokens') as mock_extract:
                    mock_extract.return_value = {
                        "pcs_subject_codes": ["EDU", "ARTS"],
                        "pcs_population_codes": ["SENIOR"],
                        "locations": ["Boston, MA"],
                        "mission": "New mission from Candid",
                        "website": "https://candid.org"
                    }
                    
                    # Apply only specific fields
                    payload = {
                        "org_id": 1,
                        "record": {
                            "ein": "98-7654321",
                            "name": "New Name From Candid"
                        },
                        "apply": {
                            "org_name": False,  # Don't overwrite name
                            "ein": True,  # Apply EIN
                            "website": False,  # Don't overwrite website
                            "mission": False,  # Don't overwrite mission
                            "pcs_subject_codes": True,  # Apply PCS codes
                            "pcs_population_codes": True,  # Apply population codes
                            "service_locations": False  # Don't apply locations
                        }
                    }
                    
                    response = client.post(
                        '/api/onboarding/essentials/apply',
                        data=json.dumps(payload),
                        content_type='application/json'
                    )
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data["saved"] is True
                    assert "ein" in data["appliedFields"]
                    assert "pcs_subject_codes" in data["appliedFields"]
                    assert "pcs_population_codes" in data["appliedFields"]
                    assert "org_name" not in data["appliedFields"]
                    assert "website" not in data["appliedFields"]
                    assert "mission" not in data["appliedFields"]
                    assert "service_locations" not in data["appliedFields"]
                    
                    # Check database - original values should be preserved
                    org = Organization.query.get(1)
                    assert org.name == "Existing Org"  # Not overwritten
                    assert org.ein == "98-7654321"  # Applied
                    assert org.website == "https://existing.org"  # Not overwritten
                    assert org.mission == "Existing mission"  # Not overwritten
                    assert org.pcs_subject_codes == ["EDU", "ARTS"]  # Applied
                    assert org.pcs_population_codes == ["SENIOR"]  # Applied
                    assert org.service_locations is None  # Not applied
    
    def test_lookup_missing_query_returns_400(self):
        """Test lookup without query parameter returns 400"""
        app = create_test_app()
        
        with app.test_client() as client:
            response = client.get('/api/onboarding/essentials/lookup')
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data
    
    def test_apply_missing_org_id_returns_400(self):
        """Test apply without org_id returns 400"""
        app = create_test_app()
        
        with app.test_client() as client:
            payload = {
                "record": {},
                "apply": {}
            }
            
            response = client.post(
                '/api/onboarding/essentials/apply',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data
            assert "org_id" in data["error"]
    
    def test_apply_creates_org_if_not_exists(self):
        """Test apply creates organization if it doesn't exist"""
        app = create_test_app()
        
        with app.test_client() as client:
            with app.app_context():
                with patch('app.api.onboarding.extract_tokens') as mock_extract:
                    mock_extract.return_value = {
                        "mission": "New org mission",
                        "website": "https://new.org",
                        "pcs_subject_codes": [],
                        "pcs_population_codes": [],
                        "locations": []
                    }
                    
                    payload = {
                        "org_id": 999,
                        "record": {"name": "Brand New Org"},
                        "apply": {
                            "org_name": True,
                            "mission": True
                        }
                    }
                    
                    response = client.post(
                        '/api/onboarding/essentials/apply',
                        data=json.dumps(payload),
                        content_type='application/json'
                    )
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data["saved"] is True
                    
                    # Check org was created
                    org = Organization.query.get(999)
                    assert org is not None
                    assert org.name == "Brand New Org"
                    assert org.mission == "New org mission"


# Test runner
def run_tests():
    """Run all tests and report results"""
    import sys
    passed = 0
    failed = 0
    
    test_instance = TestOnboardingEssentialsAPI()
    test_methods = [
        test_instance.test_lookup_by_ein_returns_200_with_tokens,
        test_instance.test_lookup_by_name_returns_404_when_no_match,
        test_instance.test_apply_only_copies_selected_fields,
        test_instance.test_lookup_missing_query_returns_400,
        test_instance.test_apply_missing_org_id_returns_400,
        test_instance.test_apply_creates_org_if_not_exists
    ]
    
    for test_method in test_methods:
        try:
            test_method()
            print(f"✓ {test_method.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_method.__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print(f"{'='*50}")
    
    return passed, failed


if __name__ == "__main__":
    import sys
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)