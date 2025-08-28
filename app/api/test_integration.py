"""
Test Integration API - Verify grant discovery pipeline
"""
from flask import Blueprint, jsonify
from app import db
from app.models import Grant, Organization
from app.services.candid_grants_client import get_candid_grants_client
from app.services.grant_discovery_service import GrantDiscoveryService
import logging

logger = logging.getLogger(__name__)

test_integration_bp = Blueprint('test_integration', __name__)

@test_integration_bp.route('/api/test/candid-pipeline', methods=['GET'])
def test_candid_pipeline():
    """Test complete Candid data pipeline"""
    results = {
        'candid_api': False,
        'grants_imported': 0,
        'discovery_working': False,
        'total_grants_in_db': 0,
        'errors': []
    }
    
    try:
        # 1. Test Candid API connection
        client = get_candid_grants_client()
        test_data = client.get_summary()
        
        if test_data and 'number_of_grants' in test_data:
            results['candid_api'] = True
            logger.info(f"Candid API working: {test_data.get('number_of_grants', 0)} grants found")
        
        # 2. Test importing some grants
        transactions = client.search_grants(keyword="education", state="MI", limit=10)
        if transactions:
            for t in transactions[:5]:
                try:
                    # Create grant from Candid data
                    grant = Grant(
                        title=f"{t.get('funder_name', 'Unknown')} - {t.get('recipient_name', 'Grant')}",
                        funder=t.get('funder_name', 'Unknown'),
                        amount_min=t.get('amount', 1000),
                        amount_max=t.get('amount', 100000),
                        geography=f"{t.get('recip_city', '')}, {t.get('recip_state', '')}",
                        eligibility="Organizations supporting education",
                        source_name='Candid Test Import',
                        source_url='https://candid.org',
                        status='idea'
                    )
                    db.session.add(grant)
                    results['grants_imported'] += 1
                except Exception as e:
                    results['errors'].append(f"Import error: {str(e)}")
            
            db.session.commit()
        
        # 3. Test discovery service
        try:
            # Get first org or create test one
            org = Organization.query.first()
            if org:
                discovery = GrantDiscoveryService()
                discovery_result = discovery.discover_and_persist(org.id, limit=5)
                if discovery_result.get('success'):
                    results['discovery_working'] = True
        except Exception as e:
            results['errors'].append(f"Discovery error: {str(e)}")
        
        # 4. Count total grants
        results['total_grants_in_db'] = Grant.query.count()
        
        # Summary
        results['summary'] = {
            'status': 'success' if results['candid_api'] else 'partial',
            'message': f"Pipeline test complete. Imported {results['grants_imported']} grants. Total in DB: {results['total_grants_in_db']}"
        }
        
    except Exception as e:
        results['errors'].append(str(e))
        results['summary'] = {'status': 'error', 'message': str(e)}
    
    return jsonify(results)

@test_integration_bp.route('/api/test/grant-stats', methods=['GET'])
def get_grant_stats():
    """Get current grant statistics"""
    try:
        stats = {
            'total_grants': Grant.query.count(),
            'by_source': {},
            'by_status': {},
            'recent_grants': []
        }
        
        # Count by source
        sources = db.session.query(Grant.source_name, db.func.count(Grant.id)).group_by(Grant.source_name).all()
        stats['by_source'] = {s[0] or 'Unknown': s[1] for s in sources}
        
        # Count by status
        statuses = db.session.query(Grant.status, db.func.count(Grant.id)).group_by(Grant.status).all()
        stats['by_status'] = {s[0] or 'Unknown': s[1] for s in statuses}
        
        # Get 5 most recent grants
        recent = Grant.query.order_by(Grant.created_at.desc()).limit(5).all()
        stats['recent_grants'] = [
            {
                'title': g.title,
                'funder': g.funder,
                'source': g.source_name,
                'created': g.created_at.isoformat() if g.created_at else None
            }
            for g in recent
        ]
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500