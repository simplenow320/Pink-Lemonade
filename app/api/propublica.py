from flask import Blueprint, request, jsonify, current_app
from app.models import Organization
from app import db
from app.services.http_helpers import make_request_with_retry
from functools import lru_cache

propublica_bp = Blueprint('propublica', __name__, url_prefix='/api/propublica')

@propublica_bp.route('/nonprofit/<ein>', methods=['GET'])
@lru_cache(maxsize=128)
def get_nonprofit_by_ein(ein):
    """
    Get nonprofit information by EIN (Employer Identification Number) from ProPublica.

    Path parameter:
        - ein: The Employer Identification Number of the nonprofit
    """
    api_url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

    try:
        # Make API request
        response = make_request_with_retry('GET', api_url)
        data = response.json()

        # Extract organization data
        org_data = data.get('organization', {})
        filings = org_data.get('filings_with_data', [])

        # Get the most recent filing
        latest_filing = filings[0] if filings else {}

        # Map the response to a consistent format
        nonprofit = {
            'ein': org_data.get('ein'),
            'name': org_data.get('name'),
            'ntee_code': org_data.get('ntee_code'),
            'address': f"{org_data.get('address')}, {org_data.get('city')}, {org_data.get('state')} {org_data.get('zipcode')}",
            'city': org_data.get('city'),
            'state': org_data.get('state'),
            'zip_code': org_data.get('zipcode'),
            'assets': latest_filing.get('totassetsend'),
            'revenue': latest_filing.get('totrevenue'),
            'fiscal_year': latest_filing.get('tax_prd_yr'),
            'status': org_data.get('subsection'),
            'form_990_url': latest_filing.get('pdf_url') if latest_filing else None,
            'website': org_data.get('website'),
            'filings': [
                {
                    'year': filing.get('tax_prd_yr'),
                    'type': filing.get('formtype'),
                    'assets': filing.get('totassetsend'),
                    'revenue': filing.get('totrevenue'),
                    'expenses': filing.get('totfuncexpns'),
                    'pdf_url': filing.get('pdf_url')
                }
                for filing in filings
            ]
        }

        return jsonify(nonprofit)

    except Exception as e:
        return jsonify({
            'error': f"Failed to retrieve nonprofit data: {str(e)}",
            'status': 'error'
        }), 500

@propublica_bp.route('/nonprofit/search', methods=['GET'])
@lru_cache(maxsize=128)
def search_nonprofits():
    """
    Search for nonprofits by name or criteria.

    Query parameters:
        - q: Search query for nonprofit name
        - state: Two-letter state code
        - ntee: NTEE code to filter by
        - page: Page number for pagination (default: 1)
    """
    search_query = request.args.get('q', '')
    state = request.args.get('state', '')
    ntee = request.args.get('ntee', '')
    page = int(request.args.get('page', 1))

    # Build API request
    api_url = "https://projects.propublica.org/nonprofits/api/v2/search.json"

    params = {
        'q': search_query,
        'state': state,
        'ntee': ntee,
        'page': page
    }

    # Remove empty params
    params = {k: v for k, v in params.items() if v}

    try:
        # Make API request
        response = make_request_with_retry('GET', api_url, params=params)
        data = response.json()

        # Extract organizations
        organizations = data.get('organizations', [])

        # Map to a consistent format
        results = []
        for org in organizations:
            nonprofit = {
                'ein': org.get('ein'),
                'name': org.get('name'),
                'city': org.get('city'),
                'state': org.get('state'),
                'ntee_code': org.get('ntee_code'),
                'score': org.get('score'),
                'url': f"https://projects.propublica.org/nonprofits/api/v2/organizations/{org.get('ein')}.json"
            }
            results.append(nonprofit)

        # Add pagination info
        response_data = {
            'results': results,
            'page': page,
            'total_pages': data.get('num_pages', 1),
            'total_results': data.get('total_results', 0)
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            'error': f"Failed to search nonprofits: {str(e)}",
            'status': 'error'
        }), 500

@propublica_bp.route('/nonprofit/sync/<ein>', methods=['POST'])
def sync_nonprofit(ein):
    """
    Sync a nonprofit's data from ProPublica to the local database.

    Path parameter:
        - ein: The Employer Identification Number of the nonprofit
    """
    api_url = f"https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"

    try:
        # Make API request
        response = make_request_with_retry('GET', api_url)
        data = response.json()

        # Extract organization data
        org_data = data.get('organization', {})
        filings = org_data.get('filings_with_data', [])

        # Get the most recent filing
        latest_filing = filings[0] if filings else {}

        # Check if nonprofit exists in database
        nonprofit = Organization.query.filter_by(ein=ein).first()

        if nonprofit:
            # Update existing record
            nonprofit.name = org_data.get('name', nonprofit.name)
            nonprofit.city = org_data.get('city', nonprofit.city)
            nonprofit.state = org_data.get('state', nonprofit.state)
            nonprofit.zip_code = org_data.get('zipcode', nonprofit.zip_code)
            nonprofit.address = org_data.get('address', nonprofit.address)
            nonprofit.website = org_data.get('website', nonprofit.website)

            # Update financial data if available
            if latest_filing:
                nonprofit.annual_revenue = latest_filing.get('totrevenue', nonprofit.annual_revenue)
                nonprofit.assets = latest_filing.get('totassetsend', nonprofit.assets)
        else:
            # Create new record
            nonprofit = Organization(
                ein=ein,
                name=org_data.get('name'),
                city=org_data.get('city'),
                state=org_data.get('state'),
                zip_code=org_data.get('zipcode'),
                address=org_data.get('address'),
                website=org_data.get('website'),
                annual_revenue=latest_filing.get('totrevenue') if latest_filing else None,
                assets=latest_filing.get('totassetsend') if latest_filing else None
            )
            db.session.add(nonprofit)

        # Commit changes
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Synced nonprofit with EIN {ein}',
            'data': {
                'id': nonprofit.id,
                'name': nonprofit.name,
                'ein': nonprofit.ein
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f"Failed to sync nonprofit: {str(e)}",
            'status': 'error'
        }), 500