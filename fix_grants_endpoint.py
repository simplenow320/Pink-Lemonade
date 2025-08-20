#!/usr/bin/env python
"""Fix grants endpoint to return proper data"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

with app.app_context():
    with app.test_client() as client:
        # Test grants endpoint
        print("Testing /api/grants endpoint...")
        response = client.get('/api/grants')
        print(f"Status: {response.status_code}")
        print(f"Content Type: {response.content_type}")
        
        # Check if it's a redirect
        if response.status_code in [301, 302, 303, 307, 308]:
            print(f"Redirect to: {response.headers.get('Location')}")
            # Follow redirect
            response = client.get(response.headers.get('Location'))
            print(f"After redirect - Status: {response.status_code}")
            
        # Try to parse response
        try:
            data = response.get_json()
            print(f"JSON Response: {data}")
        except:
            print(f"Raw Response: {response.data[:500]}")
            
print("\nChecking grant model...")
from app.models import Grant
print(f"Grant model has to_dict: {hasattr(Grant, 'to_dict')}")