from flask import Blueprint, request, jsonify, current_app
from app.models import Grant
from app import db
from app.services.http_helpers import make_request_with_retry
from functools import lru_cache
from datetime import datetime
from typing import Dict, Any
import os

socrata_bp = Blueprint('socrata', __name__, url_prefix='/api/socrata')

# List of known Socrata portals with grant data
SOCRATA_PORTALS = [
    'data.ny.gov',
    'data.cityofchicago.org',
    'data.sfgov.org',
    'data.michigan.gov',
    'data.atlanta.gov',
    'data.seattle.gov'
]

@socrata_bp.route('/portals', methods=['GET'])
def get_portals():
    """Get list of configured Socrata portals."""
    return jsonify({
        'portals': SOCRATA_PORTALS
    })

@socrata_bp.route('/local-grants/<portal>', methods=['GET'])
@lru_cache(maxsize=128)
def get_local_grants(portal):
    """
    Get local grants from a specific Socrata portal.

    Path parameter:
        - portal: The Socrata portal domain (e.g., 'data.ny.gov')

    Query parameters:
        - dataset_id: The specific dataset ID to query
        - query: SoQL query string
        - limit: Maximum number of results to return (default: 50, max: 1000)
        - offset: Number of results to skip (default: 0)
    """
    # Verify the portal is in allowed list
    if portal not in SOCRATA_PORTALS:
        return jsonify({
            'status': 'error',
            'message': f'Portal {portal} is not in the allowed list'
        }), 400

    # Get parameters
    dataset_id = request.args.get('dataset_id', '')
    query = request.args.get('query', '$where=contains(description,"grant")')
    limit = min(int(request.args.get('limit', 50)), 1000)  # Limit to 1000 max
    offset = int(request.args.get('offset', 0))

    if not dataset_id:
        return jsonify({
            'status': 'error',
            'message': 'dataset_id is required'
        }), 400

    # Build API request
    api_url = f"https://{portal}/resource/{dataset_id}.json"

    params: Dict[str, Any] = {
        '$limit': limit,
        '$offset': offset
    }

    # Add query if provided
    if query:
        for param in query.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value

    # Get app token if available
    app_token = os.environ.get('SOCRATA_TOKEN', '')
    headers = {}
    if app_token:
        headers['X-App-Token'] = app_token

    try:
        # Make API request
        response = make_request_with_retry('GET', api_url, headers=headers, params=params)
        data = response.json()

        # Map the results to a consistent format
        results = []
        for item in data:
            # Create a standard grant format with available fields
            grant = {
                'title': item.get('title', item.get('name', 'Untitled Grant')),
                'description': item.get('description', ''),
                'agency': item.get('agency', item.get('department', '')),
                'amount': item.get('amount', item.get('award_amount', None)),
                'open_date': item.get('start_date', item.get('open_date', '')),
                'close_date': item.get('end_date', item.get('close_date', item.get('due_date', ''))),
                'url': item.get('url', item.get('website', '')),
                'source': f'socrata_{portal}',
                'source_id': item.get('id', ''),
                'raw_data': item  # Include all raw data
            }
            results.append(grant)

        # Add metadata
        response_data = {
            'results': results,
            'portal': portal,
            'dataset_id': dataset_id,
            'limit': limit,
            'offset': offset,
            'count': len(results)
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            'error': f"Failed to retrieve grants from {portal}: {str(e)}",
            'status': 'error'
        }), 500

@socrata_bp.route('/datasets/<portal>', methods=['GET'])
@lru_cache(maxsize=128)
def get_datasets(portal):
    """
    Get available datasets from a specific Socrata portal.

    Path parameter:
        - portal: The Socrata portal domain (e.g., 'data.ny.gov')

    Query parameters:
        - search: Search term to filter datasets
        - limit: Maximum number of results to return (default: 100, max: 1000)
        - offset: Number of results to skip (default: 0)
    """
    # Verify the portal is in allowed list
    if portal not in SOCRATA_PORTALS:
        return jsonify({
            'status': 'error',
            'message': f'Portal {portal} is not in the allowed list'
        }), 400

    # Get parameters
    search = request.args.get('search', 'grant OR funding')
    limit = min(int(request.args.get('limit', 100)), 1000)  # Limit to 1000 max
    offset = int(request.args.get('offset', 0))

    # Build API request
    api_url = f"https://{portal}/api/catalog/v1"

    params = {
        'limit': limit,
        'offset': offset,
        'q': search,
        'only': 'datasets'
    }

    # Get app token if available
    app_token = os.environ.get('SOCRATA_TOKEN', '')
    headers = {}
    if app_token:
        headers['X-App-Token'] = app_token

    try:
        # Make API request
        response = make_request_with_retry('GET', api_url, headers=headers, params=params)
        data = response.json()

        # Extract dataset information
        results = []
        for item in data.get('results', []):
            dataset = {
                'id': item.get('resource', {}).get('id'),
                'name': item.get('resource', {}).get('name'),
                'description': item.get('resource', {}).get('description'),
                'attribution': item.get('resource', {}).get('attribution'),
                'category': item.get('classification', {}).get('domain_category'),
                'created_at': item.get('resource', {}).get('createdAt'),
                'updated_at': item.get('resource', {}).get('updatedAt'),
                'permalink': item.get('permalink')
            }
            results.append(dataset)

        # Add metadata
        response_data = {
            'results': results,
            'portal': portal,
            'limit': limit,
            'offset': offset,
            'count': len(results),
            'total': data.get('resultSetSize', 0)
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            'error': f"Failed to retrieve datasets from {portal}: {str(e)}",
            'status': 'error'
        }), 500

