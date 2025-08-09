"""
API Integration endpoints for external data sources
"""

from flask import Blueprint, jsonify, request, session
import logging
from app.services.apiManager import api_manager
from app import db
from app.models.grant import Grant
from datetime import datetime

logger = logging.getLogger(__name__)

# Create Blueprint
integration_bp = Blueprint('integration', __name__)

@integration_bp.route('/api/integration/sources', methods=['GET'])
def get_available_sources():
    """Get list of all available data sources and their status"""
    try:
        sources = []
        for source_id, config in api_manager.sources.items():
            sources.append({
                'id': source_id,
                'name': config.get('name'),
                'enabled': config.get('enabled', False),
                'description': config.get('description', ''),
                'supports': config.get('supports', []),
                'hasApiKey': bool(config.get('api_key'))
            })
        
        return jsonify({
            'success': True,
            'sources': sources
        })
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integration_bp.route('/api/integration/search', methods=['POST'])
def search_grants():
    """Search for grants across all enabled sources"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        filters = data.get('filters', {})
        sources = data.get('sources', None)  # Optional: specific sources to search
        
        # If specific sources requested, temporarily enable only those
        if sources:
            original_states = {}
            for source_id in api_manager.sources:
                original_states[source_id] = api_manager.sources[source_id]['enabled']
                api_manager.sources[source_id]['enabled'] = source_id in sources
        
        # Search across sources
        grants = api_manager.search_opportunities(query, filters)
        
        # Restore original source states if we changed them
        if sources:
            for source_id, state in original_states.items():
                api_manager.sources[source_id]['enabled'] = state
        
        return jsonify({
            'success': True,
            'grants': grants,
            'total': len(grants)
        })
        
    except Exception as e:
        logger.error(f"Error searching grants: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integration_bp.route('/api/integration/fetch/<source_name>', methods=['GET'])
def fetch_from_source(source_name):
    """Fetch grants from a specific source"""
    try:
        params = {
            'limit': int(request.args.get('limit', 25)),
            'query': request.args.get('query', ''),
            'category': request.args.get('category')
        }
        
        grants = api_manager.get_grants_from_source(source_name, params)
        
        return jsonify({
            'success': True,
            'source': source_name,
            'grants': grants,
            'total': len(grants)
        })
        
    except Exception as e:
        logger.error(f"Error fetching from {source_name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integration_bp.route('/api/integration/grant/<grant_id>', methods=['GET'])
def get_grant_details(grant_id):
    """Get detailed information about a specific grant"""
    try:
        source = request.args.get('source')
        grant = api_manager.fetch_grant_details(grant_id, source)
        
        if grant:
            return jsonify({
                'success': True,
                'grant': grant
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Grant not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching grant details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integration_bp.route('/api/integration/import', methods=['POST'])
def import_grants():
    """Import grants from external sources into the database"""
    try:
        data = request.get_json()
        grants_to_import = data.get('grants', [])
        org_id = session.get('org_id', 'org-001')
        
        imported_count = 0
        for grant_data in grants_to_import:
            try:
                # Check if grant already exists
                existing = Grant.query.filter_by(
                    org_id=org_id,
                    title=grant_data.get('title'),
                    funder=grant_data.get('funder')
                ).first()
                
                if not existing:
                    # Handle date fields
                    deadline = grant_data.get('deadline')
                    if deadline and isinstance(deadline, str):
                        try:
                            deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                        except:
                            deadline = None
                    
                    grant = Grant(
                        org_id=org_id,
                        title=grant_data.get('title'),
                        funder=grant_data.get('funder'),
                        description=grant_data.get('description'),
                        amount_min=grant_data.get('amount_min'),
                        amount_max=grant_data.get('amount_max'),
                        deadline=deadline,
                        link=grant_data.get('link'),
                        source_name=grant_data.get('source'),
                        source_url=grant_data.get('source_url'),
                        tags=grant_data.get('tags', []),
                        status='discovered'
                    )
                    db.session.add(grant)
                    imported_count += 1
                    
            except Exception as e:
                logger.error(f"Error importing grant: {e}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'imported': imported_count,
            'message': f'Successfully imported {imported_count} grants'
        })
        
    except Exception as e:
        logger.error(f"Error importing grants: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integration_bp.route('/api/integration/configure', methods=['POST'])
def configure_source():
    """Configure a data source (enable/disable, add API key)"""
    try:
        data = request.get_json()
        source_id = data.get('source_id')
        
        if not source_id or source_id not in api_manager.sources:
            return jsonify({'success': False, 'error': 'Invalid source ID'}), 400
        
        # Update configuration
        if 'enabled' in data:
            api_manager.sources[source_id]['enabled'] = data['enabled']
        
        if 'api_key' in data:
            api_manager.sources[source_id]['api_key'] = data['api_key']
            # Enable source if API key provided
            if data['api_key']:
                api_manager.sources[source_id]['enabled'] = True
        
        return jsonify({
            'success': True,
            'message': f'Source {source_id} configured successfully'
        })
        
    except Exception as e:
        logger.error(f"Error configuring source: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@integration_bp.route('/api/integration/test/<source_name>', methods=['GET'])
def test_source_connection(source_name):
    """Test connection to a specific data source"""
    try:
        # Try to fetch a small number of grants to test the connection
        test_params = {'limit': 1}
        grants = api_manager.get_grants_from_source(source_name, test_params)
        
        return jsonify({
            'success': True,
            'connected': len(grants) > 0,
            'message': f'Successfully connected to {source_name}' if grants else f'Could not fetch data from {source_name}'
        })
        
    except Exception as e:
        logger.error(f"Error testing source {source_name}: {e}")
        return jsonify({
            'success': False,
            'connected': False,
            'error': str(e)
        }), 500