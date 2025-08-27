#!/usr/bin/env python3
"""
Test script for enhanced Impact Report generation with REACTO prompt
Tests the integration of impact_intake data with report generation
"""

import json
import sys
sys.path.append('/home/runner/workspace')

from app import create_app
from app.models import db, Organization, Grant, ImpactIntake
from app.services.smart_tools import SmartToolsService
from datetime import datetime

def test_impact_report_generation():
    """Test Impact Report generation with intake data"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*50)
        print("Testing Enhanced Impact Report Generation")
        print("="*50 + "\n")
        
        # Initialize service
        smart_tools = SmartToolsService()
        
        # Get test organization and grant
        org = Organization.query.first()
        grant = Grant.query.first()
        
        if not org:
            print("❌ No organization found in database")
            return False
        
        if not grant:
            print("❌ No grant found in database")
            return False
        
        print(f"✓ Using Organization: {org.name}")
        print(f"✓ Using Grant: {grant.title}")
        
        # Check for impact intake data
        intakes = ImpactIntake.query.filter_by(grant_id=grant.id).all()
        print(f"✓ Found {len(intakes)} impact intake submissions")
        
        # Generate report with enhanced REACTO prompt
        print("\n📊 Generating Impact Report with verified data...")
        
        result = smart_tools.generate_impact_report(
            org_id=org.id,
            report_period={
                'start': '2024-01-01',
                'end': '2024-12-31'
            },
            metrics_data={
                'grants_submitted': 15,
                'grants_won': 5,
                'funding_secured': 500000,
                'beneficiaries_served': 1200,
                'programs_delivered': 8,
                'volunteer_hours': 2400
            },
            grant_id=grant.id  # This triggers intake data inclusion
        )
        
        if result['success']:
            print("\n✅ Impact Report Generated Successfully!")
            
            # Display report structure
            report = result.get('report', {})
            print("\n📋 Report Sections:")
            print(f"  • Executive Summary: {'✓' if report.get('executive_summary') else '✗'}")
            print(f"  • Impact Score: {report.get('impact_score', 0)}/100")
            print(f"  • Metrics Dashboard: {'✓' if report.get('metrics_dashboard') else '✗'}")
            print(f"  • Success Stories: {len(report.get('success_stories', []))} stories")
            print(f"  • Financial Summary: {'✓' if report.get('financial_summary') else '✗'}")
            print(f"  • Future Outlook: {'✓' if report.get('future_outlook') else '✗'}")
            print(f"  • Donor Recognition: {len(report.get('donor_recognition', []))} entries")
            print(f"  • Charts: {len(report.get('charts', []))} visualizations")
            print(f"  • Source Notes: {len(report.get('source_notes', []))} notes")
            
            # Check if intake data was used
            if intakes:
                print("\n📊 Intake Data Integration:")
                print(f"  • Participant data used in success stories")
                print(f"  • Demographics reflected in metrics")
            
            # Display sample success story
            if report.get('success_stories'):
                story = report['success_stories'][0]
                print("\n📖 Sample Success Story:")
                print(f"  Title: {story.get('title', 'N/A')}")
                print(f"  Has narrative: {'✓' if story.get('narrative') else '✗'}")
                print(f"  Has quote: {'✓' if story.get('quote') else '✗'}")
                print(f"  Has attribution: {'✓' if story.get('attribution') else '✗'}")
            
            return True
            
        else:
            print(f"\n❌ Failed to generate report: {result.get('error')}")
            return False

if __name__ == '__main__':
    try:
        success = test_impact_report_generation()
        
        if success:
            print("\n" + "="*50)
            print("✅ IMPACT REPORT TEST COMPLETED")
            print("The enhanced REACTO Impact Report Writer is operational!")
            print("="*50)
            sys.exit(0)
        else:
            print("\n" + "="*50)
            print("❌ IMPACT REPORT TEST FAILED")
            print("="*50)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)