@socrata_bp.route('/local-grants/<portal>/sync', methods=['POST'])
def sync_local_grants(portal):
    """
    Sync grants from a Socrata portal to the local database.
    This endpoint should be secured in production.

    Path parameter:
        - portal: Socrata portal domain (e.g., 'data.ny.gov')

    Query parameters:
        - dataset_id: Dataset ID (required)
        - query: SoQL query string
        - limit: Max number of records to sync (default: 500, max: 1000)
    """
    # Verify the portal is in allowed list
    if portal not in SOCRATA_PORTALS:
        return jsonify({
            'status': 'error',
            'message': f'Portal {portal} is not in the allowed list'
        }), 400

    # Get parameters
    dataset_id = request.args.get('dataset_id')
    if not dataset_id:
        return jsonify({
            'status': 'error',
            'message': 'dataset_id is required'
        }), 400

    query = request.args.get('query', '')
    limit = min(int(request.args.get('limit', 500)), 1000)  # Cap at 1000

    # Build API request
    api_url = f"https://{portal}/resource/{dataset_id}.json"

    params: Dict[str, Any] = {
        '$limit': limit
    }

    # Add query if provided
    if query:
        for param in query.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value
    else:
        # Default query to find grants
        params['$where'] = "LOWER(title) LIKE '%grant%' OR LOWER(description) LIKE '%grant%'"

    # Get app token if available
    app_token = os.environ.get('SOCRATA_TOKEN', '')
    headers = {}
    if app_token:
        headers['X-App-Token'] = app_token

    try:
        # Make API request
        response = make_request_with_retry('GET', api_url, headers=headers, params=params)
        data = response.json()

        count = 0
        for item in data:
            # Create a unique source_id
            source_id = f"{portal}_{dataset_id}_{item.get('id', hash(str(item)))}"

            # Check if grant already exists
            grant_link = item.get('website', item.get('url', item.get('link', '')))
            existing = Grant.query.filter_by(
                source_name=f"Socrata.{portal}",
                link=grant_link
            ).first()

            if not existing and grant_link:
                # Extract and normalize fields
                title = item.get('title', item.get('name', item.get('grant_title', 'Untitled Grant')))
                description = item.get('description', item.get('summary', item.get('grant_description', '')))
                agency = item.get('agency', item.get('department', item.get('organization', '')))

                # Parse amount
                amount = None
                amount_str = item.get('amount', item.get('award_amount', item.get('grant_amount')))
                if amount_str:
                    try:
                        # Clean up amount string
                        if isinstance(amount_str, str):
                            amount_str = amount_str.replace('$', '').replace(',', '')
                        amount = float(amount_str)
                    except (ValueError, TypeError):
                        pass

                # Parse dates
                open_date = None
                close_date = None

                open_date_str = item.get('start_date', item.get('open_date', item.get('issue_date')))
                close_date_str = item.get('end_date', item.get('close_date', item.get('deadline')))

                if open_date_str:
                    try:
                        # Try common date formats
                        date_formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%m/%d/%Y']
                        for fmt in date_formats:
                            try:
                                open_date = datetime.strptime(str(open_date_str), fmt)
                                break
                            except ValueError:
                                continue
                    except:
                        pass

                if close_date_str:
                    try:
                        # Try common date formats
                        date_formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%m/%d/%Y']
                        for fmt in date_formats:
                            try:
                                close_date = datetime.strptime(str(close_date_str), fmt)
                                break
                            except ValueError:
                                continue
                    except:
                        pass

                # Create grant opportunity
                grant = Grant()
                grant.title = title[:255] if title else 'Untitled Grant'
                grant.ai_summary = description[:500] if description else ''
                grant.funder = agency[:255] if agency else 'Local Agency'
                grant.amount_max = amount
                grant.source_name = f"Socrata.{portal}"
                grant.deadline = close_date.date() if close_date else None
                grant.link = grant_link
                grant.source_url = f"https://{portal}/resource/{dataset_id}.json"

                db.session.add(grant)
                count += 1

        # Commit changes
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Successfully synced {count} grants from {portal}',
            'count': count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f"Failed to sync grants from {portal}: {str(e)}",
            'status': 'error'
        }), 500