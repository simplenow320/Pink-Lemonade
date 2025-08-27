#!/usr/bin/env python3
"""
Add sample impact intake data to test the enhanced Impact Report generation
"""

import json
import sys
sys.path.append('/home/runner/workspace')

from app import create_app
from app.models import db, Grant, ImpactIntake
from app.utils.impact_intake_validator import validate_and_merge_intake_payload
from datetime import datetime

def add_sample_intake_data():
    """Add sample impact intake submissions with participant data"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*50)
        print("Adding Sample Impact Intake Data")
        print("="*50 + "\n")
        
        # Get first grant
        grant = Grant.query.first()
        if not grant:
            print("❌ No grant found in database")
            return False
        
        print(f"✓ Using Grant: {grant.title}")
        
        # Sample intake submissions with participant demographics and stories
        sample_intakes = [
            {
                'submitted_by': 'Maria Rodriguez',
                'role': 'participant',
                'payload': {
                    'age': 32,
                    'zip': '48201',
                    'ethnicity': 'Hispanic/Latino',
                    'stories': [
                        "This program changed my life. I was able to start my own business and support my family.",
                        "The mentorship I received was invaluable. My mentor helped me navigate challenges I never thought I could overcome.",
                        "I'm now employing three other people from my community."
                    ],
                    'program_name': 'Entrepreneurship Training',
                    'completion_date': '2024-06-15'
                }
            },
            {
                'submitted_by': 'James Thompson',
                'role': 'participant',
                'payload': {
                    'age': 19,
                    'zip': '48202',
                    'ethnicity': 'African American',
                    'stories': [
                        "The youth leadership program gave me confidence and direction.",
                        "I learned skills that helped me get into college with a full scholarship.",
                        "Now I'm mentoring younger students in my neighborhood.",
                        "This program saved my future."
                    ],
                    'program_name': 'Youth Leadership Academy',
                    'completion_date': '2024-05-20'
                }
            },
            {
                'submitted_by': 'Sarah Chen',
                'role': 'staff',
                'payload': {
                    'observation': "Witnessed tremendous growth in participants",
                    'program_impact': "85% of graduates found employment within 3 months",
                    'challenges': "Need more funding for materials and supplies"
                }
            },
            {
                'submitted_by': 'Michael Johnson',
                'role': 'board',
                'payload': {
                    'strategic_view': "This grant has been transformational for our organization",
                    'community_feedback': "Local businesses are eager to hire our graduates",
                    'sustainability': "We're working on securing multi-year funding"
                }
            },
            {
                'submitted_by': 'Emily Wilson',
                'role': 'participant',
                'payload': {
                    'age': 45,
                    'zip': '48203',
                    'ethnicity': 'Caucasian',
                    'stories': [
                        "After losing my job, this program gave me new skills and hope.",
                        "The job training was exactly what I needed to restart my career."
                    ],
                    'program_name': 'Career Transition Services',
                    'completion_date': '2024-07-10'
                }
            }
        ]
        
        # Add each intake submission
        added_count = 0
        for intake_data in sample_intakes:
            try:
                # Validate and merge payload
                validated_payload = validate_and_merge_intake_payload(
                    intake_data['payload'],
                    {}  # No existing payload to merge with
                )
                
                # Create intake record
                intake = ImpactIntake()
                intake.grant_id = grant.id
                intake.submitted_by = intake_data['submitted_by']
                intake.role = intake_data['role']
                intake.payload = validated_payload
                intake.created_at = datetime.utcnow()
                
                db.session.add(intake)
                added_count += 1
                print(f"✓ Added intake from {intake_data['submitted_by']} ({intake_data['role']})")
                
            except Exception as e:
                print(f"✗ Failed to add intake from {intake_data['submitted_by']}: {e}")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\n✅ Successfully added {added_count} impact intake submissions")
        
        # Verify data
        total_intakes = ImpactIntake.query.filter_by(grant_id=grant.id).count()
        print(f"📊 Total intake submissions for this grant: {total_intakes}")
        
        # Show participant demographics
        participant_intakes = ImpactIntake.query.filter_by(
            grant_id=grant.id,
            role='participant'
        ).all()
        
        if participant_intakes:
            print("\n📋 Participant Demographics:")
            for intake in participant_intakes:
                payload = intake.payload
                print(f"  • {intake.submitted_by}: Age {payload.get('age')}, "
                      f"Zip {payload.get('zip')}, {payload.get('ethnicity')}")
                if payload.get('stories'):
                    print(f"    Stories: {len(payload['stories'])} submitted")
        
        return True

if __name__ == '__main__':
    try:
        success = add_sample_intake_data()
        
        if success:
            print("\n" + "="*50)
            print("✅ SAMPLE DATA ADDED SUCCESSFULLY")
            print("Now you can generate Impact Reports with real intake data!")
            print("="*50)
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)