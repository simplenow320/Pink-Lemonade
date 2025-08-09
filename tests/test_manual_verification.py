#!/usr/bin/env python3
"""
Manual verification tests for stats service and discovery integration.
Run with: python tests/test_manual_verification.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from datetime import date, timedelta
from app import create_app, db
from app.models import Org, Grant
from app.services.stats_service import get_dashboard_stats

def test_stats_service():
    """Test that dashboard stats calculation works correctly"""
    print("Testing stats service...")
    
    # Set test environment
    os.environ["APP_DATA_MODE"] = "LIVE"
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Create test org
        org = Org(name="Test Org")
        db.session.add(org)
        db.session.commit()
        
        # Create test grants
        g1 = Grant(
            org_id=org.id, 
            title="Grant A", 
            funder="Funder X", 
            deadline=date.today() + timedelta(days=5)
        )
        g2 = Grant(
            org_id=org.id, 
            title="Grant B", 
            funder="Funder Y", 
            status="submitted"
        )
        g3 = Grant(
            org_id=org.id, 
            title="Grant C", 
            funder="Funder Z"
        )
        
        db.session.add_all([g1, g2, g3])
        db.session.commit()
        
        # Test stats calculation
        stats = get_dashboard_stats(org.id)
        
        assert stats["total"] == 3, f"Expected 3 total grants, got {stats['total']}"
        assert stats["submitted"] == 1, f"Expected 1 submitted grant, got {stats['submitted']}"
        assert isinstance(stats["due_this_month"], int), f"due_this_month should be int, got {type(stats['due_this_month'])}"
        
        print("✓ Stats service working correctly")
        print(f"  - Total: {stats['total']}")
        print(f"  - Submitted: {stats['submitted']}")
        print(f"  - Due this month: {stats['due_this_month']}")
        
        db.session.remove()
        db.drop_all()

def test_discovery_api():
    """Test that discovery API endpoint responds correctly"""
    print("\nTesting discovery API endpoint...")
    
    app = create_app()
    client = app.test_client()
    
    # Test POST to /api/scrape/run-now
    response = client.post('/api/scrape/run-now', 
                          json={"orgId": 1}, 
                          content_type='application/json')
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.get_json()
    assert "upserted" in data, f"Expected 'upserted' in response, got {data}"
    assert "mode" in data, f"Expected 'mode' in response, got {data}"
    
    print("✓ Discovery API endpoint working correctly")
    print(f"  - Status: {response.status_code}")
    print(f"  - Response: {data}")

if __name__ == "__main__":
    print("=== Manual Verification Tests ===")
    try:
        test_stats_service()
        test_discovery_api()
        print("\n✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)