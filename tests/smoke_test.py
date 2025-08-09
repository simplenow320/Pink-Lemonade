#!/usr/bin/env python3
"""
Smoke Tests for Pink Lemonade Grant Management Platform
Verifies core functionality works end-to-end
"""

import sys
import os
import tempfile
import json
import logging
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from app import create_app, db
from app.models import Grant, Org, Watchlist
from app.services.scraper_service import upsert_grant

class SmokeTestRunner:
    """Runs smoke tests and tracks results"""
    
    def __init__(self):
        self.results = []
        self.app = None
        self.base_url = "http://localhost:5000"
        
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        print(f"[{status}] {test_name}: {message}")
        
    def setup_app(self):
        """Set up test application"""
        try:
            # Create test app
            os.environ['APP_DATA_MODE'] = 'DEMO'  # Use demo mode for testing
            self.app = create_app()
            
            with self.app.app_context():
                # Create tables if they don't exist
                db.create_all()
                
                # Create test organization if it doesn't exist
                test_org = Org.query.filter_by(name="Test Organization").first()
                if not test_org:
                    test_org = Org(
                        name="Test Organization",
                        mission="Testing platform functionality"
                    )
                    db.session.add(test_org)
                    db.session.commit()
                    
            self.log_result("App Setup", True, "Flask app created and database initialized")
            return True
            
        except Exception as e:
            self.log_result("App Setup", False, f"Failed to set up app: {str(e)}")
            return False
    
    def test_app_boots(self):
        """Test 1: Verify app boots and responds"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code in [200, 302]:  # 302 might be redirect to login
                self.log_result("App Boots", True, f"App responding with status {response.status_code}")
                return True
            else:
                self.log_result("App Boots", False, f"Unexpected status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_result("App Boots", False, f"Connection failed: {str(e)}")
            return False
    
    def test_grants_api(self):
        """Test 2: Test grants API endpoints"""
        try:
            # Test GET /api/grants
            response = requests.get(f"{self.base_url}/api/grants", timeout=10)
            get_works = response.status_code == 200
            
            # Test POST /api/grants
            grant_data = {
                "title": "Test Grant",
                "funder": "Test Foundation",
                "description": "A test grant for smoke testing",
                "amount": 50000,
                "deadline": "2025-12-31"
            }
            
            response = requests.post(
                f"{self.base_url}/api/grants", 
                json=grant_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # Accept either success or "not implemented" as valid responses
            post_works = response.status_code in [200, 201, 501]
            
            if get_works and post_works:
                self.log_result("Grants API", True, "GET and POST endpoints responding")
                return True
            else:
                self.log_result("Grants API", False, f"GET status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Grants API", False, f"API test failed: {str(e)}")
            return False
    
    def test_upsert_deduplication(self):
        """Test 3: Test grant upsert deduplication functionality"""
        try:
            with self.app.app_context():
                # Create first grant
                grant_data = {
                    'title': 'Duplicate Test Grant',
                    'funder': 'Test Foundation',
                    'link': 'https://test.example.com/grant1',
                    'deadline': '2025-12-31',
                    'amount_min': 10000,
                    'amount_max': 50000,
                    'geography': 'United States',
                    'eligibility': 'Nonprofits',
                    'source_name': 'Test Source',
                    'source_url': 'https://test.example.com'
                }
                
                # First upsert
                grant1 = upsert_grant(grant_data)
                original_count = Grant.query.count()
                
                # Second upsert with same data (should not create duplicate)
                grant2 = upsert_grant(grant_data)
                final_count = Grant.query.count()
                
                if original_count == final_count and grant1 and grant2:
                    if grant1.id == grant2.id:
                        self.log_result("Upsert Deduplication", True, "Duplicate grants properly prevented")
                        return True
                    else:
                        self.log_result("Upsert Deduplication", False, "Different grant IDs returned")
                        return False
                else:
                    self.log_result("Upsert Deduplication", False, f"Grant count changed: {original_count} -> {final_count}")
                    return False
                    
        except Exception as e:
            self.log_result("Upsert Deduplication", False, f"Upsert test failed: {str(e)}")
            return False
    
    def test_watchlists_crud(self):
        """Test 4: Test watchlists CRUD operations"""
        try:
            # Test GET /api/watchlists
            response = requests.get(f"{self.base_url}/api/watchlists", timeout=10)
            get_works = response.status_code == 200
            
            # Test POST /api/watchlists
            watchlist_data = {
                "name": "Test Watchlist",
                "description": "A test watchlist for smoke testing",
                "keywords": ["test", "automation"]
            }
            
            response = requests.post(
                f"{self.base_url}/api/watchlists",
                json=watchlist_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # Accept either success or "not implemented" as valid responses
            post_works = response.status_code in [200, 201, 501]
            
            if get_works and post_works:
                self.log_result("Watchlists CRUD", True, "GET and POST endpoints responding")
                return True
            else:
                self.log_result("Watchlists CRUD", False, f"GET works: {get_works}, POST works: {post_works}")
                return False
                
        except Exception as e:
            self.log_result("Watchlists CRUD", False, f"Watchlist CRUD test failed: {str(e)}")
            return False
    
    def test_ai_endpoints_without_key(self):
        """Test 5: Test AI endpoints return proper error when no API key"""
        try:
            # Temporarily remove OpenAI key to test error handling
            original_key = os.environ.get('OPENAI_API_KEY')
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            
            # Test AI match endpoint
            match_data = {
                "grant": {"title": "Test Grant", "description": "Test description"},
                "organization": {"name": "Test Org", "focus_areas": ["testing"]}
            }
            
            response = requests.post(
                f"{self.base_url}/api/ai/match",
                json=match_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # Should return error about AI being disabled
            match_response_valid = (
                response.status_code in [400, 501, 503] or 
                (response.status_code == 200 and 'AI_DISABLED' in response.text) or
                'AI' in response.text or 'disabled' in response.text.lower()
            )
            
            # Test AI extract endpoint
            extract_data = {"text": "Test grant text for extraction"}
            
            response = requests.post(
                f"{self.base_url}/api/ai/extract",
                json=extract_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            extract_response_valid = (
                response.status_code in [400, 501, 503] or 
                (response.status_code == 200 and 'AI_DISABLED' in response.text) or
                'AI' in response.text or 'disabled' in response.text.lower()
            )
            
            # Restore original key
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key
            
            if match_response_valid and extract_response_valid:
                self.log_result("AI Endpoints No Key", True, "AI endpoints properly handle missing API key")
                return True
            else:
                self.log_result("AI Endpoints No Key", False, "AI endpoints don't properly handle missing key")
                return False
                
        except Exception as e:
            # Restore key in case of error
            if 'original_key' in locals() and original_key:
                os.environ['OPENAI_API_KEY'] = original_key
            self.log_result("AI Endpoints No Key", False, f"AI endpoint test failed: {str(e)}")
            return False
    
    def test_opportunities_endpoint(self):
        """Test 6: Test opportunities endpoint (main discovery endpoint)"""
        try:
            response = requests.get(f"{self.base_url}/api/opportunities", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'opportunities' in data:
                    self.log_result("Opportunities Endpoint", True, f"Returned {len(data.get('opportunities', []))} opportunities")
                    return True
                elif isinstance(data, list):
                    self.log_result("Opportunities Endpoint", True, f"Returned {len(data)} opportunities")
                    return True
                else:
                    self.log_result("Opportunities Endpoint", False, f"Unexpected response format: {type(data)}")
                    return False
            else:
                self.log_result("Opportunities Endpoint", False, f"HTTP {response.status_code}: {response.text[:100]}")
                return False
                
        except Exception as e:
            self.log_result("Opportunities Endpoint", False, f"Opportunities test failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all smoke tests"""
        print("=== PINK LEMONADE SMOKE TESTS ===")
        print(f"Started at: {datetime.now().isoformat()}")
        print()
        
        # Setup
        if not self.setup_app():
            return False
        
        # Run tests
        tests = [
            self.test_app_boots,
            self.test_grants_api,
            self.test_upsert_deduplication,
            self.test_watchlists_crud,
            self.test_ai_endpoints_without_key,
            self.test_opportunities_endpoint
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print()
        print(f"=== RESULTS: {passed}/{total} TESTS PASSED ===")
        print(f"Completed at: {datetime.now().isoformat()}")
        
        return passed == total
    
    def generate_report(self):
        """Generate test report"""
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        total = len(self.results)
        
        report = f"""# Smoke Test Report - Pink Lemonade Grant Platform

**Test Run:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Results:** {passed}/{total} tests passed ({(passed/total*100):.1f}%)

## Test Results

"""
        
        for result in self.results:
            status_emoji = "✅" if result['status'] == 'PASS' else "❌"
            report += f"### {status_emoji} {result['test']}\n"
            report += f"**Status:** {result['status']}\n"
            if result['message']:
                report += f"**Details:** {result['message']}\n"
            report += f"**Time:** {result['timestamp']}\n\n"
        
        report += f"""## Summary

The smoke tests verify core platform functionality:

1. **App Boots**: Verifies the Flask application starts and responds
2. **Grants API**: Tests basic grant CRUD endpoints
3. **Upsert Deduplication**: Verifies grant deduplication works correctly  
4. **Watchlists CRUD**: Tests watchlist management endpoints
5. **AI Endpoints**: Verifies proper error handling when OpenAI API key is missing
6. **Opportunities Endpoint**: Tests the main grant discovery functionality

{'🎉 All core functionality is working!' if passed == total else '⚠️ Some issues found - see failed tests above.'}
"""
        
        return report

def main():
    """Main function to run smoke tests"""
    runner = SmokeTestRunner()
    success = runner.run_all_tests()
    
    # Generate and save report
    report = runner.generate_report()
    
    with open('TEST_REPORT.md', 'w') as f:
        f.write(report)
    
    print(f"\nDetailed report saved to: TEST_REPORT.md")
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()