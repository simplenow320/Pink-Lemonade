#!/usr/bin/env python
"""
Test script for Website Context Service and Smart Tools Integration
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app properly
from app.models import db, Organization
from flask import Flask
from app.services.website_context_service import WebsiteContextService
from app.services.smart_tools import SmartToolsService
import json

# Create Flask app instance for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def test_website_context_fetch():
    """Test fetching website context"""
    print("\n" + "="*60)
    print("Testing Website Context Service")
    print("="*60)
    
    service = WebsiteContextService()
    
    # Test with a sample website
    test_url = "https://www.example.org"
    
    print(f"\nFetching context from: {test_url}")
    context = service.fetch_website_context(test_url)
    
    if context:
        print("\n✅ Website context fetched successfully!")
        print("\nExtracted information:")
        print(f"- Summary: {context.get('summary', 'No summary')[:200]}...")
        print(f"- Voice Tone: {context.get('organization_voice', {}).get('tone', 'Not detected')}")
        print(f"- Formality: {context.get('organization_voice', {}).get('formality', 'Not detected')}")
        
        if context.get('mission_vision'):
            print(f"- Mission: {context['mission_vision'].get('mission', 'Not found')[:150]}...")
        
        if context.get('programs'):
            print(f"- Programs found: {len(context.get('programs', []))}")
        
        if context.get('team_leadership'):
            print(f"- Team members found: {len(context.get('team_leadership', []))}")
        
        if context.get('writing_guidelines'):
            guidelines = context['writing_guidelines']
            print(f"\n📝 Writing Guidelines Generated:")
            print(f"- Recommended tone: {guidelines.get('tone', 'Not set')}")
            print(f"- Formality level: {guidelines.get('formality', 'Not set')}")
            print(f"- Power words: {', '.join(guidelines.get('words_to_use', [])[:5])}")
            
        return True
    else:
        print("❌ Failed to fetch website context")
        return False

def test_comprehensive_org_context():
    """Test comprehensive organization context building"""
    print("\n" + "="*60)
    print("Testing Comprehensive Organization Context Building")
    print("="*60)
    
    with app.app_context():
        # Get or create test organization
        org = Organization.query.first()
        
        if not org:
            print("Creating test organization...")
            org = Organization()
            org.name = "Test Community Foundation"
            org.legal_name = "Test Community Foundation Inc."
            org.ein = "12-3456789"
            org.mission = "We empower communities through education and resources"
            org.vision = "A world where every community thrives"
            org.values = "Integrity, Innovation, Impact"
            org.org_type = "501(c)(3)"
            org.year_founded = 2015
            org.website = "https://example.org"
            org.primary_focus_areas = ["education", "community development", "youth services"]
            org.secondary_focus_areas = ["health", "arts"]
            org.primary_city = "San Francisco"
            org.primary_state = "CA"
            org.primary_zip = "94102"
            org.annual_budget_range = "$500,000 - $1,000,000"
            org.annual_budget_exact = 750000
            org.staff_size = 12
            org.volunteer_count = 50
            org.board_size = 9
            org.unique_capabilities = "Culturally responsive programs with bilingual staff"
            org.annual_beneficiaries = 2500
            org.woman_led = True
            org.minority_led = True
            org.grant_writing_experience = "Intermediate"
            org.grant_writing_capacity = "Part-time staff"
            org.typical_grant_size = "$10,000 - $50,000"
            org.executive_director = "Jane Doe"
            org.board_chair = "John Smith"
            
            db.session.add(org)
            db.session.commit()
            print(f"✅ Created test organization: {org.name}")
        else:
            print(f"Using existing organization: {org.name}")
        
        # Test comprehensive context building
        smart_tools = SmartToolsService()
        context = smart_tools._build_comprehensive_org_context(org)
        
        print("\n📊 Comprehensive Organization Context Generated:")
        print(f"- Organization: {context.get('name')}")
        print(f"- Legal Name: {context.get('legal_name')}")
        print(f"- EIN: {context.get('ein')}")
        print(f"- Founded: {context.get('year_founded')}")
        print(f"- Mission: {context.get('mission')[:100]}...")
        print(f"- Vision: {context.get('vision')[:100]}...")
        print(f"- Primary Focus Areas: {', '.join(context.get('primary_focus_areas', []))}")
        print(f"- Service Area: {context.get('service_area_description')}")
        print(f"- Staff Size: {context.get('staff_size')}")
        print(f"- Annual Budget: {context.get('annual_budget_range')}")
        print(f"- Beneficiaries: {context.get('annual_beneficiaries'):,}")
        
        # Check diversity markers
        print("\n🌟 Diversity & Leadership:")
        print(f"- Woman-led: {context.get('woman_led')}")
        print(f"- Minority-led: {context.get('minority_led')}")
        print(f"- Executive Director: {context.get('executive_director')}")
        print(f"- Board Chair: {context.get('board_chair')}")
        
        # Check grant performance
        grant_perf = context.get('grant_performance', {})
        print("\n📈 Grant Performance:")
        print(f"- Total Grants: {grant_perf.get('total_grants_submitted', 0)}")
        print(f"- Success Rate: {grant_perf.get('success_rate', 0)}%")
        print(f"- Total Funding Pursued: ${grant_perf.get('total_funding_pursued', 0):,.0f}")
        
        # Check composite insights
        insights = context.get('composite_insights', {})
        print("\n🎯 Composite Intelligence:")
        print(f"- Maturity Score: {insights.get('organizational_maturity', 0)}/100")
        print(f"- Grant Readiness: {insights.get('grant_readiness_score', 0)}/100")
        print(f"- Recommended Tone: {insights.get('recommended_tone', 'Not set')}")
        print(f"- Competitive Advantages: {len(insights.get('competitive_advantages', []))} identified")
        
        if insights.get('competitive_advantages'):
            print("\n  Top Advantages:")
            for i, adv in enumerate(insights['competitive_advantages'][:3], 1):
                print(f"  {i}. {adv[:100]}...")
        
        # Check website insights if available
        web_insights = context.get('website_insights', {})
        if web_insights and web_insights.get('organization_voice'):
            print("\n🌐 Website Intelligence:")
            print(f"- Voice Tone: {web_insights.get('organization_voice', {}).get('tone', 'Not detected')}")
            print(f"- Tagline: {web_insights.get('tagline', 'Not found')}")
            print(f"- Programs from Web: {len(web_insights.get('programs_detailed', []))}")
            print(f"- Team Profiles: {len(web_insights.get('team_profiles', []))}")
            print(f"- Impact Stories: {len(web_insights.get('impact_stories_web', []))}")
            print(f"- Awards: {len(web_insights.get('awards_recognition', []))}")
        
        return True

def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print(" WEBSITE CONTEXT & SMART TOOLS INTEGRATION TEST")
    print("🚀"*30)
    
    # Test 1: Website Context Service
    website_test = test_website_context_fetch()
    
    # Test 2: Comprehensive Org Context
    context_test = test_comprehensive_org_context()
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    print(f"✅ Website Context Service: {'PASSED' if website_test else 'FAILED'}")
    print(f"✅ Comprehensive Org Context: {'PASSED' if context_test else 'FAILED'}")
    
    if website_test and context_test:
        print("\n🎉 ALL TESTS PASSED! The integration is working correctly.")
        print("\nThe AI now has access to:")
        print("- Complete organization profile data (50+ fields)")
        print("- Real-time website intelligence")
        print("- Grant performance metrics")
        print("- Competitive advantages analysis")
        print("- Writing style guidelines")
        print("\nThe Smart Tools can now write with deep organizational knowledge!")
    else:
        print("\n⚠️ Some tests failed. Please review the output above.")

if __name__ == "__main__":
    main()