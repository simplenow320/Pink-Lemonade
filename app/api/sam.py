from flask import Blueprint, request, jsonify, current_app
from app.models import Grant, Organization
from app import db
from app.services.http_helpers import make_request_with_retry
from functools import lru_cache
from datetime import datetime, timedelta
import os

sam_bp = Blueprint('sam', __name__, url_prefix='/api/sam')

@sam_bp.route('/opportunities', methods=['GET'])
@lru_cache(maxsize=128)
def get_opportunities():
    """
    Get funding opportunities from SAM.gov.

    Query parameters:
        - keyword: Keyword search term
        - status: Status filter ('active', 'archived', 'cancelled')
        - agency: Filter by agency name
        - postedFrom: Posted from date (YYYY-MM-DD)
        - postedTo: Posted to date (YYYY-MM-DD)
        - page: Page number (default: 1)
        - size: Results per page (default: 25, max: 100)
    """
    # Get API key - use environment variable
    api_key = os.environ.get('SAM_API_KEY', 'SAM-8eaf035c-b5cb-402a-8933-5971c25c156c')

    # Process query parameters
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', 'active')
    agency = request.args.get('agency', '')
    posted_from = request.args.get('postedFrom', '')
    posted_to = request.args.get('postedTo', '')
    page = int(request.args.get('page', 1))
    size = min(int(request.args.get('size', 25)), 100)  # Limit to 100 max

    # Build API request
    api_url = "https://api.sam.gov/opportunities/v2/search"

    params = {
        'limit': size,
        'offset': (page - 1) * size,
        'postedFrom': posted_from,
        'postedTo': posted_to,
        'keyword': keyword,
        'opportunityStatus': status,
        'ptype': 'g'  # Filter for grants
    }

    # Add agency filter if provided
    if agency:
        params['agency'] = agency

    # Remove empty params
    params = {k: v for k, v in params.items() if v}

    try:
        # Make API request
        headers = {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        }

        response = make_request_with_retry('GET', api_url, headers=headers, params=params)
        data = response.json()

        # Map the results to a consistent format
        results = []
        for item in data.get('opportunitiesData', []):
            opportunity = {
                'title': item.get('title'),
                'opportunity_id': item.get('noticeId'),
                'agency': item.get('department') or item.get('office'),
                'posted_date': item.get('postedDate'),
                'due_date': item.get('responseDeadLine'),
                'status': item.get('status'),
                'description': item.get('description'),
                'category': item.get('classificationCode'),
                'naics_code': item.get('naicsCode'),
                'award_ceiling': item.get('awardCeiling'),
                'award_floor': item.get('awardFloor'),
                'url': f"https://sam.gov/opp/{item.get('noticeId')}/view",
                'source': 'sam.gov'
            }
            results.append(opportunity)

        # Add pagination info
        response_data = {
            'results': results,
            'page': page,
            'size': size,
            'total_records': data.get('totalRecords', 0)
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            'error': f"Failed to retrieve opportunities: {str(e)}",
            'status': 'error'
        }), 500

@sam_bp.route('/entity/<uei>', methods=['GET'])
@lru_cache(maxsize=128)
def get_entity(uei):
    """
    Get entity information from SAM.gov Entity Management API.

    Path parameter:
        - uei: Unique Entity ID
    """
    # Get API key
    api_key = os.environ.get('SAM_API_KEY', 'SAM-8eaf035c-b5cb-402a-8933-5971c25c156c')

    try:
        # Build API request
        api_url = f"https://api.sam.gov/entity-information/v2/entities/{uei}"

        headers = {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        }

        # Make API request
        response = make_request_with_retry('GET', api_url, headers=headers)
        data = response.json()

        # Extract entity data
        entity_data = data.get('entityData', {})
        entity_registration = entity_data.get('entityRegistration', {})
        core_data = entity_data.get('coreData', {})

        # Map the response to a consistent format
        entity = {
            'uei': entity_registration.get('ueiSAM'),
            'legal_business_name': entity_registration.get('legalBusinessName'),
            'dba_name': entity_registration.get('dbaName'),
            'physical_address': core_data.get('physicalAddress', {}),
            'mailing_address': core_data.get('mailingAddress', {}),
            'business_type': core_data.get('businessTypes', []),
            'status': entity_registration.get('registrationStatus'),
            'expiration_date': entity_registration.get('registrationExpirationDate'),
            'activation_date': entity_registration.get('registrationActivationDate'),
            'renewal_date': entity_registration.get('registrationRenewalDate'),
            'last_updated': entity_registration.get('lastUpdateDate')
        }

        return jsonify(entity)

    except Exception as e:
        return jsonify({
            'error': f"Failed to retrieve entity information: {str(e)}",
            'status': 'error'
        }), 500

@sam_bp.route('/opportunities/sync', methods=['POST'])
def sync_opportunities():
    """
    Sync opportunities from SAM.gov to the local database.
    This is an administrative endpoint and should be protected.
    """
    # Get API key
    api_key = os.environ.get('SAM_API_KEY', 'SAM-8eaf035c-b5cb-402a-8933-5971c25c156c')

    try:
        keyword = request.args.get('keyword', 'grant')
        days = int(request.args.get('days', 30))

        # Calculate date range
        posted_from = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')

        # Build API request
        api_url = "https://api.sam.gov/opportunities/v2/search"

        params = {
            'limit': 100,
            'offset': 0,
            'keyword': keyword,
            'postedFrom': posted_from,
            'opportunityStatus': 'active',
            'ptype': 'g'  # Filter for grants
        }

        headers = {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        }

        count = 0
        has_more = True
        offset = 0

        while has_more:
            params['offset'] = offset

            # Make API request
            response = make_request_with_retry('GET', api_url, headers=headers, params=params)
            data = response.json()

            for item in data.get('opportunitiesData', []):
                # Check if opportunity already exists
                notice_id = item.get('noticeId')
                grant_url = f"https://sam.gov/opp/{notice_id}/view"
                existing = Grant.query.filter_by(
                    source_name='SAM.gov',
                    link=grant_url
                ).first()

                if not existing:
                    # Parse dates
                    try:
                        posted_date = datetime.strptime(item.get('postedDate', ''), '%Y/%m/%d') if item.get('postedDate') else None
                        close_date = datetime.strptime(item.get('responseDeadLine', ''), '%Y/%m/%d') if item.get('responseDeadLine') else None
                    except ValueError:
                        posted_date = None
                        close_date = None

                    # Create new grant opportunity record
                    grant = Grant()
                    grant.title = item.get('title') or 'Federal Opportunity'
                    grant.ai_summary = item.get('description') or ''
                    grant.funder = item.get('department') or item.get('office') or 'Federal Agency'
                    grant.source_name = 'SAM.gov'
                    grant.source_url = grant_url
                    grant.deadline = close_date
                    grant.amount_max = item.get('awardCeiling')
                    grant.link = grant_url
                    db.session.add(grant)
                    count += 1

            # Check pagination
            total_records = data.get('totalRecords', 0)
            offset += len(data.get('opportunitiesData', []))
            has_more = offset < total_records and len(data.get('opportunitiesData', [])) > 0

        # Commit changes
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Synced {count} opportunities from SAM.gov',
            'count': count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f"Failed to sync opportunities: {str(e)}",
            'status': 'error'
        }), 500