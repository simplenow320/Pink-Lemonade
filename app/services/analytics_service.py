"""
Analytics Service
Comprehensive tracking and insights for grant management
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.models import Grant, Organization, Analytics, Narrative, db
import logging
import json

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Provides comprehensive analytics for grant management:
    - Performance metrics
    - Success rate tracking
    - Funding trends
    - Time-to-decision analysis
    - ROI calculations
    """
    
    def get_dashboard_metrics(self, org_id: int, period_days: int = 30) -> Dict:
        """Get comprehensive dashboard metrics"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get grants for period
            grants = Grant.query.filter(
                Grant.org_id == org_id,
                Grant.created_at >= start_date
            ).all()
            
            # Calculate metrics
            metrics = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': period_days
                },
                'grants': self._calculate_grant_metrics(grants, org_id),
                'funding': self._calculate_funding_metrics(grants),
                'pipeline': self._calculate_pipeline_metrics(org_id),
                'efficiency': self._calculate_efficiency_metrics(grants),
                'trends': self._calculate_trends(org_id, period_days),
                'ai_usage': self._calculate_ai_usage(org_id, start_date)
            }
            
            return {
                'success': True,
                'metrics': metrics,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_success_rate_analysis(self, org_id: int) -> Dict:
        """Analyze grant success rates by various factors"""
        try:
            # Get all completed grants
            completed_grants = Grant.query.filter(
                Grant.org_id == org_id,
                Grant.application_stage.in_(['awarded', 'declined'])
            ).all()
            
            if not completed_grants:
                return {
                    'success': True,
                    'message': 'No completed grants yet',
                    'overall_rate': 0
                }
            
            # Overall success rate
            awarded = len([g for g in completed_grants if g.application_stage == 'awarded'])
            total = len(completed_grants)
            overall_rate = (awarded / total * 100) if total > 0 else 0
            
            # Success by funder
            by_funder = self._success_by_category(completed_grants, 'funder')
            
            # Success by amount range
            by_amount = self._success_by_amount_range(completed_grants)
            
            # Success by geography
            by_geography = self._success_by_category(completed_grants, 'geography')
            
            # Success over time
            by_time = self._success_over_time(completed_grants)
            
            return {
                'success': True,
                'overall_rate': round(overall_rate, 1),
                'total_completed': total,
                'total_awarded': awarded,
                'by_funder': by_funder,
                'by_amount_range': by_amount,
                'by_geography': by_geography,
                'trend': by_time,
                'insights': self._generate_success_insights(
                    overall_rate, by_funder, by_amount
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing success rates: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_funding_forecast(self, org_id: int, months_ahead: int = 6) -> Dict:
        """Forecast potential funding based on pipeline"""
        try:
            # Get active pipeline grants
            pipeline_grants = Grant.query.filter(
                Grant.org_id == org_id,
                Grant.application_stage.in_([
                    'researching', 'writing', 'review', 'submitted', 'pending'
                ])
            ).all()
            
            # Historical success rate
            success_rate = self._get_historical_success_rate(org_id)
            
            # Calculate forecast by month
            forecast = []
            current_date = datetime.utcnow()
            
            for month in range(months_ahead):
                month_date = current_date + timedelta(days=30 * month)
                month_grants = [
                    g for g in pipeline_grants
                    if g.deadline and g.deadline.month == month_date.month
                ]
                
                potential = sum(g.amount_max or 0 for g in month_grants)
                expected = potential * (success_rate / 100)
                
                forecast.append({
                    'month': month_date.strftime('%B %Y'),
                    'grants_count': len(month_grants),
                    'potential_funding': float(potential),
                    'expected_funding': float(expected),
                    'confidence': self._calculate_confidence(len(month_grants))
                })
            
            # Calculate totals
            total_potential = sum(f['potential_funding'] for f in forecast)
            total_expected = sum(f['expected_funding'] for f in forecast)
            
            return {
                'success': True,
                'forecast': forecast,
                'totals': {
                    'potential': total_potential,
                    'expected': total_expected,
                    'success_rate_used': success_rate
                },
                'recommendations': self._generate_forecast_recommendations(
                    forecast, success_rate
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_performance_benchmarks(self, org_id: int) -> Dict:
        """Compare organization performance against benchmarks"""
        try:
            org = Organization.query.get(org_id)
            if not org:
                return {'success': False, 'error': 'Organization not found'}
            
            # Calculate org metrics
            org_metrics = self._calculate_org_performance(org_id)
            
            # Industry benchmarks (could be from external data)
            benchmarks = self._get_industry_benchmarks(org)
            
            # Compare and score
            comparison = {}
            performance_score = 0
            
            for metric, value in org_metrics.items():
                benchmark = benchmarks.get(metric, {})
                if benchmark:
                    percentage = (value / benchmark['average'] * 100) if benchmark['average'] > 0 else 0
                    comparison[metric] = {
                        'value': value,
                        'benchmark': benchmark['average'],
                        'percentile': self._calculate_percentile(percentage),
                        'status': self._get_status(percentage),
                        'improvement_potential': max(0, benchmark['top_quartile'] - value)
                    }
                    performance_score += min(100, percentage) / len(org_metrics)
            
            return {
                'success': True,
                'organization': org.name,
                'performance_score': round(performance_score, 1),
                'metrics': comparison,
                'strengths': self._identify_strengths(comparison),
                'improvements': self._identify_improvements(comparison),
                'recommendations': self._generate_benchmark_recommendations(comparison)
            }
            
        except Exception as e:
            logger.error(f"Error getting benchmarks: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_roi_analysis(self, org_id: int) -> Dict:
        """Calculate ROI on grant writing efforts"""
        try:
            # Get all grants
            grants = Grant.query.filter_by(org_id=org_id).all()
            
            # Calculate investment (time and resources)
            total_applications = len(grants)
            avg_hours_per_grant = 40  # Industry average
            hourly_cost = 50  # Average grant writer hourly rate
            total_investment = total_applications * avg_hours_per_grant * hourly_cost
            
            # Calculate returns
            awarded_grants = [g for g in grants if g.application_stage == 'awarded']
            total_awarded = sum(g.amount_max or 0 for g in awarded_grants)
            
            # ROI calculation
            roi = ((float(total_awarded) - total_investment) / total_investment * 100) if total_investment > 0 else 0
            
            # Time-based analysis
            time_analysis = self._analyze_time_investment(grants)
            
            # Cost per dollar raised
            cost_per_dollar = total_investment / float(total_awarded) if total_awarded > 0 else 0
            
            # AI impact on ROI
            ai_impact = self._calculate_ai_impact(org_id)
            
            return {
                'success': True,
                'roi_percentage': round(roi, 1),
                'investment': {
                    'total_hours': total_applications * avg_hours_per_grant,
                    'total_cost': total_investment,
                    'applications_submitted': total_applications
                },
                'returns': {
                    'grants_won': len(awarded_grants),
                    'total_funding': float(total_awarded),
                    'average_award': float(total_awarded) / len(awarded_grants) if awarded_grants else 0
                },
                'efficiency': {
                    'cost_per_dollar_raised': round(cost_per_dollar, 2),
                    'hours_per_dollar': round(cost_per_dollar * hourly_cost, 2) if cost_per_dollar > 0 else 0,
                    'success_rate': len(awarded_grants) / total_applications * 100 if total_applications > 0 else 0
                },
                'time_analysis': time_analysis,
                'ai_impact': ai_impact,
                'recommendations': self._generate_roi_recommendations(roi, cost_per_dollar)
            }
            
        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============= HELPER METHODS =============
    
    def _calculate_grant_metrics(self, grants: List[Grant], org_id: int) -> Dict:
        """Calculate grant-related metrics"""
        all_grants = Grant.query.filter_by(org_id=org_id).all()
        
        return {
            'total': len(all_grants),
            'new_this_period': len(grants),
            'in_progress': len([g for g in all_grants if g.application_stage not in ['awarded', 'declined']]),
            'submitted': len([g for g in all_grants if g.application_stage in ['submitted', 'pending']]),
            'won': len([g for g in all_grants if g.application_stage == 'awarded']),
            'success_rate': self._get_historical_success_rate(org_id)
        }
    
    def _calculate_funding_metrics(self, grants: List[Grant]) -> Dict:
        """Calculate funding-related metrics"""
        return {
            'potential': sum(g.amount_max or 0 for g in grants),
            'secured': sum(g.amount_max or 0 for g in grants if g.application_stage == 'awarded'),
            'pending': sum(g.amount_max or 0 for g in grants if g.application_stage in ['submitted', 'pending']),
            'average_request': sum(g.amount_max or 0 for g in grants) / len(grants) if grants else 0
        }
    
    def _calculate_pipeline_metrics(self, org_id: int) -> Dict:
        """Calculate pipeline distribution"""
        grants = Grant.query.filter_by(org_id=org_id).all()
        
        stages = {}
        for stage in ['discovery', 'researching', 'writing', 'review', 'submitted', 'pending', 'awarded', 'declined']:
            stage_grants = [g for g in grants if g.application_stage == stage]
            stages[stage] = {
                'count': len(stage_grants),
                'value': sum(g.amount_max or 0 for g in stage_grants)
            }
        
        return stages
    
    def _calculate_efficiency_metrics(self, grants: List[Grant]) -> Dict:
        """Calculate efficiency metrics"""
        if not grants:
            return {
                'avg_time_to_submit': 0,
                'avg_time_to_decision': 0,
                'submission_rate': 0
            }
        
        submitted = [g for g in grants if g.application_stage in ['submitted', 'pending', 'awarded', 'declined']]
        decided = [g for g in grants if g.application_stage in ['awarded', 'declined']]
        
        # Calculate average times
        submit_times = []
        for grant in submitted:
            if grant.created_at and grant.updated_at:
                days = (grant.updated_at - grant.created_at).days
                submit_times.append(days)
        
        avg_submit = sum(submit_times) / len(submit_times) if submit_times else 0
        
        return {
            'avg_time_to_submit': avg_submit,
            'avg_time_to_decision': 90,  # Industry average
            'submission_rate': len(submitted) / len(grants) * 100 if grants else 0
        }
    
    def _calculate_trends(self, org_id: int, period_days: int) -> Dict:
        """Calculate trend data"""
        trends = []
        
        for i in range(6):  # Last 6 periods
            end = datetime.utcnow() - timedelta(days=period_days * i)
            start = end - timedelta(days=period_days)
            
            period_grants = Grant.query.filter(
                Grant.org_id == org_id,
                Grant.created_at >= start,
                Grant.created_at < end
            ).all()
            
            trends.append({
                'period': start.strftime('%b %Y'),
                'grants': len(period_grants),
                'funding': sum(g.amount_max or 0 for g in period_grants)
            })
        
        trends.reverse()
        return trends
    
    def _calculate_ai_usage(self, org_id: int, start_date: datetime) -> Dict:
        """Calculate AI tool usage metrics"""
        narratives = Narrative.query.filter(
            Narrative.org_id == org_id,
            Narrative.ai_generated == True,
            Narrative.created_at >= start_date
        ).count()
        
        return {
            'narratives_generated': narratives,
            'time_saved_hours': narratives * 2,  # Estimate 2 hours per narrative
            'efficiency_gain': '60%'  # Based on industry studies
        }
    
    def _success_by_category(self, grants: List[Grant], category: str) -> List[Dict]:
        """Calculate success rate by category"""
        categories = {}
        
        for grant in grants:
            cat_value = getattr(grant, category, 'Unknown')
            if cat_value not in categories:
                categories[cat_value] = {'total': 0, 'won': 0}
            
            categories[cat_value]['total'] += 1
            if grant.application_stage == 'awarded':
                categories[cat_value]['won'] += 1
        
        result = []
        for cat, stats in categories.items():
            result.append({
                'category': cat,
                'total': stats['total'],
                'won': stats['won'],
                'success_rate': stats['won'] / stats['total'] * 100 if stats['total'] > 0 else 0
            })
        
        return sorted(result, key=lambda x: x['success_rate'], reverse=True)
    
    def _success_by_amount_range(self, grants: List[Grant]) -> List[Dict]:
        """Calculate success rate by amount range"""
        ranges = {
            'Under $10K': (0, 10000),
            '$10K-$50K': (10000, 50000),
            '$50K-$100K': (50000, 100000),
            '$100K-$500K': (100000, 500000),
            'Over $500K': (500000, float('inf'))
        }
        
        results = []
        for range_name, (min_amt, max_amt) in ranges.items():
            range_grants = [
                g for g in grants
                if g.amount_max and min_amt <= g.amount_max < max_amt
            ]
            
            if range_grants:
                won = len([g for g in range_grants if g.application_stage == 'awarded'])
                results.append({
                    'range': range_name,
                    'total': len(range_grants),
                    'won': won,
                    'success_rate': won / len(range_grants) * 100
                })
        
        return results
    
    def _success_over_time(self, grants: List[Grant]) -> List[Dict]:
        """Calculate success rate trend over time"""
        # Group by quarter
        quarters = {}
        
        for grant in grants:
            if grant.created_at:
                quarter = f"Q{(grant.created_at.month-1)//3 + 1} {grant.created_at.year}"
                if quarter not in quarters:
                    quarters[quarter] = {'total': 0, 'won': 0}
                
                quarters[quarter]['total'] += 1
                if grant.application_stage == 'awarded':
                    quarters[quarter]['won'] += 1
        
        result = []
        for quarter, stats in sorted(quarters.items()):
            result.append({
                'period': quarter,
                'success_rate': stats['won'] / stats['total'] * 100 if stats['total'] > 0 else 0
            })
        
        return result
    
    def _get_historical_success_rate(self, org_id: int) -> float:
        """Get historical success rate"""
        completed = Grant.query.filter(
            Grant.org_id == org_id,
            Grant.application_stage.in_(['awarded', 'declined'])
        ).all()
        
        if not completed:
            return 25.0  # Industry average
        
        won = len([g for g in completed if g.application_stage == 'awarded'])
        return round(won / len(completed) * 100, 1)
    
    def _calculate_confidence(self, sample_size: int) -> str:
        """Calculate confidence level based on sample size"""
        if sample_size >= 10:
            return 'High'
        elif sample_size >= 5:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_org_performance(self, org_id: int) -> Dict:
        """Calculate organization performance metrics"""
        grants = Grant.query.filter_by(org_id=org_id).all()
        
        completed = [g for g in grants if g.application_stage in ['awarded', 'declined']]
        won = [g for g in completed if g.application_stage == 'awarded']
        
        return {
            'success_rate': len(won) / len(completed) * 100 if completed else 0,
            'average_award': sum(g.amount_max or 0 for g in won) / len(won) if won else 0,
            'applications_per_month': len(grants) / 12,  # Assuming 1 year of data
            'funding_secured': sum(g.amount_max or 0 for g in won)
        }
    
    def _get_industry_benchmarks(self, org: Organization) -> Dict:
        """Get industry benchmarks based on org type"""
        # These would typically come from external data sources
        return {
            'success_rate': {'average': 25, 'top_quartile': 40},
            'average_award': {'average': 50000, 'top_quartile': 100000},
            'applications_per_month': {'average': 2, 'top_quartile': 5},
            'funding_secured': {'average': 200000, 'top_quartile': 500000}
        }
    
    def _calculate_percentile(self, percentage: float) -> int:
        """Calculate percentile ranking"""
        if percentage >= 90:
            return 90
        elif percentage >= 75:
            return 75
        elif percentage >= 50:
            return 50
        elif percentage >= 25:
            return 25
        else:
            return 10
    
    def _get_status(self, percentage: float) -> str:
        """Get status based on percentage"""
        if percentage >= 100:
            return 'Excellent'
        elif percentage >= 75:
            return 'Good'
        elif percentage >= 50:
            return 'Average'
        else:
            return 'Below Average'
    
    def _identify_strengths(self, comparison: Dict) -> List[str]:
        """Identify organizational strengths"""
        strengths = []
        for metric, data in comparison.items():
            if data['status'] in ['Excellent', 'Good']:
                strengths.append(f"Strong {metric.replace('_', ' ')}: {data['percentile']}th percentile")
        return strengths[:3]  # Top 3 strengths
    
    def _identify_improvements(self, comparison: Dict) -> List[str]:
        """Identify areas for improvement"""
        improvements = []
        for metric, data in comparison.items():
            if data['status'] == 'Below Average':
                improvements.append(f"Improve {metric.replace('_', ' ')}: ${data['improvement_potential']:,.0f} opportunity")
        return improvements[:3]  # Top 3 improvements
    
    def _analyze_time_investment(self, grants: List[Grant]) -> Dict:
        """Analyze time investment patterns"""
        stages = ['discovery', 'researching', 'writing', 'review']
        stage_times = {}
        
        for stage in stages:
            stage_grants = [g for g in grants if g.application_stage == stage]
            if stage_grants:
                # Estimate based on typical durations
                typical_days = {'discovery': 7, 'researching': 14, 'writing': 21, 'review': 3}
                stage_times[stage] = {
                    'grants': len(stage_grants),
                    'avg_days': typical_days.get(stage, 7),
                    'total_hours': len(stage_grants) * typical_days.get(stage, 7) * 8
                }
        
        return stage_times
    
    def _calculate_ai_impact(self, org_id: int) -> Dict:
        """Calculate AI tool impact on efficiency"""
        # Get AI-generated content
        ai_narratives = Narrative.query.filter_by(
            org_id=org_id,
            ai_generated=True
        ).count()
        
        # Estimate time savings
        time_saved = ai_narratives * 2  # 2 hours per narrative
        cost_saved = time_saved * 50  # $50/hour
        
        return {
            'documents_generated': ai_narratives,
            'time_saved_hours': time_saved,
            'cost_saved': cost_saved,
            'efficiency_improvement': '60%'
        }
    
    def _generate_success_insights(self, overall_rate: float, by_funder: List, by_amount: List) -> List[str]:
        """Generate insights from success rate analysis"""
        insights = []
        
        if overall_rate > 30:
            insights.append(f"Success rate of {overall_rate}% exceeds industry average of 25%")
        else:
            insights.append(f"Opportunity to improve success rate from {overall_rate}% to industry average 25%")
        
        if by_funder and by_funder[0]['success_rate'] > 50:
            insights.append(f"Strong relationship with {by_funder[0]['category']} - {by_funder[0]['success_rate']:.0f}% success")
        
        if by_amount:
            best_range = max(by_amount, key=lambda x: x['success_rate'])
            insights.append(f"Highest success in {best_range['range']} range")
        
        return insights
    
    def _generate_forecast_recommendations(self, forecast: List, success_rate: float) -> List[str]:
        """Generate recommendations based on forecast"""
        recommendations = []
        
        # Check for gaps in pipeline
        empty_months = [f['month'] for f in forecast if f['grants_count'] == 0]
        if empty_months:
            recommendations.append(f"Fill pipeline gaps in: {', '.join(empty_months[:2])}")
        
        # Success rate improvement
        if success_rate < 25:
            recommendations.append("Focus on improving success rate to increase expected funding")
        
        # High-value months
        high_value = [f for f in forecast if f['potential_funding'] > 100000]
        if high_value:
            recommendations.append(f"Prioritize applications for {high_value[0]['month']}")
        
        return recommendations
    
    def _generate_benchmark_recommendations(self, comparison: Dict) -> List[str]:
        """Generate recommendations based on benchmarks"""
        recommendations = []
        
        for metric, data in comparison.items():
            if data['status'] == 'Below Average':
                if metric == 'success_rate':
                    recommendations.append("Improve grant matching and proposal quality")
                elif metric == 'applications_per_month':
                    recommendations.append("Increase application volume to capture more opportunities")
                elif metric == 'average_award':
                    recommendations.append("Target larger grants or foundations")
        
        return recommendations
    
    def _generate_roi_recommendations(self, roi: float, cost_per_dollar: float) -> List[str]:
        """Generate ROI improvement recommendations"""
        recommendations = []
        
        if roi < 100:
            recommendations.append("ROI below 100% - focus on higher success rate grants")
        
        if cost_per_dollar > 0.15:
            recommendations.append(f"High cost per dollar raised (${cost_per_dollar:.2f}) - improve efficiency")
        
        recommendations.append("Use AI tools to reduce time investment by 60%")
        recommendations.append("Focus on grants with 80%+ match scores")
        
        return recommendations