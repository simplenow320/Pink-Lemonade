"""
Test Enhanced AI Matching System
Demonstrates quality-over-quantity grant matching
"""
import requests
import json

BASE_URL = 'http://localhost:5000'
ORG_ID = 1

def print_match_card(match):
    """Pretty print a match card"""
    print(f"\n{'='*60}")
    print(f"🎯 {match['composite_score']:.0f}% Match - {match['confidence_level'].upper()}")
    print(f"Grant: {match['grant']['title'][:60]}...")
    print(f"Funder: {match['grant']['funder']}")
    print(f"Amount: ${match['grant'].get('amount_max', 'N/A')}")
    print(f"Deadline: {match['grant'].get('deadline', 'Open')}")
    print(f"\n📊 SCORING BREAKDOWN:")
    for dim, score in match['dimensions'].items():
        emoji = "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
        dim_name = dim.replace('_', ' ').title()
        print(f"  {emoji} {dim_name}: {score:.0f}%")
    print(f"\n💡 {match['recommended_action']}")
    print(f"Success Probability: {match['success_probability']*100:.0f}%")
    if match['match_explanation']:
        print(f"\n📝 EXPLANATION:")
        print(match['match_explanation'])

def test_enhanced_matching():
    """Test the enhanced matching system"""
    print("="*70)
    print(" ENHANCED GRANT MATCHING TEST - QUALITY OVER QUANTITY")
    print("="*70)
    
    # First ensure we have the enhanced matcher registered
    try:
        # Register the blueprint if not already done
        from app import app
        from app.api.enhanced_matching import enhanced_matching_bp
        app.register_blueprint(enhanced_matching_bp)
        print("✅ Enhanced matching endpoint registered")
    except:
        print("⚠️ Could not register endpoint in test mode")
    
    # Test 1: Get top quality matches
    print("\n1. Getting High-Quality Matches Only")
    print("-" * 40)
    
    url = f"{BASE_URL}/api/matching/excellence/{ORG_ID}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            stats = data.get('statistics', {})
            print(f"✅ Found {stats['total_evaluated']} quality matches")
            print(f"   - Apply Now (85+): {stats['high_confidence']} grants")
            print(f"   - Worth Exploring (70-84): {stats['medium_confidence']} grants")
            print(f"   - Average Score: {stats['average_score']}%")
            print(f"   - Best Match: {stats['best_match_score']}%")
            
            # Show "Apply Now" grants
            apply_now = data['matches'].get('apply_now', [])
            if apply_now:
                print(f"\n🎯 TOP TIER - APPLY NOW ({len(apply_now)} grants)")
                print("These are your BEST opportunities:")
                for match in apply_now[:3]:  # Show top 3
                    print_match_card(match)
            
            # Show "Worth Exploring" grants
            explore = data['matches'].get('worth_exploring', [])
            if explore:
                print(f"\n✨ WORTH EXPLORING ({len(explore)} grants)")
                print("Good fits with minor gaps:")
                for match in explore[:2]:  # Show top 2
                    print_match_card(match)
        else:
            print(f"❌ Matching failed: {data.get('error')}")
    else:
        print(f"❌ API error: {response.status_code}")
        print(response.text[:200])
    
    # Test 2: Get detailed analysis for a specific grant
    print("\n\n2. Detailed Match Analysis")
    print("-" * 40)
    
    # Get the first grant for detailed analysis
    grants_url = f"{BASE_URL}/api/matching/grants/{ORG_ID}?limit=1"
    grant_response = requests.get(grants_url)
    
    if grant_response.status_code == 200:
        grants = grant_response.json().get('grants', [])
        if grants:
            grant_id = grants[0]['id']
            detail_url = f"{BASE_URL}/api/matching/excellence/{ORG_ID}/{grant_id}"
            detail_response = requests.get(detail_url)
            
            if detail_response.status_code == 200:
                analysis = detail_response.json().get('analysis', {})
                print(f"✅ Detailed analysis for Grant #{grant_id}")
                
                # Show insights
                insights = analysis.get('insights', {})
                if insights.get('quick_wins'):
                    print("\n🏆 QUICK WINS:")
                    for win in insights['quick_wins']:
                        print(f"   - {win}")
                
                if insights.get('red_flags'):
                    print("\n🚩 RED FLAGS:")
                    for flag in insights['red_flags']:
                        print(f"   - {flag}")
                
                if insights.get('improvement_suggestions'):
                    print("\n💡 TO IMPROVE CHANCES:")
                    for suggestion in insights['improvement_suggestions']:
                        print(f"   - {suggestion}")
    
    # Test 3: Quality comparison
    print("\n\n3. Quality vs Quantity Comparison")
    print("-" * 40)
    
    # Get all grants (old way)
    old_url = f"{BASE_URL}/api/matching/grants/{ORG_ID}"
    old_response = requests.get(old_url)
    
    if old_response.status_code == 200:
        all_grants = old_response.json().get('grants', [])
        print(f"📊 Old System: Would show {len(all_grants)} grants")
        print(f"📊 New System: Shows only {stats.get('total_evaluated', 0)} quality matches")
        print(f"\n✅ Reduction: {100 - (stats.get('total_evaluated', 0)/len(all_grants)*100):.0f}% less noise")
        print("✅ Result: Users see only grants worth their time!")

if __name__ == "__main__":
    test_enhanced_matching()