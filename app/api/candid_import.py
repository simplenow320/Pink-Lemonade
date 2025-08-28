"""
Candid Grant Import API
Imports real grants from Candid API into database
"""
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from app import db
from app.models import Grant
from app.services.candid_client import get_grants_client
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

candid_import_bp = Blueprint('candid_import', __name__)

@candid_import_bp.route('/api/discovery/import-candid', methods=['POST'])
@cross_origin()
def import_candid_grants():
    """Import grants from Candid API into database"""
    try:
        data = request.get_json() or {}
        query = data.get('query', 'education health youth')
        limit = data.get('limit', 50)
        
        # Get Candid client
        client = get_grants_client()
        
        # Fetch grants from Candid
        logger.info(f"Fetching grants from Candid API with query: {query}")
        transactions = client.transactions(query=query, page=1)
        
        if not transactions:
            return jsonify({
                'success': False,
                'error': 'No grants found',
                'grants_imported': 0
            })
        
        # Import grants to database
        imported_count = 0
        for transaction in transactions[:limit]:
            try:
                # Check if grant already exists by title and funder
                title = f"{transaction.get('funder_name', 'Unknown')} - {transaction.get('recipient_name', 'Grant')}"
                existing = Grant.query.filter_by(
                    title=title,
                    funder=transaction.get('funder_name', 'Unknown')
                ).first()
                
                if existing:
                    # Update existing grant
                    amount = transaction.get('amount', 0) or 0
                    if amount > 0:
                        existing.amount_min = amount
                        existing.amount_max = amount
                    existing.geography = f"{transaction.get('recip_city', '')}, {transaction.get('recip_state', '')}"
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new grant
                    amount = transaction.get('amount', 0) or 0
                    grant = Grant(
                        title=title,
                        funder=transaction.get('funder_name', 'Unknown'),
                        amount_min=amount if amount > 0 else 1000,  # Default min
                        amount_max=amount if amount > 0 else 100000,  # Default max
                        eligibility=f"Organizations in {transaction.get('recip_city', '')}, {transaction.get('recip_state', '')}",
                        geography=f"{transaction.get('recip_city', '')}, {transaction.get('recip_state', '')}",
                        source_name='Candid Grants API',
                        source_url='https://candid.org',
                        status='idea',  # Use valid status
                        deadline=None,  # Candid doesn't provide deadlines
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(grant)
                    imported_count += 1
                    
            except Exception as e:
                logger.error(f"Error importing grant: {e}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        # Get total count
        total_grants = Grant.query.filter_by(source_name='Candid Grants API').count()
        
        return jsonify({
            'success': True,
            'grants_imported': imported_count,
            'total_candid_grants': total_grants,
            'message': f'Successfully imported {imported_count} new grants from Candid'
        })
        
    except Exception as e:
        logger.error(f"Error importing Candid grants: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'grants_imported': 0
        }), 500

@candid_import_bp.route('/api/candid/fetch-live', methods=['GET'])
@cross_origin()
def fetch_live_grants():
    """Fetch and display live grants from Candid without saving"""
    try:
        query = request.args.get('q', 'education')
        
        # Get Candid client
        client = get_grants_client()
        
        # Fetch grants
        transactions = client.transactions(query=query, page=1)
        
        # Format for display
        grants = []
        for t in transactions[:20]:
            grants.append({
                'title': f"{t.get('funder_name', 'Unknown')} Grant",
                'funder': t.get('funder_name', 'Unknown'),
                'recipient': t.get('recipient_name', ''),
                'amount': t.get('amount', 0),
                'location': f"{t.get('recip_city', '')}, {t.get('recip_state', '')}",
                'year': t.get('grant_date', ''),
                'source': 'Candid API (Live)'
            })
        
        return jsonify({
            'success': True,
            'grants': grants,
            'count': len(grants),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Error fetching live grants: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500