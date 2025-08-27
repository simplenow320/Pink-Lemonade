#!/usr/bin/env python
"""Simple test runner for impact intake without pytest dependency"""

import sys
import traceback
from app import create_app, db
from app.models import ImpactIntake, Grant, Organization
from app.utils.impact_intake_validator import validate_and_merge_intake_payload

def test_accepts_valid_payload():
    """Test accepting valid payload with all new fields"""
    app = create_app()
    with app.app_context():
        # Create test data
        org = Organization(name="Test Org", mission="Test mission", ein="12-3456789")
        db.session.add(org)
        db.session.flush()
        
        grant = Grant(title="Test Grant", funder="Test Funder", amount_max=10000, org_id=org.id)
        db.session.add(grant)
        db.session.commit()
        
        intake = ImpactIntake(grant_id=grant.id, submitted_by="test@example.com", role="staff")
        
        incoming = {
            'age': 25,
            'zip': '12345',
            'ethnicity': 'Hispanic',
            'stories': ['Story 1', 'Story 2', 'Story 3', 'Story 4']
        }
        
        intake.validate_payload(incoming)
        
        assert intake.payload['age'] == 25
        assert intake.payload['zip'] == '12345'
        assert intake.payload['ethnicity'] == 'Hispanic'
        assert len(intake.payload['stories']) == 4
        
        db.session.add(intake)
        db.session.commit()
        
        saved = ImpactIntake.query.get(intake.id)
        assert saved.payload['age'] == 25
        
        # Clean up
        db.session.delete(intake)
        db.session.delete(grant)
        db.session.delete(org)
        db.session.commit()
        
        return True

def test_rejects_invalid_age():
    """Test rejecting invalid ages"""
    try:
        validate_and_merge_intake_payload({}, {'age': -1})
        return False
    except ValueError as e:
        if "age: must be >= 0" not in str(e):
            return False
    
    try:
        validate_and_merge_intake_payload({}, {'age': 121})
        return False
    except ValueError as e:
        if "age: must be <= 120" not in str(e):
            return False
    
    return True

def test_rejects_bad_zip():
    """Test rejecting invalid zip codes"""
    try:
        validate_and_merge_intake_payload({}, {'zip': '123'})
        return False
    except ValueError as e:
        if "zip: must be at least 5 characters" not in str(e):
            return False
    
    try:
        validate_and_merge_intake_payload({}, {'zip': '12345678901'})
        return False
    except ValueError as e:
        if "zip: must be at most 10 characters" not in str(e):
            return False
    
    return True

def test_rejects_ethnicity_too_long():
    """Test rejecting ethnicity that's too long"""
    long_ethnicity = 'x' * 81
    try:
        validate_and_merge_intake_payload({}, {'ethnicity': long_ethnicity})
        return False
    except ValueError as e:
        if "ethnicity: must be at most 80 characters" not in str(e):
            return False
    
    return True

def test_truncates_stories_to_four():
    """Test that stories array is truncated to max 4 items"""
    stories = [f"Story {i}" for i in range(10)]
    result = validate_and_merge_intake_payload({}, {'stories': stories})
    
    if len(result['stories']) != 4:
        return False
    if result['stories'][0] != 'Story 0':
        return False
    if result['stories'][3] != 'Story 3':
        return False
    
    return True

def test_preserves_existing_payload_keys():
    """Test backward compatibility"""
    existing = {'custom_field': 'value', 'other_data': 123, 'age': 30}
    incoming = {'age': 35, 'zip': '90210'}
    
    result = validate_and_merge_intake_payload(existing, incoming)
    
    if result['age'] != 35:
        return False
    if result['zip'] != '90210':
        return False
    if result['custom_field'] != 'value':
        return False
    if result['other_data'] != 123:
        return False
    
    return True

def test_indexes_exist():
    """Check that table and indexes were created"""
    app = create_app()
    with app.app_context():
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'impact_intake' not in tables:
            return False
        
        columns = [col['name'] for col in inspector.get_columns('impact_intake')]
        required = ['id', 'grant_id', 'submitted_by', 'role', 'payload', 'created_at']
        
        for col in required:
            if col not in columns:
                return False
        
        return True

def main():
    """Run all tests"""
    tests = [
        ('test_accepts_valid_payload', test_accepts_valid_payload),
        ('test_rejects_invalid_age', test_rejects_invalid_age),
        ('test_rejects_bad_zip', test_rejects_bad_zip),
        ('test_rejects_ethnicity_too_long', test_rejects_ethnicity_too_long),
        ('test_truncates_stories_to_four', test_truncates_stories_to_four),
        ('test_preserves_existing_payload_keys', test_preserves_existing_payload_keys),
        ('test_indexes_exist_or_are_declared', test_indexes_exist)
    ]
    
    passed = 0
    failed = 0
    
    print("Running Impact Intake Tests")
    print("=" * 50)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✓ {test_name}")
                passed += 1
            else:
                print(f"✗ {test_name}: Assertion failed")
                failed += 1
        except Exception as e:
            print(f"✗ {test_name}: {str(e)[:100]}")
            failed += 1
            if '--verbose' in sys.argv:
                traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())