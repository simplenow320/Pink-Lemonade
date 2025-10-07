from flask import Blueprint, request, jsonify, current_app
from services.api_service import api_service
from models.grant import GrantOpportunity
from models.nonprofit import NonprofitProfile
from app import db
from utils.caching import cached
from utils.error_handlers import APIError
from datetime import datetime, timedelta

sam_bp = Blueprint('sam', __name__)

@sam_bp.route('/opportunities', methods=['GET'])
@cached(timeout=3600)
def get_opportunities():
    """
    Get funding opportunities from SAM.gov API

    Query parameters:
    - keyword: Keyword search term
    - status: Opportunity status (active, archived, etc.)
    - agency: Filter by agency name
    - posted_from: Posted from date (MM/DD/YYYY)
    - posted_to: Posted to date (MM/DD/YYYY)
    - page: Page number (default: 1)
    - size: Results per page (default: 25, max: 100)
    """
    try:
        # Check for API key
        api_key = current_app.config.get('SAM_API_KEY')
        if not api_key:
            raise APIError("SAM.gov API key is not configured", status_code=500)

        # Get query parameters
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', 'active')
        agency = request.args.get('agency', '')
        posted_from = request.args.get('posted_from', '')
        posted_to = request.args.get('posted_to', '')
        page = int(request.args.get('page', 1))
        size = min(int(request.args.get('size', 25)), 100)  # Cap at 100

        # Construct query parameters
        params = {
            'api_key': api_key,
            'limit': size,
            'offset': (page - 1) * size,
            'opportunityStatus': status,
            'ptype': 'g'  # Filter for grants
        }

        if keyword:
            params['keyword'] = keyword

        if agency:
            params['agency'] = agency

        if posted_from:
            params['postedFrom'] = posted_from

        if posted_to:
            params['postedTo'] = posted_to

        # Make API request
        api_url = f"{current_app.config['SAM_API_URL']}/opportunities/v2/search"

        headers = {'X-Api-Key': api_key}

        response = api_service.make_request('GET', api_url, headers=headers, params=params)
        data = response.json()

        # Process and format the results
        opportunities = []
        for item in data.get('opportunitiesData', []):
            opportunity = {
                'notice_id': item.get('noticeId'),
                'opportunity_id': item.get('opportunityId'),
                'title': item.get('title'),
                'department': item.get('department'),
                'sub_tier': item.get('subTier'),
                'office': item.get('office'),
                'posted_date': item.get('postedDate'),
                'close_date': item.get('responseDeadLine'),
                'award_ceiling': item.get('awardCeiling'),
                'award_floor': item.get('awardFloor'),
                'estimated_funding': item.get('estimatedFunding'),
                'naics_code': item.get('naicsCode'),
                'classification_code': item.get('classificationCode'),
                'url': f"https://sam.gov/opp/{item.get('noticeId')}/view"
            }
            opportunities.append(opportunity)

        # Return formatted response
        return jsonify({
            'status': 'success',
            'data': opportunities,
            'metadata': {
                'page': page,
                'size': size,
                'total': data.get('totalRecords', 0)
            }
        })

    except Exception as e:
        raise APIError(f"Error fetching opportunities: {str(e)}", status_code=500)

@sam_bp.route('/entity/<uei>', methods=['GET'])
@cached(timeout=86400)  # Cache for 1 day
def get_entity(uei):
    """
    Get entity information from SAM.gov Entity Management API

    Path parameter:
    - uei: Unique Entity ID
    """
    try:
        # Check for API key
        api_key = current_app.config.get('SAM_API_KEY')
        if not api_key:
            raise APIError("SAM.gov API key is not configured", status_code=500)

        # Make API request
        api_url = f"{current_app.config['SAM_API_URL']}/entity-information/v2/entities/{uei}"

        headers = {'X-Api-Key': api_key}

        response = api_service.make_request('GET', api_url, headers=headers)
        data = response.json()

        # Extract entity data
        entity_data = data.get('entityData', {})

        # Process and format the result
        entity = {
            'uei': uei,
            'legal_business_name': entity_data.get('entityRegistration', {}).get('legalBusinessName'),
            'physical_address': entity_data.get('coreData', {}).get('physicalAddress', {}),
            'mailing_address': entity_data.get('coreData', {}).get('mailingAddress', {}),
            'business_types': entity_data.get('coreData', {}).get('businessTypes', []),
            'status': entity_data.get('entityRegistration', {}).get('registrationStatus'),
            'registration_date': entity_data.get('entityRegistration', {}).get('registrationDate'),
            'expiration_date': entity_data.get('entityRegistration', {}).get('expirationDate')
        }

        return jsonify({
            'status': 'success',
            'data': entity
        })

    except Exception as e:
        raise APIError(f"Error fetching entity details: {str(e)}", status_code=500)

@sam_bp.route('/opportunities/sync', methods=['POST'])
def sync_opportunities():
    """
    Sync opportunities from SAM.gov to the local database
    This endpoint should be secured in production
    """
    try:
        # Check for API key
        api_key = current_app.config.get('SAM_API_KEY')
        if not api_key:
            raise APIError("SAM.gov API key is not configured", status_code=500)

        # Get parameters
        keyword = request.args.get('keyword', 'grant')
        days = int(request.args.get('days', 30))

        # Calculate date range
        from_date = (datetime.now() - timedelta(days=days)).strftime('%m/%d/%Y')

        # Construct query parameters
        params = {
            'api_key': api_key,
            'limit': 100,
            'offset': 0,
            'keyword': keyword,
            'postedFrom': from_date,
            'ptype': 'g'  # Filter for grants
        }

        # Make API request
        api_url = f"{current_app.config['SAM_API_URL']}/opportunities/v2/search"

        headers = {'X-Api-Key': api_key}

        count = 0
        offset = 0
        has_more = True

        while has_more:
            params['offset'] = offset

            response = api_service.make_request('GET', api_url, headers=headers, params=params)
            data = response.json()

            # Process results
            opportunities = data.get('opportunitiesData', [])

            for item in opportunities:
                # Check if opportunity already exists
                notice_id = item.get('noticeId')

                existing = GrantOpportunity.query.filter_by(
                    source='sam.gov',
                    source_id=notice_id
                ).first()

                if not existing:
                    # Parse dates
                    posted_date = None
                    close_date = None

                    if item.get('postedDate'):
                        try:
                            posted_date = datetime.strptime(item.get('postedDate'), '%m/%d/%Y')
                        except ValueError:
                            pass

                    if item.get('responseDeadLine'):
                        try:
                            close_date = datetime.strptime(item.get('responseDeadLine'), '%m/%d/%Y')
                        except ValueError:
                            pass

                    # Determine amount from ceiling or estimated funding
                    amount = item.get('awardCeiling') or item.get('estimatedFunding')

                    # Create new grant opportunity
                    grant = GrantOpportunity(
                        title=item.get('title', '')[:255],
                        description=item.get('description', ''),
                        agency=item.get('department') or item.get('office', ''),
                        amount=amount,
                        opportunity_id=item.get('opportunityId'),
                        source='sam.gov',
                        source_id=notice_id,
                        open_date=posted_date,
                        close_date=close_date,
                        url=f"https://sam.gov/opp/{notice_id}/view"
                    )
                    db.session.add(grant)
                    count += 1

            # Check if there are more results
            total = data.get('totalRecords', 0)
            offset += len(opportunities)
            has_more = offset < total and len(opportunities) > 0

        # Commit changes
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Successfully synced {count} opportunities',
            'count': count
        })

    except Exception as e:
        db.session.rollback()
        raise APIError(f"Error syncing opportunities: {str(e)}", status_code=500)