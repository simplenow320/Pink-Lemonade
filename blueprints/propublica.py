from flask import Blueprint, request, jsonify, current_app
from services.api_service import api_service
from models.nonprofit import NonprofitProfile
from app import db
from utils.caching import cached
from utils.error_handlers import APIError
from datetime import datetime

propublica_bp = Blueprint('propublica', __name__)

@propublica_bp.route('/nonprofit/<ein>', methods=['GET'])
@cached(timeout=86400)  # Cache for 1 day
def get_nonprofit_by_ein(ein):
    """
    Get nonprofit information by EIN from ProPublica API

    Path parameter:
    - ein: Employer Identification Number
    """
    try:
        api_url = f"{current_app.config['PROPUBLICA_API_URL']}/organizations/{ein}.json"

        # Make API request
        response = api_service.make_request('GET', api_url)
        data = response.json()

        # Extract organization data
        organization = data.get('organization', {})

        # Get filings data
        filings = organization.get('filings_with_data', [])

        # Create response
        nonprofit = {
            'ein': organization.get('ein'),
            'name': organization.get('name'),
            'address': organization.get('address'),
            'city': organization.get('city'),
            'state': organization.get('state'),
            'zip_code': organization.get('zipcode'),
            'ntee_code': organization.get('ntee_code'),
            'classification': organization.get('subsection'),
            'website': organization.get('website'),
            'filings': [
                {
                    'year': filing.get('tax_prd_yr'),
                    'total_revenue': filing.get('totrevenue'),
                    'total_expenses': filing.get('totfuncexpns'),
                    'total_assets': filing.get('totassetsend'),
                    'filing_type': filing.get('formtype'),
                    'pdf_url': filing.get('pdf_url')
                }
                for filing in filings
            ]
        }

        return jsonify({
            'status': 'success',
            'data': nonprofit
        })

    except Exception as e:
        raise APIError(f"Error fetching nonprofit data: {str(e)}", status_code=500)

@propublica_bp.route('/nonprofits/search', methods=['GET'])
@cached(timeout=3600)
def search_nonprofits():
    """
    Search for nonprofits by name or other criteria

    Query parameters:
    - q: Search query (organization name)
    - state: Two-letter state code
    - city: City name
    - ntee: NTEE code
    - page: Page number (default: 1)
    """
    try:
        # Get query parameters
        query = request.args.get('q', '')
        state = request.args.get('state', '')
        city = request.args.get('city', '')
        ntee = request.args.get('ntee', '')
        page = int(request.args.get('page', 1))

        # Construct query parameters
        params = {'page': page}

        if query:
            params['q'] = query
        if state:
            params['state[id]'] = state
        if city:
            params['city'] = city
        if ntee:
            params['ntee[id]'] = ntee

        # Make API request
        api_url = f"{current_app.config['PROPUBLICA_API_URL']}/search.json"

        response = api_service.make_request('GET', api_url, params=params)
        data = response.json()

        # Extract and format results
        organizations = []
        for org in data.get('organizations', []):
            organizations.append({
                'ein': org.get('ein'),
                'name': org.get('name'),
                'city': org.get('city'),
                'state': org.get('state'),
                'ntee_code': org.get('ntee_code'),
                'assets': org.get('assets'),
                'income': org.get('income')
            })

        # Return formatted response
        return jsonify({
            'status': 'success',
            'data': organizations,
            'metadata': {
                'page': page,
                'total_pages': data.get('num_pages', 1),
                'total_results': data.get('total_results', 0)
            }
        })

    except Exception as e:
        raise APIError(f"Error searching nonprofits: {str(e)}", status_code=500)

@propublica_bp.route('/nonprofit/sync/<ein>', methods=['POST'])
def sync_nonprofit(ein):
    """
    Sync a nonprofit's data to the local database
    This endpoint should be secured in production
    """
    try:
        api_url = f"{current_app.config['PROPUBLICA_API_URL']}/organizations/{ein}.json"

        # Make API request
        response = api_service.make_request('GET', api_url)
        data = response.json()

        # Extract organization data
        organization = data.get('organization', {})

        # Get the most recent filing
        filings = organization.get('filings_with_data', [])
        latest_filing = filings[0] if filings else {}

        # Check if nonprofit already exists
        nonprofit = NonprofitProfile.query.filter_by(ein=ein).first()

        if nonprofit:
            # Update existing record
            nonprofit.name = organization.get('name', nonprofit.name)
            nonprofit.address = organization.get('address', nonprofit.address)
            nonprofit.city = organization.get('city', nonprofit.city)
            nonprofit.state = organization.get('state', nonprofit.state)
            nonprofit.zip_code = organization.get('zipcode', nonprofit.zip_code)
            nonprofit.ntee_code = organization.get('ntee_code', nonprofit.ntee_code)
            nonprofit.website = organization.get('website', nonprofit.website)

            if latest_filing:
                nonprofit.total_revenue = latest_filing.get('totrevenue', nonprofit.total_revenue)
                nonprofit.total_assets = latest_filing.get('totassetsend', nonprofit.total_assets)
                nonprofit.fiscal_year = latest_filing.get('tax_prd_yr', nonprofit.fiscal_year)
        else:
            # Create new record
            nonprofit = NonprofitProfile(
                ein=ein,
                name=organization.get('name', ''),
                address=organization.get('address', ''),
                city=organization.get('city', ''),
                state=organization.get('state', ''),
                zip_code=organization.get('zipcode', ''),
                ntee_code=organization.get('ntee_code', ''),
                website=organization.get('website', ''),
                total_revenue=latest_filing.get('totrevenue') if latest_filing else None,
                total_assets=latest_filing.get('totassetsend') if latest_filing else None,
                fiscal_year=latest_filing.get('tax_prd_yr') if latest_filing else None
            )
            db.session.add(nonprofit)

        # Commit changes
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Successfully synced nonprofit with EIN {ein}',
            'data': nonprofit.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        raise APIError(f"Error syncing nonprofit: {str(e)}", status_code=500)