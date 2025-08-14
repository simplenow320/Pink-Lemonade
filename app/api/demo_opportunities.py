"""
Demo Opportunities API - Shows platform capabilities with sample data
"""
import logging
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

bp = Blueprint('demo_opportunities', __name__)

# Sample data to demonstrate multi-source capabilities
DEMO_FEDERAL = [
    {
        "source": "grants.gov",
        "source_type": "Federal",
        "source_name": "Grants.gov",
        "title": "Community Development Block Grant Program",
        "funder": "Department of Housing and Urban Development",
        "amount": "$250,000 - $1,000,000",
        "deadline": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
        "location": "National",
        "description": "Support for community development activities"
    },
    {
        "source": "grants.gov", 
        "source_type": "Federal",
        "source_name": "Grants.gov",
        "title": "Youth Mentoring Program Grant",
        "funder": "Department of Education",
        "amount": "$50,000 - $500,000",
        "deadline": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "location": "Chicago, Detroit, Milwaukee",
        "description": "Funding for youth mentoring initiatives"
    }
]

DEMO_FOUNDATION = [
    {
        "source": "candid_news",
        "source_type": "Foundation",
        "source_name": "Philanthropy News Digest",
        "title": "MacArthur Foundation Announces Climate Solutions RFP",
        "funder": "MacArthur Foundation",
        "amount": "$100,000 - $2,000,000",
        "published_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "location": "National",
        "description": "Request for proposals for innovative climate solutions"
    },
    {
        "source": "candid_news",
        "source_type": "Foundation",
        "source_name": "Foundation Center",
        "title": "Gates Foundation Education Innovation Grant",
        "funder": "Bill & Melinda Gates Foundation",
        "amount": "$250,000 - $5,000,000",
        "published_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
        "location": "Atlanta, Chicago, Los Angeles",
        "description": "Supporting educational innovation in urban communities"
    }
]

DEMO_HISTORICAL = [
    {
        "source": "candid_grants",
        "source_type": "Historical",
        "source_name": "Grant History Database",
        "title": "Ford Foundation - Community Development Grant",
        "funder": "Ford Foundation",
        "amount": "$500,000",
        "grant_date": "2024-06-15",
        "recipient": "Urban Community Alliance",
        "location": "Detroit",
        "description": "Historical grant for community development"
    },
    {
        "source": "candid_grants",
        "source_type": "Historical", 
        "source_name": "Grant History Database",
        "title": "Kellogg Foundation - Youth Program Support",
        "funder": "W.K. Kellogg Foundation",
        "amount": "$750,000",
        "grant_date": "2024-08-20",
        "recipient": "Youth Empowerment Network",
        "location": "Grand Rapids",
        "description": "Previous funding for youth programs"
    }
]

@bp.route('/api/demo/opportunities', methods=['GET'])
def get_demo_opportunities():
    """
    Demo endpoint showing multi-source grant aggregation capability
    """
    try:
        all_opportunities = []
        
        # Add federal grants
        all_opportunities.extend(DEMO_FEDERAL)
        
        # Add foundation news
        all_opportunities.extend(DEMO_FOUNDATION)
        
        # Add historical grants
        all_opportunities.extend(DEMO_HISTORICAL)
        
        # Add some variety with random locations from our expanded list
        cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                  "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
                  "Austin", "Jacksonville", "Fort Worth", "Columbus", "Indianapolis",
                  "Charlotte", "San Francisco", "Seattle", "Denver", "Washington DC",
                  "Boston", "Nashville", "Detroit", "Portland", "Memphis"]
        
        for opp in all_opportunities:
            if random.random() > 0.5:
                opp["location"] = random.choice(cities)
        
        return jsonify({
            'success': True,
            'message': 'Demonstration of multi-source capability',
            'opportunities': all_opportunities,
            'total': len(all_opportunities),
            'sources': {
                'federal': len(DEMO_FEDERAL),
                'foundation': len(DEMO_FOUNDATION),
                'historical': len(DEMO_HISTORICAL),
                'saved': 0
            },
            'available_locations': cities + ["National"]
        })
        
    except Exception as e:
        logger.error(f"Error in demo opportunities: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })