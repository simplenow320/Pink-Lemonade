"""
Comprehensive test for the consolidated grant matching system
Tests discovery, persistence, AI scoring, and Smart Tools access
"""
import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = 'http://localhost:5000'
TEST_ORG_ID = 1  # Using existing org

print("=" * 60)
print("GRANT MATCHING SYSTEM - COMPREHENSIVE TEST")
print("=" * 60)


def test_discovery_pipeline():
    """Test the complete discovery pipeline"""
    print("\n1. Testing Discovery Pipeline")
    print("-" * 40)
    
    # First, test the pipeline
    url = f"{BASE_URL}/api/matching/test/{TEST_ORG_ID}"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Pipeline test endpoint working")
        
        # Check each test result
        tests = result.get('tests', {})
        for test_name, test_result in tests.items():
            if isinstance(test_result, bool):
                status = "✅" if test_result else "❌"
                print(f"  {status} {test_name}: {test_result}")
        
        # Show summary
        if 'organization_name' in result:
            print(f"\nOrganization: {result['organization_name']}")
        if 'total_grants_in_db' in result:
            print(f"Grants in database: {result['total_grants_in_db']}")
        
        return result.get('success', False)
    else:
        print(f"❌ Pipeline test failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def test_grant_discovery():
    """Test grant discovery with the new V2 endpoint"""
    print("\n2. Testing Grant Discovery V2")
    print("-" * 40)
    
    # Test discovery endpoint
    url = f"{BASE_URL}/api/matching/discover/{TEST_ORG_ID}"
    params = {
        'limit': 10,
        'refresh': 'true'  # Force refresh to test external APIs
    }
    
    print(f"Calling: {url}")
    response = requests.get(url, params=params)
    
    if response.status_code in [200, 207]:  # 207 indicates partial success
        result = response.json()
        print(f"✅ Discovery endpoint responded")
        
        # Check discovery stats
        stats = result.get('discovery_stats', {})
        print(f"\nDiscovery Statistics:")
        print(f"  Total discovered: {stats.get('total_discovered', 0)}")
        print(f"  Newly added: {stats.get('newly_added', 0)}")
        print(f"  Updated: {stats.get('updated', 0)}")
        print(f"  From cache: {stats.get('from_cache', 0)}")
        print(f"  AI scored: {stats.get('ai_scored', 0)}")
        print(f"  Sources checked: {stats.get('sources_checked', [])}")
        print(f"  Sources failed: {stats.get('sources_failed', [])}")
        
        # Check grants returned
        grants = result.get('grants', [])
        print(f"\nGrants returned: {len(grants)}")
        
        # Show top 3 grants
        if grants:
            print("\nTop grants:")
            for i, grant in enumerate(grants[:3], 1):
                score = grant.get('match_score', 0)
                title = grant.get('title', 'Untitled')[:60]
                print(f"  {i}. [{score}/5] {title}...")
        
        # Check for errors
        if result.get('errors'):
            print(f"\n⚠️ Errors encountered: {result['errors']}")
        
        return len(grants) > 0
    else:
        print(f"❌ Discovery failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def test_persisted_grants():
    """Test that grants are persisted and accessible"""
    print("\n3. Testing Grant Persistence")
    print("-" * 40)
    
    url = f"{BASE_URL}/api/matching/grants/{TEST_ORG_ID}"
    params = {'limit': 5}
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        result = response.json()
        grants = result.get('grants', [])
        print(f"✅ Persisted grants endpoint working")
        print(f"  Grants in database: {len(grants)}")
        
        # Check grant fields
        if grants:
            sample = grants[0]
            required_fields = ['id', 'title', 'funder', 'status', 'org_id']
            missing = [f for f in required_fields if f not in sample]
            if missing:
                print(f"  ⚠️ Missing fields: {missing}")
            else:
                print(f"  ✅ All required fields present")
        
        return len(grants) > 0
    else:
        print(f"❌ Persistence check failed: {response.status_code}")
        return False


def test_smart_tools_access():
    """Test that Smart Tools can access grant data"""
    print("\n4. Testing Smart Tools Access")
    print("-" * 40)
    
    url = f"{BASE_URL}/api/matching/smart-tools/{TEST_ORG_ID}"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        grants = result.get('grants', [])
        print(f"✅ Smart Tools endpoint working")
        print(f"  Grants available: {len(grants)}")
        print(f"  Purpose: {result.get('purpose')}")
        
        # Verify grants have necessary fields for Smart Tools
        if grants:
            sample = grants[0]
            smart_tool_fields = ['title', 'funder', 'deadline', 'amount_min', 'amount_max']
            present = [f for f in smart_tool_fields if f in sample]
            print(f"  Smart Tool fields present: {present}")
        
        return True
    else:
        print(f"❌ Smart Tools access failed: {response.status_code}")
        return False


def test_discovery_stats():
    """Test statistics endpoint"""
    print("\n5. Testing Discovery Statistics")
    print("-" * 40)
    
    url = f"{BASE_URL}/api/matching/stats/{TEST_ORG_ID}"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        stats = result.get('stats', {})
        print(f"✅ Statistics endpoint working")
        print(f"  Total grants: {stats.get('total_grants', 0)}")
        print(f"  Recent discoveries: {stats.get('recent_discoveries', 0)}")
        print(f"  High matches: {stats.get('high_matches', 0)}")
        
        # Show source breakdown
        by_source = stats.get('by_source', {})
        if by_source:
            print(f"\n  By source:")
            for source, count in by_source.items():
                print(f"    - {source}: {count}")
        
        # Show status breakdown
        by_status = stats.get('by_status', {})
        if by_status:
            print(f"\n  By status:")
            for status, count in by_status.items():
                print(f"    - {status}: {count}")
        
        return True
    else:
        print(f"❌ Statistics failed: {response.status_code}")
        return False


def test_ai_scoring():
    """Test that AI scoring is working"""
    print("\n6. Testing AI Scoring")
    print("-" * 40)
    
    # Get grants with scores
    url = f"{BASE_URL}/api/matching/grants/{TEST_ORG_ID}"
    params = {'limit': 10}
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        result = response.json()
        grants = result.get('grants', [])
        
        # Check how many have scores
        scored = [g for g in grants if g.get('match_score') and g['match_score'] > 0]
        print(f"✅ AI Scoring check")
        print(f"  Grants with scores: {len(scored)}/{len(grants)}")
        
        if scored:
            # Show score distribution
            scores = [g['match_score'] for g in scored]
            avg_score = sum(scores) / len(scores)
            print(f"  Average score: {avg_score:.1f}")
            print(f"  Score range: {min(scores)} - {max(scores)}")
            
            # Check for match reasons
            with_reasons = [g for g in scored if g.get('match_reason')]
            print(f"  Grants with explanations: {len(with_reasons)}/{len(scored)}")
        
        return len(scored) > 0
    else:
        print(f"❌ AI scoring check failed: {response.status_code}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\nStarting comprehensive grant matching tests...")
    print("Testing with Organization ID:", TEST_ORG_ID)
    
    results = {
        'Pipeline Test': test_discovery_pipeline(),
        'Discovery V2': test_grant_discovery(),
        'Persistence': test_persisted_grants(),
        'Smart Tools': test_smart_tools_access(),
        'Statistics': test_discovery_stats(),
        'AI Scoring': test_ai_scoring()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    # Overall result
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Grant matching system is working!")
    else:
        failed = [name for name, passed in results.items() if not passed]
        print(f"⚠️ Some tests failed: {', '.join(failed)}")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server at", BASE_URL)
        print("Make sure the Flask app is running on port 5000")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)