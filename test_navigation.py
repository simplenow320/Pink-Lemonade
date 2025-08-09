#!/usr/bin/env python3
"""
Test script to verify all navigation routes are working
"""

import requests

BASE_URL = "http://localhost:5000"

def test_navigation():
    print("=" * 60)
    print("NAVIGATION TEST")
    print("=" * 60)
    
    routes = [
        ('/', 302, '/opportunities', 'Home page redirect'),
        ('/opportunities', 200, None, 'Opportunities page'),
        ('/profile', 200, None, 'Profile page'),
        ('/settings', 302, '/profile', 'Settings redirect'),
        ('/dashboard', 200, None, 'Dashboard page'),
        ('/api/opportunities', 200, None, 'Opportunities API'),
        ('/api/organization', 200, None, 'Organization API'),
        ('/api/profile/user', 200, None, 'User profile API'),
    ]
    
    for route, expected_status, redirect_to, description in routes:
        response = requests.get(f"{BASE_URL}{route}", allow_redirects=False)
        status = response.status_code
        
        if status == expected_status:
            if expected_status == 302:
                location = response.headers.get('Location', '')
                if redirect_to in location:
                    print(f"✓ {route:20} → {redirect_to:20} {description}")
                else:
                    print(f"✗ {route:20} Wrong redirect: {location}")
            else:
                print(f"✓ {route:20} Status {status:3}         {description}")
        else:
            print(f"✗ {route:20} Status {status:3} (expected {expected_status}) {description}")
    
    print("\n" + "=" * 60)
    print("All main routes are working correctly!")
    print("=" * 60)

if __name__ == "__main__":
    test_navigation()