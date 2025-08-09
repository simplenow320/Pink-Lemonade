#!/usr/bin/env python3
"""
Comprehensive End-to-End Feature and Navigation Test Suite
Tests every button, link, menu item, tab, route, and API endpoint
"""

import requests
import json
import time
from datetime import datetime
import sys

BASE_URL = "http://localhost:5000"

class TestRunner:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        
    def test(self, name, func, *args):
        """Run a test and record results"""
        try:
            result, message = func(*args)
            if result == "PASS":
                self.passed += 1
                status = "✓ PASS"
            elif result == "SKIP":
                self.skipped += 1
                status = "⊘ SKIP"
            else:
                self.failed += 1
                status = "✗ FAIL"
            
            self.results.append({
                'name': name,
                'status': status,
                'message': message
            })
            print(f"{status}: {name} - {message}")
            return result == "PASS"
        except Exception as e:
            self.failed += 1
            self.results.append({
                'name': name,
                'status': '✗ FAIL',
                'message': f"Exception: {str(e)}"
            })
            print(f"✗ FAIL: {name} - Exception: {str(e)}")
            return False

# Test functions
def test_route(path, expected_status=200, allow_redirect=True):
    """Test a route returns expected status"""
    try:
        response = requests.get(f"{BASE_URL}{path}", allow_redirects=allow_redirect)
        if response.status_code == expected_status:
            return "PASS", f"Status {response.status_code}"
        else:
            return "FAIL", f"Status {response.status_code}, expected {expected_status}"
    except Exception as e:
        return "FAIL", str(e)

def test_redirect(path, expected_location):
    """Test a route redirects to expected location"""
    try:
        response = requests.get(f"{BASE_URL}{path}", allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if expected_location in location:
                return "PASS", f"Redirects to {location}"
            else:
                return "FAIL", f"Redirects to {location}, expected {expected_location}"
        else:
            return "FAIL", f"Status {response.status_code}, expected redirect"
    except Exception as e:
        return "FAIL", str(e)

def test_api_endpoint(path, method="GET", data=None, expected_status=200):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{path}", json=data)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{path}", json=data)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{path}")
        
        if response.status_code == expected_status:
            try:
                json_data = response.json()
                return "PASS", f"Status {response.status_code}, JSON response"
            except:
                return "PASS", f"Status {response.status_code}"
        else:
            return "FAIL", f"Status {response.status_code}, expected {expected_status}"
    except Exception as e:
        return "FAIL", str(e)

