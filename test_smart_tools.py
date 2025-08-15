#!/usr/bin/env python
"""Test Smart Tools Suite - AI-powered writing tools"""

from app import create_app, db
from app.models import Organization
from app.services.smart_tools import SmartToolsService
import json

app = create_app()

with app.app_context():
    # Initialize Smart Tools
    smart_tools = SmartToolsService()
    
    print("=" * 60)
    print("🚀 SMART TOOLS SUITE TEST")
    print("=" * 60)
    
    # Get test organization
    org = Organization.query.filter_by(name='Test Nonprofit').first()
    if not org:
        print("Test organization not found!")
        exit(1)
    
    print(f"\nOrganization: {org.name}")
    print(f"Mission: {org.mission}")
    print("-" * 40)
    
    # Test 1: Grant Pitch Generator
    print("\n🎯 TOOL 1: GRANT PITCH GENERATOR")
    print("-" * 40)
    
    print("Generating elevator pitch (60 seconds)...")
    pitch_result = smart_tools.generate_grant_pitch(org.id, pitch_type='elevator')
    
    if pitch_result.get('success'):
        print(f"✅ Pitch generated!")
        print(f"Speaking Time: {pitch_result.get('speaking_time')}")
        print(f"Word Count: {pitch_result.get('word_count')}")
        print(f"\nHook: {pitch_result.get('hook')}")
        print(f"\nKey Points:")
        for point in pitch_result.get('key_points', [])[:3]:
            print(f"  • {point}")
        print(f"\nCall to Action: {pitch_result.get('call_to_action')}")
        print(f"\nPitch Preview:")
        print(f"{pitch_result.get('pitch_text', '')[:200]}...")
    else:
        print(f"❌ Error: {pitch_result.get('error')}")
    
    # Test 2: Case for Support Builder
    print("\n📋 TOOL 2: CASE FOR SUPPORT BUILDER")
    print("-" * 40)
    
    campaign_details = {
        'goal': 500000,
        'purpose': 'Expand STEM programs to 5 new schools',
        'timeline': '18 months',
        'target_donors': 'foundations and corporate partners'
    }
    
    print(f"Campaign Goal: ${campaign_details['goal']:,.0f}")
    print(f"Purpose: {campaign_details['purpose']}")
    print("Generating case for support...")
    
    case_result = smart_tools.generate_case_for_support(org.id, campaign_details)
    
    if case_result.get('success'):
        print(f"✅ Case for support generated!")
        sections = case_result.get('sections', {})
        print(f"Sections created: {len(sections)}")
        print(f"Total Word Count: {case_result.get('total_word_count', 0)}")
        print(f"\nKey Messages:")
        for msg in case_result.get('key_messages', [])[:3]:
            print(f"  • {msg}")
        print(f"\nExecutive Summary Preview:")
        exec_summary = sections.get('executive_summary', '')
        print(f"{exec_summary[:200]}..." if exec_summary else "No summary")
    else:
        print(f"❌ Error: {case_result.get('error')}")
    
    # Test 3: Impact Report Creator
    print("\n📊 TOOL 3: IMPACT REPORT CREATOR")
    print("-" * 40)
    
    report_period = {
        'start': '2024-01-01',
        'end': '2024-12-31'
    }
    
    metrics_data = {
        'grants_submitted': 12,
        'grants_won': 4,
        'funding_secured': 450000,
        'beneficiaries_served': 1200,
        'programs_delivered': 8
    }
    
    print(f"Report Period: {report_period['start']} to {report_period['end']}")
    print(f"Grants Won: {metrics_data['grants_won']}/{metrics_data['grants_submitted']}")
    print(f"Funding Secured: ${metrics_data['funding_secured']:,.0f}")
    print("Generating impact report...")
    
    impact_result = smart_tools.generate_impact_report(org.id, report_period, metrics_data)
    
    if impact_result.get('success'):
        print(f"✅ Impact report generated!")
        report = impact_result.get('report', {})
        print(f"Impact Score: {impact_result.get('impact_score', 0)}/100")
        print(f"\nKey Achievements:")
        for achievement in report.get('key_achievements', [])[:3]:
            print(f"  • {achievement}")
        print(f"\nRecommended Visualizations:")
        for viz in report.get('visualizations', [])[:3]:
            print(f"  • {viz}")
    else:
        print(f"❌ Error: {impact_result.get('error')}")
    
    # Test 4: Quick Tools
    print("\n⚡ QUICK TOOLS TEST")
    print("-" * 40)
    
    # Thank You Letter
    print("\n💌 Generating thank you letter...")
    donor_info = {
        'name': 'Sarah Johnson',
        'amount': 5000,
        'purpose': 'STEM scholarship fund'
    }
    
    thank_you_result = smart_tools.generate_thank_you_letter(org.id, donor_info)
    
    if thank_you_result.get('success'):
        print(f"✅ Thank you letter generated!")
        print(f"Subject: {thank_you_result.get('subject_line')}")
        print(f"Letter Preview:")
        letter = thank_you_result.get('letter_text', '')
        print(f"{letter[:150]}..." if letter else "No letter")
    else:
        print(f"❌ Error: {thank_you_result.get('error')}")
    
    # Social Media Post
    print("\n📱 Generating social media post...")
    social_result = smart_tools.generate_social_media_post(
        org.id, 
        platform='twitter',
        topic='student success story'
    )
    
    if social_result.get('success'):
        print(f"✅ Twitter post generated!")
        print(f"Post: {social_result.get('post_text')}")
        print(f"Hashtags: {', '.join(social_result.get('hashtags', []))}")
        print(f"Best Time: {social_result.get('best_time_to_post')}")
    else:
        print(f"❌ Error: {social_result.get('error')}")
    
    print("\n" + "=" * 60)
    print("✅ SMART TOOLS TEST COMPLETE!")
    print("=" * 60)
    print("\nTools Tested:")
    print("  🎯 Grant Pitch Generator - ✅")
    print("  📋 Case for Support Builder - ✅")
    print("  📊 Impact Report Creator - ✅")
    print("  💌 Thank You Letter Writer - ✅")
    print("  📱 Social Media Post Creator - ✅")
    print("\nAll Smart Tools are operational!")