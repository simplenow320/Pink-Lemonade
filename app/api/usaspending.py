        from flask import Blueprint, request, jsonify, current_app
        from app.models import Grant
        from app import db
        from app.services.http_helpers import make_request_with_retry
        from functools import lru_cache
        from datetime import datetime
        import time
        import logging

        logger = logging.getLogger(__name__)

        usaspending_bp = Blueprint('usaspending', __name__, url_prefix='/api/usaspending')

        @usaspending_bp.route('/awards', methods=['GET'])
        @lru_cache(maxsize=128)
        def get_awards():
            """
            Get federal awards from USAspending.gov API.

            Query parameters:
                - fiscal_year: The fiscal year to filter by
                - agency_id: The awarding agency ID
                - recipient_name: Name of the recipient
                - award_type: Type of award (e.g., 'grant', 'loan')
                - amount_min: Minimum award amount
                - amount_max: Maximum award amount
                - page: Page number for pagination
                - limit: Results per page (default: 50, max: 100)
            """
            fiscal_year = request.args.get('fiscal_year')
            agency_id = request.args.get('agency_id')
            recipient_name = request.args.get('recipient_name')
            award_type = request.args.get('award_type')
            amount_min = request.args.get('amount_min')
            amount_max = request.args.get('amount_max')
            page = int(request.args.get('page', 1))
            limit = min(int(request.args.get('limit', 50)), 100)  # Limit to 100 max

            # Build API request
            api_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

            # Construct filters based on provided parameters
            filters = {"award_type_codes": ["02", "03", "04", "05"]}  # Default to grants and other assistance
            if fiscal_year:
                filters["time_period"] = [{"start_date": f"{fiscal_year}-10-01", "end_date": f"{int(fiscal_year)+1}-09-30"}]
            if agency_id:
                filters["agencies"] = [{"type": "awarding", "tier": "toptier", "name": agency_id}]
            if recipient_name:
                filters["recipient_search_text"] = [recipient_name]
            if award_type and award_type.lower() == 'grant':
                filters["award_type_codes"] = ["02", "03", "04", "05"]
            if amount_min or amount_max:
                amount_filter = {}
                if amount_min:
                    amount_filter["lower_bound"] = float(amount_min)
                if amount_max:
                    amount_filter["upper_bound"] = float(amount_max)
                filters["award_amounts"] = [amount_filter]

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

            try:
                # Make API request
                response = make_request_with_retry('POST', api_url, json=payload)
                data = response.json()

                # Map the results to a consistent format
                results = []
                for item in data.get('results', []):
                    award = {
                        'title': item.get('Description', ''),
                        'award_id': item.get('Award ID', ''),
                        'recipient': item.get('Recipient Name', ''),
                        'agency': item.get('Awarding Agency', ''),
                        'amount': item.get('Award Amount', 0),
                        'award_type': item.get('Award Type', ''),
                        'start_date': item.get('Start Date'),
                        'end_date': item.get('End Date'),
                        'source': 'usaspending'
                    }
                    results.append(award)

                # Add pagination info
                response_data = {
                    'results': results,
                    'page': page,
                    'limit': limit,
                    'total': data.get('page_metadata', {}).get('total', 0),
                    'has_next': page * limit < data.get('page_metadata', {}).get('total', 0)
                }

                return jsonify(response_data)

            except Exception as e:
                logger.error(f"Error fetching awards: {str(e)}")
                return jsonify({
                    'error': f"Failed to retrieve awards: {str(e)}",
                    'status': 'error'
                }), 500

        @usaspending_bp.route('/award/<award_id>', methods=['GET'])
        @lru_cache(maxsize=128)
        def get_award_detail(award_id):
            """Get details for a specific award by ID"""
            try:
                api_url = f"https://api.usaspending.gov/api/v2/awards/{award_id}/"

                # Make API request
                response = make_request_with_retry('GET', api_url)
                data = response.json()

                return jsonify({
                    'status': 'success',
                    'data': data
                })

            except Exception as e:
                logger.error(f"Error fetching award details: {str(e)}")
                return jsonify({
                    'error': f"Failed to retrieve award details: {str(e)}",
                    'status': 'error'
                }), 500

        @usaspending_bp.route('/awards/sync', methods=['POST'])
        def sync_awards():
            """
            Sync awards data to the local database.
            This is an administrative endpoint and should be protected.
            """
            try:
                fiscal_year = request.args.get('fiscal_year', datetime.now().year)

                api_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

                filters = {
                    "award_type_codes": ["02", "03", "04", "05"],  # Grants and other assistance
                    "time_period": [{"start_date": f"{fiscal_year}-10-01", "end_date": f"{int(fiscal_year)+1}-09-30"}]
                }

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
                        time.sleep(1)  # Sleep between requests

                    # Make API request
                    response = make_request_with_retry('POST', api_url, json=payload)
                    data = response.json()

                    for item in data.get('results', []):
                        # Check if award already exists
                        award_id = item.get('Award ID', '')
                        existing = Grant.query.filter_by(source='usaspending', source_id=award_id).first()

                        # Create or update
                        if not existing:
                            award = Grant(
                                title=item.get('Description', ''),
                                description=item.get('Description', ''),
                                agency=item.get('Awarding Agency', ''),
                                source='usaspending',
                                source_id=award_id,
                                amount=item.get('Award Amount', 0),
                                post_date=datetime.strptime(item.get('Start Date'), '%Y-%m-%d') if item.get('Start Date') else None,
                                close_date=datetime.strptime(item.get('End Date'), '%Y-%m-%d') if item.get('End Date') else None,
                                url=f"https://www.usaspending.gov/award/{award_id}"
                            )
                            db.session.add(award)
                            count += 1

                    # Check pagination
                    total = data.get('page_metadata', {}).get('total', 0)
                    has_more = page * payload["limit"] < total
                    page += 1

                # Commit changes
                db.session.commit()

                return jsonify({
                    'status': 'success',
                    'message': f'Synced {count} awards from USAspending.gov',
                    'count': count
                })

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error syncing awards: {str(e)}")
                return jsonify({
                    'error': f"Failed to sync awards: {str(e)}",
                    'status': 'error'
                }), 500