#!/usr/bin/env python
"""Test Workflow Pipeline - 8-Stage Grant Management"""

from app import create_app, db
from app.models import Grant, Organization
from app.services.workflow_manager import WorkflowManager
import json

app = create_app()

with app.app_context():
    # Initialize workflow manager
    manager = WorkflowManager()
    
    print("=" * 60)
    print("🚀 GRANT WORKFLOW PIPELINE TEST")
    print("=" * 60)
    
    # Get test organization
    org = Organization.query.first()
    if not org:
        print("No organization found!")
        exit(1)
    
    print(f"\nOrganization: {org.name}")
    print("-" * 40)
    
    # Get grants
    grants = Grant.query.filter_by(org_id=org.id).all()
    print(f"Total grants: {len(grants)}")
    
    # Show pipeline stages
    print("\n📊 PIPELINE STAGES:")
    for key, info in manager.STAGES.items():
        print(f"  {info['icon']} {info['order']}. {info['name']} - {info['description']}")
    
    # Test moving a grant through stages
    if grants:
        test_grant = grants[0]
        print(f"\n🎯 Testing grant: {test_grant.title[:50]}...")
        print(f"Current stage: {test_grant.application_stage}")
        
        # Move to researching
        print("\n➡️ Moving to Researching stage...")
        result = manager.move_to_stage(test_grant.id, 'researching', 'Testing workflow')
        if result['success']:
            print(f"✅ Moved to: {result['new_stage']}")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        # Get checklist
        print("\n📋 Stage Checklist:")
        checklist_result = manager.get_stage_checklist(test_grant.id)
        if checklist_result['success']:
            for item in checklist_result['checklist']:
                status = "✓" if item.get('completed') else "○"
                print(f"  {status} {item['task']} [{item['priority']}]")
            print(f"\nCompletion: {checklist_result['completion_rate']*100:.0f}%")
        
        # Move to writing
        print("\n➡️ Moving to Writing stage...")
        result = manager.move_to_stage(test_grant.id, 'writing', 'Ready to write')
        if result['success']:
            print(f"✅ Moved to: {result['new_stage']}")
    
    # Get pipeline overview
    print("\n" + "=" * 60)
    print("📊 PIPELINE OVERVIEW")
    print("=" * 60)
    
    pipeline_status = manager.get_pipeline_status(org.id)
    if pipeline_status['success']:
        metrics = pipeline_status['metrics']
        print(f"\n📈 Metrics:")
        print(f"  • Total Grants: {metrics['total_grants']}")
        print(f"  • In Progress: {metrics['in_progress']}")
        print(f"  • Success Rate: {metrics['success_rate']:.1f}%")
        print(f"  • Total Potential: ${metrics['total_potential']:,.0f}")
        
        print(f"\n🔄 Stage Distribution:")
        for stage_key, stage_data in pipeline_status['pipeline'].items():
            if stage_data['count'] > 0:
                print(f"  • {stage_data['info']['icon']} {stage_data['info']['name']}: {stage_data['count']} grants (${stage_data['total_value']:,.0f})")
    
    # Test batch operations
    print("\n" + "=" * 60)
    print("⚡ BATCH OPERATIONS")
    print("=" * 60)
    
    # Move multiple grants
    if len(grants) >= 2:
        grant_ids = [g.id for g in grants[:2]]
        print(f"\nMoving {len(grant_ids)} grants to Discovery stage...")
        batch_result = manager.batch_move(grant_ids, 'discovery')
        print(f"✅ Moved: {batch_result['moved']}")
        print(f"❌ Failed: {batch_result['failed']}")
    
    print("\n✅ Workflow Pipeline Test Complete!")