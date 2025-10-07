from flask import Blueprint, request, jsonify, current_app
from services.api_service import api_service
from models.grant import GrantOpportunity
from app import db
from utils.caching import cached
from utils.error_handlers import APIError
from datetime import datetime

socrata_bp = Blueprint('socrata', __name__)

@socrata_bp.route('/portals', methods=['GET'])
def get_portals():
    """Get list of available Socrata data portals"""
    portals = current_app.config.get('SOCRATA_PORTALS', [])

    return jsonify({
        'status': 'success',
        'data': portals
    })

@socrata_bp.route('/local-grants/<portal>', methods=['GET'])
@cached(timeout=3600)
def get_local_grants(portal):
    """
    Get grant data from a specific Socrata portal

    Path parameter:
    - portal: Socrata portal domain (e.g., data.ny.gov)

    Query parameters:
    - dataset_id: Dataset ID (required)
    - query: SoQL query string
    - limit: Results per page (default: 25, max: 1000)
    - offset: Pagination offset (default: 0)
    """
    try:
        # Validate portal
        portals = current_app.config.get('SOCRATA_PORTALS', [])
        if portal not in portals:
            raise APIError(f"Invalid portal: {portal}. Use /api/socrata/portals to get available portals.", status_code=400)

        # Get query parameters
        dataset_id = request.args.get('dataset_id')
        if not dataset_id:
            raise APIError("dataset_id is required", status_code=400)

        query = request.args.get('query', '')
        limit = min(int(request.args.get('limit', 25)), 1000)  # Cap at 1000
        offset = int(request.args.get('offset', 0))

        # Construct query parameters
        params = {
            '$limit': limit,
            '$offset': offset
        }

        # Add SoQL query if provided
        if query:
            params['$query'] = query
        else:
            # Default query to find grants
            params['$where'] = "LOWER(title) LIKE '%grant%' OR LOWER(description) LIKE '%grant%'"
            params['$order'] = 'created_at DESC'

        # Get app token if available
        app_token = current_app.config.get('SOCRATA_TOKEN')
        headers = {'Accept': 'application/json'}

        if app_token:
            headers['X-App-Token'] = app_token

        # Make API request
        api_url = f"https://{portal}/resource/{dataset_id}.json"

        response = api_service.make_request('GET', api_url, headers=headers, params=params)
        data = response.json()

        # Process and format the results
        grants = []
        for item in data:
            # Map fields to a common format
            # Note: Field names vary between datasets, so we need to handle different possibilities
            grant = {
                'title': item.get('title', item.get('name', item.get('grant_title', 'Untitled Grant'))),
                'description': item.get('description', item.get('summary', item.get('grant_description', ''))),
                'amount': item.get('amount', item.get('award_amount', item.get('grant_amount'))),
                'agency': item.get('agency', item.get('department', item.get('organization'))),
                'open_date': item.get('start_date', item.get('open_date', item.get('issue_date'))),
                'close_date': item.get('end_date', item.get('close_date', item.get('deadline'))),
                'eligibility': item.get('eligibility', item.get('eligible_applicants', '')),
                'url': item.get('website', item.get('url', item.get('link'))),
                'source_data': item  # Include all original data
            }
            grants.append(grant)

        # Return formatted response
        return jsonify({
            'status': 'success',
            'data': grants,
            'metadata': {
                'portal': portal,
                'dataset_id': dataset_id,
                'limit': limit,
                'offset': offset,
                'count': len(grants)
            }
        })

    except Exception as e:
        raise APIError(f"Error fetching local grants: {str(e)}", status_code=500)

