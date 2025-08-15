"""
PHASE 3: Advanced Analytics Engine
Provides comprehensive analytics without modifying existing phases
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy import func, and_, or_, extract
from app.models import db, Grant, Organization, User, LovedGrant
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

class Phase3AnalyticsEngine:
    """Advanced analytics engine for grant performance insights"""
    
    def get_executive_dashboard(self, user_id: int) -> Dict:
        """
        Generate executive-level dashboard metrics
        
        Args:
            user_id: User ID for filtering
            
        Returns:
            Executive dashboard data
        """
        try:
            # Get all grants for user
            grants = Grant.query.filter_by(user_id=user_id).all()
            
            # Calculate key metrics
            total_grants = len(grants)
            submitted = sum(1 for g in grants if g.status in ['submitted', 'pending', 'awarded', 'rejected'])
            awarded = sum(1 for g in grants if g.status == 'awarded')
            
            # Success rate
            success_rate = (awarded / submitted * 100) if submitted > 0 else 0
            
            # Total funding
            total_awarded = sum(
                g.grant_amount or 0 for g in grants 
                if g.status == 'awarded' and g.grant_amount
            )
            
            # Average grant size
            avg_grant_size = (total_awarded / awarded) if awarded > 0 else 0
            
            # Pipeline value
            pipeline_value = sum(
                g.grant_amount or 0 for g in grants 
                if g.status not in ['awarded', 'rejected'] and g.grant_amount
            )
            
            # Time metrics
            submission_times = []
            for grant in grants:
                if grant.status in ['submitted', 'awarded'] and grant.created_at:
                    if grant.submission_deadline:
                        days = (grant.submission_deadline - grant.created_at).days
                        submission_times.append(days)
            
            avg_time_to_submit = sum(submission_times) / len(submission_times) if submission_times else 0
            
            # Current month performance
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            month_submitted = sum(
                1 for g in grants 
                if g.created_at and g.created_at.month == current_month 
                and g.created_at.year == current_year
            )
            
            return {
                'success': True,
                'metrics': {
                    'total_applications': total_grants,
                    'success_rate': round(success_rate, 1),
                    'total_awarded': total_awarded,
                    'average_grant_size': round(avg_grant_size, 0),
                    'pipeline_value': pipeline_value,
                    'avg_days_to_submit': round(avg_time_to_submit, 1),
                    'current_month_applications': month_submitted,
                    'awarded_count': awarded,
                    'pending_count': sum(1 for g in grants if g.status == 'pending'),
                    'active_count': sum(1 for g in grants if g.status not in ['awarded', 'rejected'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating executive dashboard: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_success_metrics(self, user_id: int, period_days: int = 365) -> Dict:
        """
        Calculate detailed success metrics over specified period
        
        Args:
            user_id: User ID
            period_days: Number of days to analyze
            
        Returns:
            Success metrics data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            
            grants = Grant.query.filter(
                and_(
                    Grant.user_id == user_id,
                    Grant.created_at >= cutoff_date
                )
            ).all()
            
            # Group by status
            status_counts = defaultdict(int)
            for grant in grants:
                status_counts[grant.status or 'unknown'] += 1
            
            # Calculate conversion rates
            stages = ['discovery', 'research', 'draft', 'review', 'submitted']
            conversions = {}
            
            for i in range(len(stages) - 1):
                from_stage = stages[i]
                to_stage = stages[i + 1]
                
                from_count = sum(1 for g in grants if g.application_stage == from_stage)
                to_count = sum(1 for g in grants if g.application_stage in stages[i+1:])
                
                if from_count > 0:
                    conversions[f"{from_stage}_to_{to_stage}"] = round((to_count / from_count) * 100, 1)
                else:
                    conversions[f"{from_stage}_to_{to_stage}"] = 0
            
            # Success by grant size
            size_buckets = {
                'small': {'min': 0, 'max': 25000, 'awarded': 0, 'total': 0},
                'medium': {'min': 25000, 'max': 100000, 'awarded': 0, 'total': 0},
                'large': {'min': 100000, 'max': 500000, 'awarded': 0, 'total': 0},
                'major': {'min': 500000, 'max': float('inf'), 'awarded': 0, 'total': 0}
            }
            
            for grant in grants:
                if grant.grant_amount:
                    for bucket_name, bucket_data in size_buckets.items():
                        if bucket_data['min'] <= grant.grant_amount < bucket_data['max']:
                            bucket_data['total'] += 1
                            if grant.status == 'awarded':
                                bucket_data['awarded'] += 1
                            break
            
            # Calculate success rate by size
            size_success = {}
            for bucket_name, bucket_data in size_buckets.items():
                if bucket_data['total'] > 0:
                    rate = (bucket_data['awarded'] / bucket_data['total']) * 100
                    size_success[bucket_name] = {
                        'rate': round(rate, 1),
                        'count': bucket_data['total']
                    }
            
            return {
                'success': True,
                'period_days': period_days,
                'total_grants': len(grants),
                'status_distribution': dict(status_counts),
                'stage_conversions': conversions,
                'success_by_size': size_success,
                'overall_success_rate': self._calculate_overall_success_rate(grants)
            }
            
        except Exception as e:
            logger.error(f"Error calculating success metrics: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_predictions(self, user_id: int, grant_data: Dict) -> Dict:
        """
        Generate success predictions for a grant opportunity
        
        Args:
            user_id: User ID
            grant_data: Grant opportunity data
            
        Returns:
            Prediction results
        """
        try:
            # Get historical data
            historical_grants = Grant.query.filter_by(user_id=user_id).all()
            
            # Base prediction factors
            factors = {
                'match_score': grant_data.get('match_score', 50) / 100,
                'organization_experience': min(len(historical_grants) / 20, 1.0),
                'deadline_buffer': self._calculate_deadline_factor(grant_data.get('deadline')),
                'grant_size_fit': self._calculate_size_fit(grant_data.get('amount'), historical_grants),
                'historical_success': self._calculate_historical_success(historical_grants)
            }
            
            # Calculate weighted prediction
            weights = {
                'match_score': 0.35,
                'organization_experience': 0.20,
                'deadline_buffer': 0.15,
                'grant_size_fit': 0.15,
                'historical_success': 0.15
            }
            
            success_probability = sum(
                factors[key] * weights[key] 
                for key in factors
            ) * 100
            
            # Generate recommendations
            recommendations = self._generate_recommendations(factors, success_probability)
            
            # Estimate effort required
            effort_hours = self._estimate_effort(grant_data)
            
            # ROI calculation
            expected_value = (grant_data.get('amount', 0) * success_probability / 100)
            roi_score = (expected_value / max(effort_hours * 50, 1)) * 100  # Assuming $50/hour
            
            return {
                'success': True,
                'success_probability': round(success_probability, 1),
                'factors': {k: round(v * 100, 1) for k, v in factors.items()},
                'recommendations': recommendations,
                'effort_hours': effort_hours,
                'expected_value': round(expected_value, 0),
                'roi_score': round(roi_score, 1),
                'confidence_level': self._calculate_confidence(len(historical_grants))
            }
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyze_trends(self, user_id: int, months: int = 12) -> Dict:
        """
        Analyze historical trends and patterns
        
        Args:
            user_id: User ID
            months: Number of months to analyze
            
        Returns:
            Trend analysis data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
            
            grants = Grant.query.filter(
                and_(
                    Grant.user_id == user_id,
                    Grant.created_at >= cutoff_date
                )
            ).order_by(Grant.created_at).all()
            
            # Monthly trends
            monthly_data = defaultdict(lambda: {
                'applications': 0,
                'awarded': 0,
                'amount_awarded': 0,
                'success_rate': 0
            })
            
            for grant in grants:
                if grant.created_at:
                    month_key = f"{grant.created_at.year}-{grant.created_at.month:02d}"
                    monthly_data[month_key]['applications'] += 1
                    
                    if grant.status == 'awarded':
                        monthly_data[month_key]['awarded'] += 1
                        if grant.grant_amount:
                            monthly_data[month_key]['amount_awarded'] += grant.grant_amount
            
            # Calculate success rates
            for month_key, data in monthly_data.items():
                if data['applications'] > 0:
                    data['success_rate'] = round(
                        (data['awarded'] / data['applications']) * 100, 1
                    )
            
            # Seasonal patterns
            seasonal_patterns = self._analyze_seasonal_patterns(grants)
            
            # Funder preferences
            funder_analysis = self._analyze_funder_preferences(grants)
            
            # Growth metrics
            growth_metrics = self._calculate_growth_metrics(monthly_data)
            
            return {
                'success': True,
                'monthly_trends': dict(monthly_data),
                'seasonal_patterns': seasonal_patterns,
                'funder_analysis': funder_analysis,
                'growth_metrics': growth_metrics,
                'total_period_grants': len(grants)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_roi(self, user_id: int) -> Dict:
        """
        Calculate return on investment metrics
        
        Args:
            user_id: User ID
            
        Returns:
            ROI metrics
        """
        try:
            grants = Grant.query.filter_by(user_id=user_id).all()
            
            # Calculate costs (estimated hours * rate)
            total_hours = 0
            for grant in grants:
                if grant.status in ['submitted', 'awarded', 'rejected']:
                    # Estimate based on grant complexity
                    hours = self._estimate_effort({'amount': grant.grant_amount})
                    total_hours += hours
            
            estimated_cost = total_hours * 50  # $50/hour estimate
            
            # Calculate revenue
            total_revenue = sum(
                g.grant_amount or 0 for g in grants 
                if g.status == 'awarded'
            )
            
            # ROI calculation
            roi = ((total_revenue - estimated_cost) / max(estimated_cost, 1)) * 100
            
            # Cost per application
            cost_per_app = estimated_cost / len(grants) if grants else 0
            
            # Revenue per successful grant
            successful_grants = [g for g in grants if g.status == 'awarded']
            revenue_per_success = (
                total_revenue / len(successful_grants) 
                if successful_grants else 0
            )
            
            return {
                'success': True,
                'total_revenue': total_revenue,
                'estimated_cost': round(estimated_cost, 0),
                'roi_percentage': round(roi, 1),
                'cost_per_application': round(cost_per_app, 0),
                'revenue_per_success': round(revenue_per_success, 0),
                'total_hours_invested': round(total_hours, 1),
                'applications_submitted': len([
                    g for g in grants 
                    if g.status in ['submitted', 'awarded', 'rejected']
                ])
            }
            
        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_team_performance(self, user_id: int) -> Dict:
        """
        Analyze team performance metrics
        
        Args:
            user_id: User ID
            
        Returns:
            Team performance data
        """
        try:
            # Get grants with team members
            grants = Grant.query.filter_by(user_id=user_id).all()
            
            team_metrics = defaultdict(lambda: {
                'grants_worked': 0,
                'grants_awarded': 0,
                'total_value': 0,
                'avg_days_to_submit': []
            })
            
            for grant in grants:
                if hasattr(grant, 'team_members') and grant.team_members:
                    for member_id in grant.team_members:
                        team_metrics[member_id]['grants_worked'] += 1
                        
                        if grant.status == 'awarded':
                            team_metrics[member_id]['grants_awarded'] += 1
                            if grant.grant_amount:
                                team_metrics[member_id]['total_value'] += grant.grant_amount
                        
                        if grant.created_at and grant.submission_deadline:
                            days = (grant.submission_deadline - grant.created_at).days
                            team_metrics[member_id]['avg_days_to_submit'].append(days)
            
            # Calculate averages
            for member_id, metrics in team_metrics.items():
                if metrics['avg_days_to_submit']:
                    avg_days = sum(metrics['avg_days_to_submit']) / len(metrics['avg_days_to_submit'])
                    metrics['avg_days_to_submit'] = round(avg_days, 1)
                else:
                    metrics['avg_days_to_submit'] = 0
                
                # Success rate
                if metrics['grants_worked'] > 0:
                    metrics['success_rate'] = round(
                        (metrics['grants_awarded'] / metrics['grants_worked']) * 100, 1
                    )
                else:
                    metrics['success_rate'] = 0
            
            return {
                'success': True,
                'team_metrics': dict(team_metrics),
                'total_team_members': len(team_metrics),
                'collaborative_grants': sum(
                    1 for g in grants 
                    if hasattr(g, 'team_members') and g.team_members and len(g.team_members) > 1
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting team performance: {e}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    def _calculate_overall_success_rate(self, grants: List[Grant]) -> float:
        """Calculate overall success rate from grants list"""
        submitted = sum(1 for g in grants if g.status in ['submitted', 'awarded', 'rejected'])
        awarded = sum(1 for g in grants if g.status == 'awarded')
        return round((awarded / submitted * 100), 1) if submitted > 0 else 0
    
    def _calculate_deadline_factor(self, deadline) -> float:
        """Calculate deadline factor for predictions"""
        if not deadline:
            return 0.5
        
        if isinstance(deadline, str):
            try:
                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except:
                return 0.5
        
        days_available = (deadline - datetime.utcnow()).days
        
        if days_available < 7:
            return 0.2
        elif days_available < 14:
            return 0.4
        elif days_available < 30:
            return 0.6
        elif days_available < 60:
            return 0.8
        else:
            return 1.0
    
    def _calculate_size_fit(self, amount: int, historical: List[Grant]) -> float:
        """Calculate how well grant size fits organization"""
        if not amount or not historical:
            return 0.5
        
        awarded_grants = [
            g.grant_amount for g in historical 
            if g.status == 'awarded' and g.grant_amount
        ]
        
        if not awarded_grants:
            return 0.5
        
        avg_awarded = sum(awarded_grants) / len(awarded_grants)
        
        # Perfect fit if within 20% of average
        ratio = amount / avg_awarded if avg_awarded > 0 else 1
        
        if 0.8 <= ratio <= 1.2:
            return 1.0
        elif 0.5 <= ratio <= 2.0:
            return 0.7
        elif 0.25 <= ratio <= 4.0:
            return 0.4
        else:
            return 0.2
    
    def _calculate_historical_success(self, grants: List[Grant]) -> float:
        """Calculate historical success factor"""
        if not grants:
            return 0.5
        
        submitted = sum(1 for g in grants if g.status in ['submitted', 'awarded', 'rejected'])
        if submitted == 0:
            return 0.5
        
        awarded = sum(1 for g in grants if g.status == 'awarded')
        return min(awarded / submitted, 1.0)
    
    def _generate_recommendations(self, factors: Dict, probability: float) -> List[str]:
        """Generate actionable recommendations based on factors"""
        recommendations = []
        
        if factors['match_score'] < 0.6:
            recommendations.append("Strengthen alignment with grant requirements")
        
        if factors['deadline_buffer'] < 0.5:
            recommendations.append("Start application immediately - limited time")
        
        if factors['grant_size_fit'] < 0.5:
            recommendations.append("Consider if grant size aligns with capacity")
        
        if factors['organization_experience'] < 0.3:
            recommendations.append("Partner with experienced organizations")
        
        if probability > 70:
            recommendations.append("High probability - prioritize this opportunity")
        elif probability < 30:
            recommendations.append("Low probability - consider if effort justified")
        
        return recommendations
    
    def _estimate_effort(self, grant_data: Dict) -> int:
        """Estimate effort hours required for grant"""
        base_hours = 40  # Base effort
        
        # Adjust based on grant size
        amount = grant_data.get('amount', 0)
        if amount > 500000:
            base_hours += 40
        elif amount > 100000:
            base_hours += 20
        elif amount > 25000:
            base_hours += 10
        
        return base_hours
    
    def _calculate_confidence(self, sample_size: int) -> str:
        """Calculate confidence level based on sample size"""
        if sample_size >= 50:
            return "High"
        elif sample_size >= 20:
            return "Medium"
        elif sample_size >= 5:
            return "Low"
        else:
            return "Very Low"
    
    def _analyze_seasonal_patterns(self, grants: List[Grant]) -> Dict:
        """Analyze seasonal grant patterns"""
        seasonal_data = {
            'Q1': {'applications': 0, 'success_rate': 0},
            'Q2': {'applications': 0, 'success_rate': 0},
            'Q3': {'applications': 0, 'success_rate': 0},
            'Q4': {'applications': 0, 'success_rate': 0}
        }
        
        for grant in grants:
            if grant.created_at:
                quarter = f"Q{(grant.created_at.month - 1) // 3 + 1}"
                seasonal_data[quarter]['applications'] += 1
                if grant.status == 'awarded':
                    seasonal_data[quarter]['success_rate'] += 1
        
        # Calculate success rates
        for quarter, data in seasonal_data.items():
            if data['applications'] > 0:
                data['success_rate'] = round(
                    (data['success_rate'] / data['applications']) * 100, 1
                )
        
        return seasonal_data
    
    def _analyze_funder_preferences(self, grants: List[Grant]) -> Dict:
        """Analyze funder success patterns"""
        funder_data = defaultdict(lambda: {
            'applications': 0,
            'awarded': 0,
            'total_amount': 0,
            'success_rate': 0
        })
        
        for grant in grants:
            if grant.funding_organization:
                funder = grant.funding_organization
                funder_data[funder]['applications'] += 1
                
                if grant.status == 'awarded':
                    funder_data[funder]['awarded'] += 1
                    if grant.grant_amount:
                        funder_data[funder]['total_amount'] += grant.grant_amount
        
        # Calculate success rates and sort by applications
        for funder, data in funder_data.items():
            if data['applications'] > 0:
                data['success_rate'] = round(
                    (data['awarded'] / data['applications']) * 100, 1
                )
        
        # Return top 10 funders
        sorted_funders = sorted(
            funder_data.items(), 
            key=lambda x: x[1]['applications'], 
            reverse=True
        )[:10]
        
        return dict(sorted_funders)
    
    def _calculate_growth_metrics(self, monthly_data: Dict) -> Dict:
        """Calculate growth metrics from monthly data"""
        if not monthly_data:
            return {}
        
        sorted_months = sorted(monthly_data.keys())
        
        if len(sorted_months) < 2:
            return {'growth_rate': 0}
        
        # Compare last month to first month
        first_month = monthly_data[sorted_months[0]]
        last_month = monthly_data[sorted_months[-1]]
        
        # Application growth
        app_growth = 0
        if first_month['applications'] > 0:
            app_growth = ((last_month['applications'] - first_month['applications']) / 
                         first_month['applications']) * 100
        
        # Success rate improvement
        success_improvement = last_month['success_rate'] - first_month['success_rate']
        
        # Average monthly applications
        total_apps = sum(data['applications'] for data in monthly_data.values())
        avg_monthly = total_apps / len(monthly_data)
        
        return {
            'application_growth_rate': round(app_growth, 1),
            'success_rate_improvement': round(success_improvement, 1),
            'average_monthly_applications': round(avg_monthly, 1),
            'months_analyzed': len(monthly_data)
        }

# Singleton instance
phase3_analytics = Phase3AnalyticsEngine()