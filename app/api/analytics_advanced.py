"""
Advanced Analytics API
Success tracking, trends, and ROI calculations
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app import db
from app.models.grant import Grant
from sqlalchemy import func, extract
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('analytics_advanced', __name__, url_prefix='/api/analytics')

@bp.route('/success-rate', methods=['GET'])
def get_success_rate():
    """Calculate grant success rates"""
    try:
        # Get date range
        days = int(request.args.get('days', 365))
        start_date = datetime.now() - timedelta(days=days)
        
        # Query grant statistics
        total_submitted = Grant.query.filter(
            Grant.date_submitted >= start_date,
            Grant.status.in_(['awarded', 'declined', 'submitted', 'under_review'])
        ).count()
        
        total_awarded = Grant.query.filter(
            Grant.date_decision >= start_date,
            Grant.status == 'awarded'
        ).count()
        
        total_declined = Grant.query.filter(
            Grant.date_decision >= start_date,
            Grant.status == 'declined'
        ).count()
        
        # Calculate by category
        category_stats = db.session.query(
            func.json_extract(Grant.focus_areas, '$[0]').label('category'),
            func.count(Grant.id).label('total'),
            func.sum(func.cast(Grant.status == 'awarded', db.Integer)).label('awarded')
        ).filter(
            Grant.date_submitted >= start_date
        ).group_by('category').all()
        
        # Calculate by funder
        funder_stats = db.session.query(
            Grant.funder,
            func.count(Grant.id).label('total'),
            func.sum(func.cast(Grant.status == 'awarded', db.Integer)).label('awarded')
        ).filter(
            Grant.date_submitted >= start_date
        ).group_by(Grant.funder).all()
        
        return jsonify({
            'overall': {
                'submitted': total_submitted,
                'awarded': total_awarded,
                'declined': total_declined,
                'success_rate': (total_awarded / total_submitted * 100) if total_submitted > 0 else 0,
                'pending': total_submitted - total_awarded - total_declined
            },
            'by_category': [
                {
                    'category': stat.category or 'Uncategorized',
                    'total': stat.total,
                    'awarded': stat.awarded or 0,
                    'success_rate': (stat.awarded / stat.total * 100) if stat.total > 0 else 0
                }
                for stat in category_stats
            ],
            'by_funder': [
                {
                    'funder': stat.funder,
                    'total': stat.total,
                    'awarded': stat.awarded or 0,
                    'success_rate': (stat.awarded / stat.total * 100) if stat.total > 0 else 0
                }
                for stat in funder_stats[:10]  # Top 10 funders
            ]
        })
        
    except Exception as e:
        logger.error(f"Error calculating success rate: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/funding-trends', methods=['GET'])
def get_funding_trends():
    """Analyze funding trends over time"""
    try:
        # Get monthly trends for past year
        months = 12
        trends = []
        
        for i in range(months):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            
            # Get grants for this month
            month_grants = Grant.query.filter(
                Grant.date_submitted >= month_start,
                Grant.date_submitted < month_end
            ).all()
            
            total_amount = sum(g.amount or 0 for g in month_grants)
            awarded_amount = sum(g.amount or 0 for g in month_grants if g.status == 'awarded')
            
            trends.append({
                'month': month_start.strftime('%B %Y'),
                'submitted_count': len(month_grants),
                'total_requested': total_amount,
                'awarded_amount': awarded_amount,
                'success_rate': len([g for g in month_grants if g.status == 'awarded']) / len(month_grants) * 100 if month_grants else 0
            })
        
        # Get trending focus areas
        trending_areas = db.session.query(
            func.json_extract(Grant.focus_areas, '$[0]').label('area'),
            func.count(Grant.id).label('count')
        ).filter(
            Grant.created_at >= datetime.now() - timedelta(days=90)
        ).group_by('area').order_by(func.count(Grant.id).desc()).limit(5).all()
        
        return jsonify({
            'monthly_trends': list(reversed(trends)),
            'trending_focus_areas': [
                {'area': t.area or 'Other', 'count': t.count}
                for t in trending_areas
            ]
        })
        
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/roi', methods=['GET'])
def calculate_roi():
    """Calculate return on investment for grant efforts"""
    try:
        # Time period
        days = int(request.args.get('days', 365))
        start_date = datetime.now() - timedelta(days=days)
        
        # Get awarded grants
        awarded_grants = Grant.query.filter(
            Grant.date_decision >= start_date,
            Grant.status == 'awarded'
        ).all()
        
        # Calculate totals
        total_awarded = sum(g.amount or 0 for g in awarded_grants)
        total_grants = len(awarded_grants)
        
        # Estimate costs (hours spent * hourly rate)
        hours_per_grant = 20  # Average hours per application
        hourly_rate = 50  # Average hourly rate
        total_cost = Grant.query.filter(
            Grant.date_submitted >= start_date
        ).count() * hours_per_grant * hourly_rate
        
        # ROI calculation
        roi = ((total_awarded - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        # Cost per dollar raised
        cost_per_dollar = total_cost / total_awarded if total_awarded > 0 else 0
        
        # Average grant size
        avg_grant_size = total_awarded / total_grants if total_grants > 0 else 0
        
        return jsonify({
            'total_awarded': total_awarded,
            'total_cost_estimate': total_cost,
            'roi_percentage': roi,
            'cost_per_dollar_raised': cost_per_dollar,
            'average_grant_size': avg_grant_size,
            'total_grants_won': total_grants,
            'time_period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error calculating ROI: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/competitor-analysis', methods=['GET'])
def competitor_analysis():
    """Analyze competition for grants"""
    try:
        # Analyze by funder
        funder_competition = db.session.query(
            Grant.funder,
            func.count(Grant.id).label('applications'),
            func.avg(Grant.match_score).label('avg_match_score'),
            func.sum(func.cast(Grant.status == 'awarded', db.Integer)).label('wins')
        ).group_by(Grant.funder).having(func.count(Grant.id) > 1).all()
        
        competition_data = []
        for funder in funder_competition:
            competition_data.append({
                'funder': funder.funder,
                'total_applications': funder.applications,
                'avg_match_score': funder.avg_match_score or 0,
                'wins': funder.wins or 0,
                'win_rate': (funder.wins / funder.applications * 100) if funder.applications > 0 else 0,
                'competition_level': 'High' if funder.applications > 10 else 'Medium' if funder.applications > 5 else 'Low'
            })
        
        # Sort by competition level
        competition_data.sort(key=lambda x: x['total_applications'], reverse=True)
        
        return jsonify({
            'funder_competition': competition_data[:20],  # Top 20
            'summary': {
                'high_competition': len([f for f in competition_data if f['competition_level'] == 'High']),
                'medium_competition': len([f for f in competition_data if f['competition_level'] == 'Medium']),
                'low_competition': len([f for f in competition_data if f['competition_level'] == 'Low'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing competition: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/reports/custom', methods=['POST'])
def generate_custom_report():
    """Generate custom analytics report"""
    try:
        data = request.get_json()
        
        # Report parameters
        start_date = datetime.fromisoformat(data.get('start_date', (datetime.now() - timedelta(days=365)).isoformat()))
        end_date = datetime.fromisoformat(data.get('end_date', datetime.now().isoformat()))
        metrics = data.get('metrics', ['success_rate', 'funding_total', 'applications'])
        group_by = data.get('group_by', 'month')
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'data': []
        }
        
        # Generate report based on grouping
        if group_by == 'month':
            current = start_date.replace(day=1)
            while current < end_date:
                month_end = (current + timedelta(days=32)).replace(day=1)
                
                month_data = {
                    'period': current.strftime('%B %Y')
                }
                
                # Get grants for period
                grants = Grant.query.filter(
                    Grant.date_submitted >= current,
                    Grant.date_submitted < month_end
                ).all()
                
                if 'success_rate' in metrics:
                    awarded = len([g for g in grants if g.status == 'awarded'])
                    month_data['success_rate'] = (awarded / len(grants) * 100) if grants else 0
                
                if 'funding_total' in metrics:
                    month_data['funding_total'] = sum(g.amount or 0 for g in grants if g.status == 'awarded')
                
                if 'applications' in metrics:
                    month_data['applications'] = len(grants)
                
                report['data'].append(month_data)
                current = month_end
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': str(e)}), 500