@socrata_bp.route('/datasets/<portal>', methods=['GET'])
@cached(timeout=86400)  # Cache for 1 day
def get_datasets(portal):
    """
    Get datasets from a specific Socrata portal

    Path parameter:
    - portal: Socrata portal domain (e.g., data.ny.gov)

    Query parameters:
    - search: Search term (default: 'grant funding')
    - limit: Results per page (default: 10, max: 100)
    - offset: Pagination offset (default: 0)
    """
    try:
        # Validate portal
        portals = current_app.config.get('SOCRATA_PORTALS', [])
        if portal not in portals:
            raise APIError(f"Invalid portal: {portal}. Use /api/socrata/portals to get available portals.", status_code=400)

        # Get query parameters
        search = request.args.get('search', 'grant funding')
        limit = min(int(request.args.get('limit', 10)), 100)  # Cap at 100
        offset = int(request.args.get('offset', 0))

        # Construct query parameters
        params = {
            'q': search,
            'limit': limit,
            'offset': offset
        }

        # Get app token if available
        app_token = current_app.config.get('SOCRATA_TOKEN')
        headers = {'Accept': 'application/json'}

        if app_token:
            headers['X-App-Token'] = app_token

        # Make API request
        api_url = f"https://{portal}/api/catalog/v1"

        response = api_service.make_request('GET', api_url, headers=headers, params=params)
        data = response.json()

        # Process and format the results
        datasets = []
        for item in data.get('results', []):
            resource = item.get('resource', {})
            dataset = {
                'id': resource.get('id'),
                'name': resource.get('name'),
                'description': resource.get('description'),
                'category': resource.get('category'),
                'type': resource.get('type'),
                'updated_at': resource.get('updatedAt'),
                'created_at': resource.get('createdAt'),
                'permalink': resource.get('permalink')
            }
            datasets.append(dataset)

        # Return formatted response
        return jsonify({
            'status': 'success',
            'data': datasets,
            'metadata': {
                'portal': portal,
                'limit': limit,
                'offset': offset,
                'count': len(datasets),
                'total': data.get('resultSetSize', 0)
            }
        })

    except Exception as e:
        raise APIError(f"Error fetching datasets: {str(e)}", status_code=500)

@socrata_bp.route('/local-grants/<portal>/sync', methods=['POST'])
def sync_local_grants(portal):
    """
    Sync grants from a Socrata portal to the local database
    This endpoint should be secured in production

    Path parameter:
    - portal: Socrata portal domain (e.g., data.ny.gov)

    Query parameters:
    - dataset_id: Dataset ID (required)
    - query: SoQL query string
    - limit: Max number of records to sync (default: 500, max: 1000)
    """
    try:
        # Validate portal
        portals = current_app.config.get('SOCRATA_PORTALS', [])
        if portal not in portals:
            raise APIError(f"Invalid portal: {portal}. Use /api/socrata/portals to get available portals.", status_code=400)

        # Get query parameters
        dataset_id = request.args.get('dataset_id')
        if not dataset_id:
            raise APIError("dataset_id is required", status_code=400)

        query = request.args.get('query', '')
        limit = min(int(request.args.get('limit', 500)), 1000)  # Cap at 1000

        # Construct query parameters
        params = {
            '$limit': limit
        }

        # Add SoQL query if provided
        if query:
            params['$query'] = query
        else:
            # Default query to find grants
            params['$where'] = "LOWER(title) LIKE '%grant%' OR LOWER(description) LIKE '%grant%'"
            params['$order'] = 'created_at DESC'

        # Get app token if available
        app_token = current_app.config.get('SOCRATA_TOKEN')
        headers = {'Accept': 'application/json'}

        if app_token:
            headers['X-App-Token'] = app_token

        # Make API request
        api_url = f"https://{portal}/resource/{dataset_id}.json"

        response = api_service.make_request('GET', api_url, headers=headers, params=params)
        data = response.json()

        count = 0
        for item in data:
            # Create a unique source_id
            source_id = f"{portal}_{dataset_id}_{item.get('id', hash(str(item)))}"

            # Check if grant already exists
            existing = GrantOpportunity.query.filter_by(
                source=f"socrata.{portal}",
                source_id=source_id
            ).first()

            if not existing:
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
                                open_date = datetime.strptime(open_date_str, fmt)
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
                                close_date = datetime.strptime(close_date_str, fmt)
                                break
                            except ValueError:
                                continue
                    except:
                        pass

                # Create grant opportunity
                grant = GrantOpportunity(
                    title=title[:255],  # Truncate to fit column
                    description=description,
                    agency=agency[:255] if agency else None,  # Truncate to fit column
                    amount=amount,
                    source=f"socrata.{portal}",
                    source_id=source_id,
                    open_date=open_date,
                    close_date=close_date,
                    url=item.get('website', item.get('url', item.get('link', ''))),
                    eligibility=item.get('eligibility', item.get('eligible_applicants', ''))
                )

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
        raise APIError(f"Error syncing grants from {portal}: {str(e)}", status_code=500)