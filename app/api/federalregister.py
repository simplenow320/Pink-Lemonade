from flask import Blueprint, request, jsonify, current_app
from app.models import Grant
from app import db
from app.services.http_helpers import make_request_with_retry
from functools import lru_cache
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

federalregister_bp = Blueprint('federalregister', __name__, url_prefix='/api/federalregister')

@federalregister_bp.route('/notices', methods=['GET'])
@lru_cache(maxsize=128)
def get_notices():
    """
    Get funding notices from Federal Register.

    Query parameters:
        - term: Search term (default: 'Notice of Funding Opportunity')
        - agency: Filter by agency
        - days: Number of days to look back (default: 30)
        - page: Page number (default: 1)
        - per_page: Results per page (default: 20, max: 50)
    """
    term = request.args.get('term', 'Notice of Funding Opportunity')
    agency = request.args.get('agency')
    days = int(request.args.get('days', 30))
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 50)  # Limit to 50 max

    # Calculate date range
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    # Build API request
    api_url = "https://www.federalregister.gov/api/v1/documents.json"

    params = {
        'conditions[term]': term,
        'conditions[publication_date][gte]': start_date,
        'conditions[publication_date][lte]': end_date,
        'page': page,
        'per_page': per_page,
        'order': 'newest'
    }

    # Add agency filter if provided
    if agency:
        params['conditions[agencies][]'] = agency

    try:
        # Make API request
        response = make_request_with_retry('GET', api_url, params=params)
        data = response.json()

        # Map the results to a consistent format
        results = []
        for item in data.get('results', []):
            notice = {
                'title': item.get('title'),
                'document_number': item.get('document_number'),
                'html_url': item.get('html_url'),
                'pdf_url': item.get('pdf_url'),
                'publication_date': item.get('publication_date'),
                'agency_names': item.get('agencies', []),
                'excerpts': item.get('excerpts'),
                'type': item.get('type'),
                'abstract': item.get('abstract'),
                'document_type': item.get('document_type'),
                'source': 'federal_register'
            }
            results.append(notice)

        # Add pagination info
        response_data = {
            'results': results,
            'page': page,
            'per_page': per_page,
            'total_pages': data.get('total_pages', 1),
            'total_results': data.get('count', 0),
            'date_range': {'start': start_date, 'end': end_date}
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error fetching notices from Federal Register: {str(e)}")
        return jsonify({
            'error': f"Failed to retrieve data: {str(e)}",
            'status': 'error'
        }), 500

@federalregister_bp.route('/notice/<document_number>', methods=['GET'])
@lru_cache(maxsize=128)
def get_notice_detail(document_number):
    """Get detailed information about a specific notice"""
    try:
        # Make API request
        api_url = f"https://www.federalregister.gov/api/v1/documents/{document_number}.json"

        response = make_request_with_retry('GET', api_url)
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
        logger.error(f"Error fetching notice details: {str(e)}")
        return jsonify({
            'error': f"Failed to retrieve notice details: {str(e)}",
            'status': 'error'
        }), 500

@federalregister_bp.route('/notices/sync', methods=['POST'])
def sync_funding_notices():
    """
    Sync funding notices from Federal Register to the local database.
    This endpoint should be secured in production.
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
        api_url = "https://www.federalregister.gov/api/v1/documents.json"

        count = 0
        page = 1
        has_more = True

        while has_more:
            params['page'] = page

            response = make_request_with_retry('GET', api_url, params=params)
            data = response.json()

            # Process results
            for item in data.get('results', []):
                # Check if it's a funding opportunity
                title = item.get('title', '').lower()
                if 'funding' in title or 'grant' in title or 'award' in title:
                    # Check if notice already exists
                    document_number = item.get('document_number')

                    existing = Grant.query.filter_by(
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
                        grant = Grant(
                            title=item.get('title', '')[:255],
                            description=item.get('abstract', ''),
                            agency=agency_str,
                            source='federalregister',
                            source_id=document_number,
                            post_date=publication_date,
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
        logger.error(f"Error syncing funding notices: {str(e)}")
        return jsonify({
            'error': f"Failed to sync notices: {str(e)}",
            'status': 'error'
        }), 500