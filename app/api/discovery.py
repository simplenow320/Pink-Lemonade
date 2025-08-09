"""
Discovery API endpoints for live grant data integration
"""

from flask import Blueprint, jsonify, request, session
import logging
import os
from app.services.apiManager import APIManager

logger = logging.getLogger(__name__)

# Create Blueprint
discovery_bp = Blueprint('discovery', __name__)

# Initialize API Manager
api_manager = APIManager()

@discovery_bp.route('/api/discovery/sources', methods=['GET'])
def get_discovery_sources():
    """Get all available discovery sources and their status"""
    try:
        sources = api_manager.get_enabled_sources()
        
        # Add status information for each source
        sources_info = []
        for source_id, config in sources.items():
            sources_info.append({
                'id': source_id,
                'name': config['name'],
                'description': config['description'],
                'enabled': config['enabled'],
                'supports': config.get('supports', []),
                'rate_limit': config.get('rate_limit', {}),
                'cache_ttl': config.get('cache_ttl', 60)
            })
        
        return jsonify({
            'success': True,
            'sources': sources_info,
            'total_enabled': len(sources_info)
        })
        
    except Exception as e:
        logger.error(f"Error fetching discovery sources: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'sources': []
        }), 500

@discovery_bp.route('/api/discovery/search', methods=['GET'])
def search_opportunities():
    """Search for grant opportunities across all enabled sources"""
    try:
        # Get search parameters
        query = request.args.get('query', 'nonprofit grant')
        limit = int(request.args.get('limit', 25))
        source = request.args.get('source', None)  # Optional: search specific source
        
        # Get data mode
        data_mode = os.environ.get('APP_DATA_MODE', 'MOCK')
        
        if data_mode == 'LIVE':
            # Use API Manager to search live sources
            if source:
                # Search specific source
                results = api_manager.search_grants(source, {
                    'query': query,
                    'limit': limit
                })
            else:
                # Search all enabled sources
                all_results = []
                enabled_sources = api_manager.get_enabled_sources()
                
                for source_id in enabled_sources.keys():
                    try:
                        source_results = api_manager.search_grants(source_id, {
                            'query': query,
                            'limit': limit // len(enabled_sources) + 5  # Distribute across sources
                        })
                        all_results.extend(source_results)
                    except Exception as e:
                        logger.warning(f"Error searching {source_id}: {e}")
                        continue
                
                # Sort by relevance/date and limit results
                results = sorted(all_results, key=lambda x: x.get('deadline', ''), reverse=True)[:limit]
        else:
            # MOCK mode: return empty results or placeholder
            results = []
        
        return jsonify({
            'success': True,
            'opportunities': results,
            'total': len(results),
            'dataMode': data_mode,
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Error searching opportunities: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'opportunities': []
        }), 500

@discovery_bp.route('/api/discovery/run', methods=['POST'])
def run_discovery():
    """Run discovery across all sources and return new opportunities"""
    try:
        data_mode = os.environ.get('APP_DATA_MODE', 'MOCK')
        
        if data_mode == 'LIVE':
            # Get organization context for targeted discovery
            org_id = session.get('org_id', 'org-001')
            
            # Run discovery with organization context
            new_opportunities = []
            enabled_sources = api_manager.get_enabled_sources()
            
            # Search each enabled source
            for source_id in enabled_sources.keys():
                try:
                    # Use broad search terms for discovery
                    search_terms = ['nonprofit grant', 'community funding', 'education grant', 'faith-based grant']
                    
                    for term in search_terms:
                        source_results = api_manager.search_grants(source_id, {
                            'query': term,
                            'limit': 10
                        })
                        new_opportunities.extend(source_results)
                        
                except Exception as e:
                    logger.warning(f"Error in discovery for {source_id}: {e}")
                    continue
            
            # Remove duplicates based on title similarity
            unique_opportunities = []
            seen_titles = set()
            
            for opp in new_opportunities:
                title_lower = opp.get('title', '').lower()
                if title_lower not in seen_titles:
                    unique_opportunities.append(opp)
                    seen_titles.add(title_lower)
            
            # Limit to reasonable number
            discovery_results = unique_opportunities[:50]
        else:
            # MOCK mode: return empty discovery
            discovery_results = []
        
        return jsonify({
            'success': True,
            'newOpportunities': discovery_results,
            'total': len(discovery_results),
            'dataMode': data_mode,
            'timestamp': api_manager._get_current_timestamp()
        })
        
    except Exception as e:
        logger.error(f"Error running discovery: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'newOpportunities': []
        }), 500

@discovery_bp.route('/api/discovery/status', methods=['GET'])
def get_discovery_status():
    """Get current discovery system status"""
    try:
        enabled_sources = api_manager.get_enabled_sources()
        data_mode = os.environ.get('APP_DATA_MODE', 'MOCK')
        
        # Test connectivity to each source
        source_status = {}
        for source_id, config in enabled_sources.items():
            try:
                # Simple connectivity test
                test_result = api_manager.search_grants(source_id, {
                    'query': 'test',
                    'limit': 1
                })
                source_status[source_id] = {
                    'status': 'online',
                    'name': config['name'],
                    'last_tested': api_manager._get_current_timestamp()
                }
            except Exception as e:
                source_status[source_id] = {
                    'status': 'error',
                    'name': config['name'],
                    'error': str(e),
                    'last_tested': api_manager._get_current_timestamp()
                }
        
        return jsonify({
            'success': True,
            'dataMode': data_mode,
            'sources': source_status,
            'totalSources': len(enabled_sources),
            'onlineSources': sum(1 for s in source_status.values() if s['status'] == 'online')
        })
        
    except Exception as e:
        logger.error(f"Error getting discovery status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500