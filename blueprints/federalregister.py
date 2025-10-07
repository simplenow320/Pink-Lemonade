from flask import Blueprint, request, jsonify, current_app
from services.api_service import api_service
from models.grant import GrantOpportunity
from app import db
from utils.caching import cached
from utils.error_handlers import APIError
from datetime import datetime, timedelta
import logging

federalregister_bp = Blueprint('federalregister', __name__)
logger = logging.getLogger(__name__)

@federalregister_bp.route('/notices', methods=['GET'])
@cached(timeout=3600)
def get_funding_notices():
    """
    Get funding notices from Federal Register API

    Query parameters:
    - term: Search term (default: 'Notice of Funding Opportunity')
    - days: Number of days to look back (default: 30)
    - agency: Filter by agency name
    - page: Page number (default: 1)
    - per_page: Results per page (default: 25, max: 100)
    """
    try:
        # Get query parameters
        term = request.args.get('term', 'Notice of Funding Opportunity')
        days = int(request.args.get('days', 30))
        agency = request.args.get('agency')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 25)), 100)  # Cap at 100

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Construct query parameters
        params = {
            'conditions[term]': term,
            'conditions[publication_date][gte]': start_date.strftime('%Y-%m-%d'),
            'conditions[publication_date][lte]': end_date.strftime('%Y-%m-%d'),
            'page': page,
            'per_page': per_page,
            'order': 'newest'
        }

        if agency:
            params['conditions[agencies][]'] = agency

        # Make API request
        api_url = f"{current_app.config['FEDERAL_REGISTER_API_URL']}/documents.json"

        response = api_service.make_request('GET', api_url, params=params)
        data = response.json()

        # Process and format the results
        notices = []
        for item in data.get('results', []):
            # Check if it's a funding opportunity
            title = item.get('title', '').lower()
            if 'funding' in title or 'grant' in title or 'award' in title:
                notice = {
                    'document_number': item.get('document_number'),
                    'title': item.get('title'),
                    'publication_date': item.get('publication_date'),
                    'agencies': [agency.get('name') for agency in item.get('agencies', [])],
                    'html_url': item.get('html_url'),
                    'pdf_url': item.get('pdf_url'),
                    'abstract': item.get('abstract')
                }
                notices.append(notice)

        # Return formatted response
        return jsonify({
            'status': 'success',
            'data': notices,
            'metadata': {
                'page': page,
                'per_page': per_page,
                'total_pages': data.get('total_pages', 1),
                'total_results': data.get('count', 0),
                'count': len(notices)
            }
        })

    except Exception as e:
        raise APIError(f"Error fetching funding notices: {str(e)}", status_code=500)

@federalregister_bp.route('/notice/<document_number>', methods=['GET'])
@cached(timeout=86400)  # Cache for 1 day
def get_notice_detail(document_number):
    """Get detailed information about a specific notice"""
    try:
        # Make API request
        api_url = f"{current_app.config['FEDERAL_REGISTER_API_URL']}/documents/{document_number}.json"

        response = api_service.make_request('GET', api_url)
        data = response.json()

        # Extract funding opportunity specific information
        notice = {
            'document_number': data.get('document_number'),
            'title': data.get('title'),
            'publication_date': data.get('publication_date'),
            'agencies': [agency.get('name') for agency in data.get('agencies', [])],
            'html_url': data.get('html_url'),
            'pdf_url': data.get('pdf_url'),
            'abstract': data.get('abstract'),
            'body_html': data.get('body_html'),
            'dates': data.get('dates'),
            'agency_contact_details': data.get('agencies_participating_raw')
        }

        return jsonify({
            'status': 'success',
            'data': notice
        })

    except Exception as e:
        raise APIError(f"Error fetching notice details: {str(e)}", status_code=500)

@federalregister_bp.route('/notices/sync', methods=['POST'])
def sync_funding_notices():
    """
    Sync funding notices to the local database
    This endpoint should be secured in production
    """
    try:
        # Get parameters
        days = int(request.args.get('days', 7))  # Default to last 7 days
        term = request.args.get('term', 'Notice of Funding Opportunity')

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Construct query parameters
        params = {
            'conditions[term]': term,
            'conditions[publication_date][gte]': start_date.strftime('%Y-%m-%d'),
            'conditions[publication_date][lte]': end_date.strftime('%Y-%m-%d'),
            'per_page': 100,
            'page': 1,
            'order': 'newest'
        }

        # Make API request
        api_url = f"{current_app.config['FEDERAL_REGISTER_API_URL']}/documents.json"

        count = 0
        page = 1
        has_more = True

        while has_more:
            params['page'] = page

            response = api_service.make_request('GET', api_url, params=params)
            data = response.json()

            # Process results
            for item in data.get('results', []):
                # Check if it's a funding opportunity
                title = item.get('title', '').lower()
                if 'funding' in title or 'grant' in title or 'award' in title:
                    # Check if notice already exists
                    document_number = item.get('document_number')

                    existing = GrantOpportunity.query.filter_by(
                        source='federalregister',
                        source_id=document_number
                    ).first()

                    if not existing:
                        # Parse date
                        publication_date = None
                        if item.get('publication_date'):
                            try:
                                publication_date = datetime.strptime(item.get('publication_date'), '%Y-%m-%d')
                            except ValueError:
                                pass

                        # Get agency names
                        agencies = [agency.get('name') for agency in item.get('agencies', [])]
                        agency_str = ', '.join(agencies) if agencies else ''

                        # Create new grant opportunity
                        grant = GrantOpportunity(
                            title=item.get('title', '')[:255],
                            description=item.get('abstract', ''),
                            agency=agency_str,
                            source='federalregister',
                            source_id=document_number,
                            open_date=publication_date,
                            url=item.get('html_url')
                        )
                        db.session.add(grant)
                        count += 1

            # Check if there are more pages
            total_pages = data.get('total_pages', 1)
            has_more = page < total_pages
            page += 1

        # Commit changes
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Successfully synced {count} funding notices',
            'count': count
        })

    except Exception as e:
        db.session.rollback()
        raise APIError(f"Error syncing funding notices: {str(e)}", status_code=500)