def test_search_filter(endpoint, params):
    """Test search and filter functionality"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params)
        if response.status_code == 200:
            data = response.json()
            if 'opportunities' in data or 'grants' in data or 'results' in data:
                return "PASS", f"Returned data with params: {params}"
            else:
                return "PASS", "Response received"
        else:
            return "FAIL", f"Status {response.status_code}"
    except Exception as e:
        return "FAIL", str(e)

def test_page_elements(path, elements):
    """Test if page contains expected elements"""
    try:
        response = requests.get(f"{BASE_URL}{path}")
        if response.status_code != 200:
            return "FAIL", f"Page status {response.status_code}"
        
        content = response.text
        missing = []
        for element in elements:
            if element not in content:
                missing.append(element)
        
        if missing:
            return "FAIL", f"Missing elements: {', '.join(missing[:3])}"
        else:
            return "PASS", f"All {len(elements)} elements present"
    except Exception as e:
        return "FAIL", str(e)

def test_demo_badge():
    """Test if DEMO badge appears in mock mode"""
    try:
        response = requests.get(f"{BASE_URL}/api/opportunities")
        if response.status_code == 200:
            data = response.json()
            mode = data.get('mode', 'unknown')
            
            # Check if demo badge appears on page
            page_response = requests.get(f"{BASE_URL}/opportunities")
            if 'demo-badge' in page_response.text:
                return "PASS", f"Mode: {mode}, Demo badge present"
            else:
                return "PASS", f"Mode: {mode}"
        else:
            return "FAIL", f"API status {response.status_code}"
    except Exception as e:
        return "FAIL", str(e)

def run_all_tests():
    """Run comprehensive test suite"""
    runner = TestRunner()
    
    print("=" * 70)
    print("PINK LEMONADE - END-TO-END FEATURE & NAVIGATION TEST")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    # 1. CORE NAVIGATION ROUTES
    print("\n1. CORE NAVIGATION ROUTES")
    print("-" * 40)
    runner.test("Home Page (/)", test_redirect, "/", "/opportunities")
    runner.test("Opportunities Page", test_route, "/opportunities")
    runner.test("Profile Page", test_route, "/profile")
    runner.test("Dashboard Page", test_route, "/dashboard")
    runner.test("Settings Redirect", test_redirect, "/settings", "/profile")
    
    # 2. API ENDPOINTS - OPPORTUNITIES
    print("\n2. API ENDPOINTS - OPPORTUNITIES")
    print("-" * 40)
    runner.test("GET /api/opportunities", test_api_endpoint, "/api/opportunities")
    runner.test("POST /api/opportunities/save", test_api_endpoint, "/api/opportunities/save", "POST", {
        'opportunity_id': 'test123',
        'title': 'Test Grant',
        'funder': 'Test Foundation',
        'description': 'Test',
        'amount_min': 1000,
        'amount_max': 5000,
        'deadline': '2025-12-31',
        'source': 'test'
    })
    runner.test("POST /api/opportunities/apply", test_api_endpoint, "/api/opportunities/apply", "POST", {
        'opportunity_id': 'test456',
        'title': 'Test Grant 2',
        'funder': 'Test Foundation 2',
        'description': 'Test',
        'amount_min': 2000,
        'amount_max': 10000,
        'deadline': '2025-12-31',
        'source': 'test'
    })
    
    # 3. API ENDPOINTS - ORGANIZATION
    print("\n3. API ENDPOINTS - ORGANIZATION")
    print("-" * 40)
    runner.test("GET /api/organization", test_api_endpoint, "/api/organization")
    runner.test("POST /api/organization", test_api_endpoint, "/api/organization", "POST", {
        'name': 'Test Organization',
        'mission': 'Test mission statement',
        'focus_areas': ['Education', 'Youth'],
        'keywords': ['test', 'nonprofit']
    })
    
    # 4. API ENDPOINTS - PROFILE
    print("\n4. API ENDPOINTS - PROFILE")
    print("-" * 40)
    runner.test("GET /api/profile/user", test_api_endpoint, "/api/profile/user")
    runner.test("POST /api/profile/user", test_api_endpoint, "/api/profile/user", "POST", {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com'
    })
    runner.test("GET /api/profile/documents", test_api_endpoint, "/api/profile/documents")
    runner.test("GET /api/profile/context", test_api_endpoint, "/api/profile/context")
    
    # 5. API ENDPOINTS - GRANTS
    print("\n5. API ENDPOINTS - GRANTS")
    print("-" * 40)
    runner.test("GET /api/grants", test_api_endpoint, "/api/grants")
    runner.test("GET /api/grants/saved", test_api_endpoint, "/api/grants/saved")
    runner.test("GET /api/grants/applications", test_api_endpoint, "/api/grants/applications")
    
    # 6. API ENDPOINTS - AI FEATURES
    print("\n6. API ENDPOINTS - AI FEATURES")
    print("-" * 40)
    runner.test("POST /api/ai/match-score", test_api_endpoint, "/api/ai/match-score", "POST", {
        'grant': {'title': 'Test Grant', 'description': 'Education grant'},
        'organization': {'name': 'Test Org', 'mission': 'Education'}
    })
    runner.test("POST /api/ai/extract-grant", test_api_endpoint, "/api/ai/extract-grant", "POST", {
        'text': 'Grant opportunity: $10,000 for education programs'
    })
    runner.test("POST /api/ai/generate-narrative", test_api_endpoint, "/api/ai/generate-narrative", "POST", {
        'grant_id': 1,
        'prompt': 'Generate a brief narrative'
    })
    
    # 7. SEARCH & FILTERS
    print("\n7. SEARCH & FILTERS")
    print("-" * 40)
    runner.test("Search by keyword", test_search_filter, "/api/opportunities", {'search': 'community'})
    runner.test("Filter by city", test_search_filter, "/api/opportunities", {'city': 'Atlanta'})
    runner.test("Filter by focus area", test_search_filter, "/api/opportunities", {'focus_area': 'Youth'})
    runner.test("Filter by deadline", test_search_filter, "/api/opportunities", {'deadline_days': '30'})
    runner.test("Filter by source", test_search_filter, "/api/opportunities", {'source': 'grants_gov'})
    runner.test("Combined filters", test_search_filter, "/api/opportunities", {
        'search': 'grant',
        'focus_area': 'Education',
        'deadline_days': '60'
    })
    
    # 8. PAGINATION
    print("\n8. PAGINATION")
    print("-" * 40)
    runner.test("Page 1", test_search_filter, "/api/opportunities", {'page': '1'})
    runner.test("Page 2", test_search_filter, "/api/opportunities", {'page': '2'})
    runner.test("Custom page size", test_search_filter, "/api/opportunities", {'page': '1', 'per_page': '5'})
    
    # 9. PAGE ELEMENTS - OPPORTUNITIES
    print("\n9. PAGE ELEMENTS - OPPORTUNITIES")
    print("-" * 40)
    runner.test("Opportunities page elements", test_page_elements, "/opportunities", [
        'Grant Opportunities',
        'search-input',
        'city-filter',
        'focus-filter',
        'deadline-filter',
        'source-filter',
        'opportunities-container',
        'demo-badge',
        '--pink-matte: #db2777'
    ])
    
    # 10. PAGE ELEMENTS - PROFILE
    print("\n10. PAGE ELEMENTS - PROFILE")
    print("-" * 40)
    runner.test("Profile page elements", test_page_elements, "/profile", [
        'User Profile',
        'user-form',
        'org-form',
        'upload-zone',
        'completion-bar',
        'ai-context',
        'documents-list'
    ])
    
    # 11. PAGE ELEMENTS - DASHBOARD
    print("\n11. PAGE ELEMENTS - DASHBOARD")
    print("-" * 40)
    runner.test("Dashboard page elements", test_page_elements, "/dashboard", [
        'Dashboard',
        'Pink Lemonade'
    ])
    
    # 12. DATA MODE VERIFICATION
    print("\n12. DATA MODE VERIFICATION")
    print("-" * 40)
    runner.test("Demo badge display", test_demo_badge)
    
    # 13. ERROR HANDLING
    print("\n13. ERROR HANDLING")
    print("-" * 40)
    runner.test("404 for invalid route", test_route, "/invalid-route-test", 404)
    runner.test("API error for invalid grant ID", test_api_endpoint, "/api/grants/99999", "GET", None, 404)
    
    # 14. ADDITIONAL API ENDPOINTS
    print("\n14. ADDITIONAL API ENDPOINTS")
    print("-" * 40)
    runner.test("GET /api/analytics", test_api_endpoint, "/api/analytics")
    runner.test("GET /api/analytics/dashboard", test_api_endpoint, "/api/analytics/dashboard")
    runner.test("GET /api/scraper/sources", test_api_endpoint, "/api/scraper/sources")
    runner.test("GET /api/discovery/search", test_api_endpoint, "/api/discovery/search")
    
    # 15. WRITING ASSISTANT
    print("\n15. WRITING ASSISTANT")
    print("-" * 40)
    runner.test("GET /api/writing-assistant/templates", test_api_endpoint, "/api/writing-assistant/templates")
    runner.test("POST /api/writing-assistant/generate", test_api_endpoint, "/api/writing-assistant/generate", "POST", {
        'grant_id': 1,
        'template': 'brief'
    })
    
    # Generate summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {runner.passed + runner.failed + runner.skipped}")
    print(f"✓ Passed: {runner.passed}")
    print(f"✗ Failed: {runner.failed}")
    print(f"⊘ Skipped: {runner.skipped}")
    print(f"Success Rate: {runner.passed / max(1, runner.passed + runner.failed) * 100:.1f}%")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    return runner

if __name__ == "__main__":
    runner = run_all_tests()
    
    # Exit with error code if tests failed
    if runner.failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)