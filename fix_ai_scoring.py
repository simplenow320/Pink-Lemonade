"""
Fix AI scoring for existing grants
Forces AI scoring on grants that don't have scores yet
"""
import requests
import json

BASE_URL = 'http://localhost:5000'
ORG_ID = 1

print("=" * 60)
print("FIXING AI SCORING FOR EXISTING GRANTS")
print("=" * 60)

# First, trigger AI scoring using the batch endpoint
print("\n1. Triggering batch AI scoring...")
url = f"{BASE_URL}/api/grant-matching/batch"
response = requests.post(url, json={})

if response.status_code == 200:
    result = response.json()
    print(f"✅ AI scoring triggered")
    print(f"  Total grants: {result.get('total_grants', 0)}")
    print(f"  Newly scored: {result.get('updated', 0)}")
else:
    print(f"⚠️ Batch scoring returned: {response.status_code}")
    print(f"Response: {response.text[:200]}")

# Now verify scores were applied
print("\n2. Verifying AI scores...")
url = f"{BASE_URL}/api/matching/grants/{ORG_ID}"
params = {'limit': 10}
response = requests.get(url, params=params)

if response.status_code == 200:
    result = response.json()
    grants = result.get('grants', [])
    
    scored = [g for g in grants if g.get('match_score') and g['match_score'] > 0]
    print(f"✅ Grants with scores: {len(scored)}/{len(grants)}")
    
    if scored:
        print("\nTop scored grants:")
        for i, grant in enumerate(scored[:5], 1):
            score = grant.get('match_score', 0)
            title = grant.get('title', 'Untitled')[:50]
            reason = grant.get('match_reason', '')[:60]
            print(f"  {i}. [{score}/5] {title}")
            if reason:
                print(f"     Reason: {reason}...")
else:
    print(f"❌ Failed to get grants: {response.status_code}")

print("\n" + "=" * 60)
print("AI SCORING FIX COMPLETE")
print("=" * 60)