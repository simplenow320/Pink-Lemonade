#!/usr/bin/env python
"""
Simple test script for scraper functionality
Runs without pytest to verify core scraper behavior
"""

import os
import sys
import json

# Set up path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment for testing
os.environ["APP_DATA_MODE"] = "DEMO"  # Test in DEMO mode
os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:///test.db")

from app import create_app, db
from app.models import Org, Watchlist, Grant
from app.services.scraper_service import run_now_for_org, normalize_grant_record, upsert_grant

def test_scraper_api():
    """Test the scraper API endpoint"""
    app = create_app()
    
    with app.app_context():
        # Reset database
        db.drop_all()
        db.create_all()
        
        # Create test org and watchlist
        org = Org(name="Test Org", mission="Testing scraper")
        db.session.add(org)
        db.session.commit()
        
        watchlist = Watchlist(org_id=org.id, city="Detroit")
        db.session.add(watchlist)
        db.session.commit()
        
        print(f"✓ Created test org (ID: {org.id}) and watchlist")
        
        # Test the API endpoint
        client = app.test_client()
        
        # Test with missing orgId
        response = client.post('/api/scrape/run-now', 
                              json={},
                              content_type='application/json')
        assert response.status_code == 400
        print("✓ API correctly rejects request without orgId")
        
        # Test with valid orgId in DEMO mode
        response = client.post('/api/scrape/run-now',
                              json={"orgId": org.id, "query": "education"},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data["mode"] == "DEMO"
        assert data["upserted"] == 0  # DEMO mode returns empty
        print(f"✓ API returns correct DEMO response: {data}")
        
        # Test direct upsert functionality
        test_record = {
            "title": "Test Grant",
            "funder": "Test Foundation",
            "link": "https://example.com",
            "amount_min": 10000,
            "amount_max": 50000,
            "deadline": "2025-12-31",
            "geography": "Michigan",
            "eligibility": "Nonprofits",
            "source_name": "Manual Test",
            "source_url": "https://example.com"
        }
        
        normalized = normalize_grant_record(test_record)
        grant = upsert_grant(normalized, org_id=org.id)
        assert grant is not None
        assert grant.title == "Test Grant"
        print(f"✓ Direct upsert created grant: {grant.title}")
        
        # Test deduplication
        grant2 = upsert_grant(normalized, org_id=org.id)
        assert grant2.id == grant.id  # Should be same record
        print("✓ Deduplication works (same grant not duplicated)")
        
        # Check grant count
        count = Grant.query.filter_by(org_id=org.id).count()
        assert count == 1
        print(f"✓ Total grants in database: {count}")
        
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_scraper_api()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)