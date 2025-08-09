"""
Advanced Search Service
Provides powerful search and filtering capabilities
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import or_, and_, func
from app.models import Grant, Organization
from app import db
import logging

logger = logging.getLogger(__name__)

class AdvancedSearchService:
    """Advanced search and filtering for grants"""
    
    def __init__(self):
        self.search_fields = ['title', 'funder', 'description', 'focus_areas', 'eligibility_criteria']
    
    def search_grants(self, org_id: int, query: str = None, filters: Dict = None) -> List[Dict]:
        """
        Advanced grant search with multiple filters
        """
        try:
            # Start with base query
            grants_query = Grant.query.filter_by(org_id=org_id)
            
            # Apply text search if provided
            if query:
                search_conditions = []
                for field in self.search_fields:
                    search_conditions.append(
                        getattr(Grant, field).ilike(f'%{query}%')
                    )
                grants_query = grants_query.filter(or_(*search_conditions))
            
            # Apply filters
            if filters:
                # Status filter
                if filters.get('status'):
                    if isinstance(filters['status'], list):
                        grants_query = grants_query.filter(Grant.status.in_(filters['status']))
                    else:
                        grants_query = grants_query.filter_by(status=filters['status'])
                
                # Amount range filter
                if filters.get('amount_min'):
                    grants_query = grants_query.filter(Grant.amount_max >= filters['amount_min'])
                if filters.get('amount_max'):
                    grants_query = grants_query.filter(Grant.amount_min <= filters['amount_max'])
                
                # Deadline filter
                if filters.get('deadline_start'):
                    grants_query = grants_query.filter(Grant.deadline >= filters['deadline_start'])
                if filters.get('deadline_end'):
                    grants_query = grants_query.filter(Grant.deadline <= filters['deadline_end'])
                
                # Match score filter
                if filters.get('min_match_score'):
                    grants_query = grants_query.filter(Grant.match_score >= filters['min_match_score'])
                
                # Source filter
                if filters.get('source_name'):
                    grants_query = grants_query.filter_by(source_name=filters['source_name'])
                
                # Geography filter
                if filters.get('geography'):
                    grants_query = grants_query.filter(
                        Grant.geography.ilike(f'%{filters["geography"]}%')
                    )
                
                # Focus area filter
                if filters.get('focus_area'):
                    grants_query = grants_query.filter(
                        Grant.focus_areas.ilike(f'%{filters["focus_area"]}%')
                    )
            
            # Apply sorting
            sort_by = filters.get('sort_by', 'deadline') if filters else 'deadline'
            sort_order = filters.get('sort_order', 'asc') if filters else 'asc'
            
            if sort_by == 'deadline':
                if sort_order == 'desc':
                    grants_query = grants_query.order_by(Grant.deadline.desc())
                else:
                    grants_query = grants_query.order_by(Grant.deadline.asc())
            elif sort_by == 'amount':
                if sort_order == 'desc':
                    grants_query = grants_query.order_by(Grant.amount_max.desc())
                else:
                    grants_query = grants_query.order_by(Grant.amount_max.asc())
            elif sort_by == 'match_score':
                if sort_order == 'desc':
                    grants_query = grants_query.order_by(Grant.match_score.desc())
                else:
                    grants_query = grants_query.order_by(Grant.match_score.asc())
            elif sort_by == 'created':
                if sort_order == 'desc':
                    grants_query = grants_query.order_by(Grant.discovered_at.desc())
                else:
                    grants_query = grants_query.order_by(Grant.discovered_at.asc())
            
            # Apply pagination if specified
            page = filters.get('page', 1) if filters else 1
            per_page = filters.get('per_page', 50) if filters else 50
            
            paginated = grants_query.paginate(page=page, per_page=per_page, error_out=False)
            
            results = []
            for grant in paginated.items:
                grant_dict = grant.to_dict()
                # Add additional computed fields
                if grant.deadline:
                    days_until = (grant.deadline - datetime.now()).days
                    grant_dict['days_until_deadline'] = days_until
                    grant_dict['deadline_urgency'] = self._calculate_urgency(days_until)
                results.append(grant_dict)
            
            return {
                'grants': results,
                'total': paginated.total,
                'page': page,
                'per_page': per_page,
                'total_pages': paginated.pages
            }
            
        except Exception as e:
            logger.error(f"Error searching grants: {e}")
            return {'grants': [], 'total': 0, 'page': 1, 'per_page': 50, 'total_pages': 0}
    
    def get_saved_searches(self, user_id: int) -> List[Dict]:
        """
        Get saved searches for a user
        """
        # This would typically query a SavedSearch model
        # For now, return predefined common searches
        return [
            {
                'id': 1,
                'name': 'High Match Score',
                'filters': {'min_match_score': 4},
                'icon': '⭐'
            },
            {
                'id': 2,
                'name': 'Upcoming Deadlines',
                'filters': {
                    'deadline_end': (datetime.now() + timedelta(days=30)).isoformat(),
                    'sort_by': 'deadline',
                    'sort_order': 'asc'
                },
                'icon': '⏰'
            },
            {
                'id': 3,
                'name': 'Large Grants',
                'filters': {'amount_min': 100000},
                'icon': '💰'
            },
            {
                'id': 4,
                'name': 'Federal Grants',
                'filters': {'source_name': 'Grants.gov'},
                'icon': '🏛️'
            }
        ]
    
    def get_search_suggestions(self, org_id: int, partial_query: str) -> List[str]:
        """
        Get search suggestions based on partial query
        """
        try:
            suggestions = set()
            
            # Search in grant titles
            grants = Grant.query.filter(
                Grant.org_id == org_id,
                Grant.title.ilike(f'%{partial_query}%')
            ).limit(5).all()
            
            for grant in grants:
                suggestions.add(grant.title)
            
            # Search in funders
            funders = db.session.query(Grant.funder).filter(
                Grant.org_id == org_id,
                Grant.funder.ilike(f'%{partial_query}%')
            ).distinct().limit(5).all()
            
            for funder in funders:
                if funder[0]:
                    suggestions.add(funder[0])
            
            return list(suggestions)[:10]
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []
    
    def get_filter_options(self, org_id: int) -> Dict:
        """
        Get available filter options based on existing data
        """
        try:
            # Get unique values for filters
            sources = db.session.query(Grant.source_name).filter(
                Grant.org_id == org_id
            ).distinct().all()
            
            statuses = db.session.query(Grant.status).filter(
                Grant.org_id == org_id
            ).distinct().all()
            
            # Get amount ranges
            amount_stats = db.session.query(
                func.min(Grant.amount_min),
                func.max(Grant.amount_max)
            ).filter(Grant.org_id == org_id).first()
            
            return {
                'sources': [s[0] for s in sources if s[0]],
                'statuses': [s[0] for s in statuses if s[0]],
                'amount_range': {
                    'min': amount_stats[0] or 0,
                    'max': amount_stats[1] or 1000000
                },
                'sort_options': [
                    {'value': 'deadline', 'label': 'Deadline'},
                    {'value': 'amount', 'label': 'Amount'},
                    {'value': 'match_score', 'label': 'Match Score'},
                    {'value': 'created', 'label': 'Date Added'}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting filter options: {e}")
            return {}
    
    def _calculate_urgency(self, days_until: int) -> str:
        """Calculate deadline urgency level"""
        if days_until < 0:
            return 'expired'
        elif days_until <= 7:
            return 'critical'
        elif days_until <= 14:
            return 'high'
        elif days_until <= 30:
            return 'medium'
        else:
            return 'low'

# Singleton instance
search_service = AdvancedSearchService()