#!/usr/bin/env python
"""Test AI Grant Matching with REACTO"""

from app import create_app, db
from app.models import Grant, Organization
from app.services.ai_grant_matcher import AIGrantMatcher
import json

app = create_app()

with app.app_context():
    # Get test organization
    org = Organization.query.filter_by(name='Test Nonprofit').first()
    if not org:
        print("Test organization not found!")
        exit(1)
    
    print(f"Testing AI matching for: {org.name}")
    print(f"Mission: {org.mission}")
    print(f"Focus Areas: {org.primary_focus_areas}")
    print("-" * 50)
    
    # Get grants
    grants = Grant.query.limit(3).all()
    print(f"\nFound {len(grants)} grants to match")
    
    # Initialize matcher
    matcher = AIGrantMatcher()
    
    # Test single grant analysis
    if grants:
        print(f"\n🔍 Analyzing grant: {grants[0].title[:50]}...")
        analysis = matcher.analyze_single_grant(grants[0].id, org.id)
        
        if 'match_analysis' in analysis:
            match = analysis['match_analysis']
            print(f"\n✅ Match Score: {match.get('match_score', 0)}/5")
            print(f"📊 Verdict: {match.get('verdict', 'N/A')}")
            print(f"💡 Recommendation: {match.get('recommendation', 'N/A')}")
            
            print("\n🎯 Key Alignments:")
            for alignment in match.get('key_alignments', [])[:3]:
                print(f"  • {alignment}")
            
            print("\n⚠️ Potential Challenges:")
            for challenge in match.get('potential_challenges', [])[:2]:
                print(f"  • {challenge}")
            
            print("\n📝 Next Steps:")
            for step in match.get('next_steps', [])[:3]:
                print(f"  • {step}")
        else:
            print("❌ AI analysis failed:", analysis.get('error', 'Unknown error'))
    
    # Test bulk matching
    print("\n" + "="*50)
    print("🚀 Getting top recommendations...")
    recommendations = matcher.match_grants_for_organization(org.id, limit=5)
    
    if recommendations:
        print(f"\n📋 Top {len(recommendations)} Recommendations:")
        for i, grant in enumerate(recommendations, 1):
            print(f"\n{i}. {grant['title'][:60]}...")
            print(f"   Score: {grant.get('match_score', 0)}/5 - {grant.get('match_verdict', 'N/A')}")
            print(f"   Funder: {grant.get('funder', 'Unknown')}")
            print(f"   Amount: ${grant.get('amount_min', 0):,.0f} - ${grant.get('amount_max', 0):,.0f}")
            print(f"   Tip: {grant.get('application_tips', 'No tips available')[:100]}...")
    else:
        print("No recommendations generated")
    
    print("\n✅ AI Matching Test Complete!")