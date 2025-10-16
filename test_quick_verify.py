"""
Quick verification test for grant matching system
"""
import requests
import json

BASE_URL = 'http://localhost:5000'
ORG_ID = 1

print("=" * 60)
print("GRANT MATCHING SYSTEM - QUICK VERIFICATION")
print("=" * 60)

tests_passed = []
tests_failed = []

# Test 1: Discovery endpoint returns grants
print("\n1. Testing Discovery Endpoint...")
response = requests.get(f"{BASE_URL}/api/matching/discover/{ORG_ID}")
if response.status_code == 200:
    data = response.json()
    grants = data.get('grants', [])
    if grants:
        tests_passed.append("Discovery")
        print(f"✅ Discovery: {len(grants)} grants returned")
        # Show first grant with score
        if grants[0].get('match_score'):
            print(f"   First grant score: {grants[0]['match_score']}/5")
    else:
        tests_failed.append("Discovery - no grants returned")
        print("❌ Discovery: No grants returned")
else:
    tests_failed.append(f"Discovery - status {response.status_code}")
    print(f"❌ Discovery failed: {response.status_code}")

# Test 2: AI scoring works
print("\n2. Testing AI Scoring...")
response = requests.get(f"{BASE_URL}/api/matching/grants/{ORG_ID}?limit=10")
if response.status_code == 200:
    data = response.json()
    grants = data.get('grants', [])
    scored = [g for g in grants if g.get('match_score', 0) > 0]
    if scored:
        tests_passed.append("AI Scoring")
        avg_score = sum(g['match_score'] for g in scored) / len(scored)
        print(f"✅ AI Scoring: {len(scored)}/{len(grants)} grants scored")
        print(f"   Average score: {avg_score:.1f}/5")
    else:
        tests_failed.append("AI Scoring - no scores")
        print("❌ AI Scoring: No grants have scores")
else:
    tests_failed.append(f"AI Scoring - status {response.status_code}")
    print(f"❌ AI Scoring failed: {response.status_code}")

# Test 3: Smart Tools can access grants
print("\n3. Testing Smart Tools Access...")
response = requests.get(f"{BASE_URL}/api/matching/smart-tools/{ORG_ID}")
if response.status_code == 200:
    data = response.json()
    grants = data.get('grants', [])
    if grants:
        tests_passed.append("Smart Tools")
        print(f"✅ Smart Tools: {len(grants)} grants available")
    else:
        tests_failed.append("Smart Tools - no grants")
        print("❌ Smart Tools: No grants available")
else:
    tests_failed.append(f"Smart Tools - status {response.status_code}")
    print(f"❌ Smart Tools failed: {response.status_code}")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"✅ PASSED: {len(tests_passed)}")
for test in tests_passed:
    print(f"   - {test}")

if tests_failed:
    print(f"\n❌ FAILED: {len(tests_failed)}")
    for test in tests_failed:
        print(f"   - {test}")
else:
    print("\n🎉 ALL TESTS PASSED!")

print("=" * 60)