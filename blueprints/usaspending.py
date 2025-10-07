from flask import Blueprint, request, jsonify, current_app
from services.api_service import api_service
from models.grant import GrantOpportunity
from app import db
from utils.caching import cached
from utils.error_handlers import APIError
from datetime import datetime
import time

usaspending_bp = Blueprint('usaspending', __name__)

@usaspending_bp.route('/awards', methods=['GET'])
@cached(timeout=3600)
def get_awards():
    """
    Retrieve federal awards data from USAspending.gov API

    Query parameters:
    - fiscal_year: Fiscal year (e.g., 2023)
    - recipient_name: Filter by recipient name
    - amount_min: Minimum award amount
    - amount_max: Maximum award amount
    - agency_id: Filter by agency ID
    - page: Page number (default: 1)
    - limit: Results per page (default: 50, max: 100)
    """
    try:
        # Get query parameters
        fiscal_year = request.args.get('fiscal_year')
        recipient_name = request.args.get('recipient_name')
        amount_min = request.args.get('amount_min')
        amount_max = request.args.get('amount_max')
        agency_id = request.args.get('agency_id')
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100

        # Build API request
        api_url = f"{current_app.config['USASPENDING_API_URL']}/search/spending_by_award/"

        # Construct filters
        filters = {"award_type_codes": ["02", "03", "04", "05"]}  # Grant award types

        if fiscal_year:
            filters["time_period"] = [
                {
                    "start_date": f"{fiscal_year}-10-01", 
                    "end_date": f"{int(fiscal_year)+1}-09-30"
                }
            ]

        if recipient_name:
            filters["recipient_search_text"] = [recipient_name]

        if amount_min or amount_max:
            amount_filter = {}
            if amount_min:
                amount_filter["lower_bound"] = float(amount_min)
            if amount_max:
                amount_filter["upper_bound"] = float(amount_max)
            filters["award_amounts"] = [amount_filter]

        if agency_id:
            filters["agencies"] = [{"type": "awarding", "tier": "toptier", "name": agency_id}]

        # Prepare the request payload
        payload = {
            "filters": filters,
            "fields": [
                "Award ID", 
                "Recipient Name", 
                "Award Amount",
                "Awarding Agency",
                "Award Type",
                "Description",
                "Start Date",
                "End Date"
            ],
            "page": page,
            "limit": limit,
            "sort": "Award Amount",
            "order": "desc"
        }

        # Make API request
        response = api_service.make_request('POST', api_url, json=payload)
        data = response.json()

        # Process and format the results
        results = []
        for item in data.get('results', []):
            award = {
                'award_id': item.get('Award ID'),
                'recipient_name': item.get('Recipient Name'),
                'award_amount': item.get('Award Amount'),
                'awarding_agency': item.get('Awarding Agency'),
                'award_type': item.get('Award Type'),
                'description': item.get('Description'),
                'start_date': item.get('Start Date'),
                'end_date': item.get('End Date')
            }
            results.append(award)

        # Return formatted response
        return jsonify({
            'status': 'success',
            'data': results,
            'metadata': {
                'page': page,
                'limit': limit,
                'total': data.get('page_metadata', {}).get('total', 0),
                'count': len(results)
            }
        })

    except Exception as e:
        raise APIError(f"Error fetching awards: {str(e)}", status_code=500)

@usaspending_bp.route('/award/<award_id>', methods=['GET'])
@cached(timeout=86400)  # Cache for 1 day
def get_award_detail(award_id):
    """Get details for a specific award by ID"""
    try:
        # Make API request
        api_url = f"{current_app.config['USASPENDING_API_URL']}/awards/{award_id}/"

        response = api_service.make_request('GET', api_url)
        data = response.json()

        return jsonify({
            'status': 'success',
            'data': data
        })

    except Exception as e:
        raise APIError(f"Error fetching award details: {str(e)}", status_code=500)

@usaspending_bp.route('/awards/sync', methods=['POST'])
def sync_awards():
    """
    Sync awards data to the local database
    This endpoint should be secured in production
    """
    try:
        # Get parameters
        fiscal_year = request.args.get('fiscal_year', datetime.now().year)

        # Build API request
        api_url = f"{current_app.config['USASPENDING_API_URL']}/search/spending_by_award/"

        # Construct filters
        filters = {
            "award_type_codes": ["02", "03", "04", "05"],  # Grant award types
            "time_period": [
                {
                    "start_date": f"{fiscal_year}-10-01", 
                    "end_date": f"{int(fiscal_year)+1}-09-30"
                }
            ]
        }

        # Prepare the request payload
        payload = {
            "filters": filters,
            "fields": [
                "Award ID", 
                "Recipient Name", 
                "Award Amount",
                "Awarding Agency",
                "Award Type",
                "Description",
                "Start Date",
                "End Date"
            ],
            "page": 1,
            "limit": 100,
            "sort": "Award Amount",
            "order": "desc"
        }

        count = 0
        page = 1
        has_more = True

        while has_more:
            payload["page"] = page

            # Respect rate limits
            if page > 1:
                time.sleep(1)

            # Make API request
            response = api_service.make_request('POST', api_url, json=payload)
            data = response.json()

            # Process results
            for item in data.get('results', []):
                award_id = item.get('Award ID')

                # Check if award already exists
                existing = GrantOpportunity.query.filter_by(
                    source='usaspending',
                    source_id=award_id
                ).first()

                if not existing:
                    # Parse dates
                    start_date = None
                    end_date = None

                    if item.get('Start Date'):
                        try:
                            start_date = datetime.strptime(item.get('Start Date'), '%Y-%m-%d')
                        except ValueError:
                            pass

                    if item.get('End Date'):
                        try:
                            end_date = datetime.strptime(item.get('End Date'), '%Y-%m-%d')
                        except ValueError:
                            pass

                    # Create new grant opportunity
                    grant = GrantOpportunity(
                        title=item.get('Description', '')[:255],
                        description=item.get('Description', ''),
                        agency=item.get('Awarding Agency', ''),
                        amount=item.get('Award Amount'),
                        opportunity_id=award_id,
                        source='usaspending',
                        source_id=award_id,
                        open_date=start_date,
                        close_date=end_date,
                        url=f"https://www.usaspending.gov/award/{award_id}"
                    )
                    db.session.add(grant)
                    count += 1

            # Check if there are more pages
            total = data.get('page_metadata', {}).get('total', 0)
            has_more = page * payload["limit"] < total
            page += 1

        # Commit changes to the database
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Successfully synced {count} awards',
            'count': count
        })

    except Exception as e:
        db.session.rollback()
        raise APIError(f"Error syncing awards: {str(e)}", status_code=500)