"""
Analytics Service for GrantFlow

This service processes grant data to generate analytics and success metrics.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import func, and_, extract
from calendar import monthrange
from collections import defaultdict

from app import db
from app.models import Grant, GrantAnalytics, GrantSuccessMetrics

logger = logging.getLogger(__name__)


def record_status_change(grant_id, new_status, previous_status=None, metadata=None):
    """
    Record a status change for analytics tracking
    
    Args:
        grant_id (int): ID of the grant
        new_status (str): New status value
        previous_status (str, optional): Previous status value
        metadata (dict, optional): Additional metadata
    
    Returns:
        dict: Result of the operation
    """
    try:
        grant = Grant.query.get(grant_id)
        if not grant:
            return {"success": False, "error": "Grant not found"}
        
        # Create new analytics entry
        analytics = GrantAnalytics()
        analytics.grant_id = grant_id
        analytics.status = new_status
        analytics.previous_status = previous_status
        analytics.amount = grant.amount
        analytics.meta_data = metadata or {}
        
        # Update submitted/decision dates based on status
        if new_status == "Submitted" and not analytics.date_submitted:
            analytics.date_submitted = datetime.now().date()
        
        if new_status in ["Won", "Declined"] and not analytics.date_decision:
            analytics.date_decision = datetime.now().date()
            analytics.success = (new_status == "Won")
        
        db.session.add(analytics)
        db.session.commit()
        
        # If status is terminal (Won/Declined), update metrics
        if new_status in ["Won", "Declined"]:
            update_success_metrics()
        
        return {"success": True, "analytics_id": analytics.id}
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error recording status change: {str(e)}")
        return {"success": False, "error": str(e)}


def update_success_metrics():
    """
    Update success metrics for different time periods (monthly, quarterly, yearly)
    This is meant to be run after grant status changes or periodically
    
    Returns:
        dict: Result of the operation
    """
    try:
        # Get current date
        now = datetime.now()
        
        # Update monthly metrics (current month)
        month_key = now.strftime("%Y-%m")
        _update_period_metrics('monthly', month_key, 
                              now.replace(day=1), 
                              now.replace(day=monthrange(now.year, now.month)[1]))
        
        # Update quarterly metrics (current quarter)
        quarter = (now.month - 1) // 3 + 1
        quarter_key = f"{now.year}-Q{quarter}"
        quarter_start = datetime(now.year, (quarter - 1) * 3 + 1, 1)
        quarter_end = datetime(now.year if quarter < 4 else now.year + 1,
                              ((quarter) % 4 + 1) * 3 if quarter < 4 else 1,
                              1) - timedelta(days=1)
        _update_period_metrics('quarterly', quarter_key, quarter_start, quarter_end)
        
        # Update yearly metrics (current year)
        year_key = str(now.year)
        _update_period_metrics('yearly', year_key,
                             datetime(now.year, 1, 1),
                             datetime(now.year, 12, 31))
        
        # Update all-time metrics
        _update_period_metrics('all-time', 'all-time', 
                              datetime(2000, 1, 1), # Far past date
                              now)
        
        return {"success": True, "message": "Metrics updated successfully"}
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating success metrics: {str(e)}")
        return {"success": False, "error": str(e)}


def _update_period_metrics(period, period_key, start_date, end_date):
    """
    Update metrics for a specific time period
    
    Args:
        period (str): Type of period ('monthly', 'quarterly', 'yearly', 'all-time')
        period_key (str): Identifier for the period
        start_date (datetime): Start date for the period
        end_date (datetime): End date for the period
    """
    # Find existing metrics or create new
    metrics = GrantSuccessMetrics.query.filter_by(
        period=period, period_key=period_key
    ).first()
    
    if not metrics:
        metrics = GrantSuccessMetrics()
        metrics.period = period
        metrics.period_key = period_key
    
    # Calculate total submissions in this period
    submissions_query = db.session.query(
        GrantAnalytics.grant_id,
        func.min(GrantAnalytics.date_submitted).label('submission_date')
    ).filter(
        GrantAnalytics.date_submitted.between(start_date, end_date)
    ).group_by(GrantAnalytics.grant_id)
    
    submissions = submissions_query.all()
    metrics.total_submitted = len(submissions)
    
    # Calculate wins/declines in this period
    decisions = db.session.query(
        GrantAnalytics.grant_id,
        GrantAnalytics.success,
        GrantAnalytics.amount,
        GrantAnalytics.date_submitted,
        GrantAnalytics.date_decision
    ).filter(
        GrantAnalytics.date_decision.between(start_date, end_date),
        GrantAnalytics.success != None
    ).all()
    
    # Process decision data
    metrics.total_won = sum(1 for d in decisions if d.success is True)
    metrics.total_declined = sum(1 for d in decisions if d.success is False)
    metrics.total_funding_requested = sum(d.amount or 0 for d in decisions)
    metrics.total_funding_received = sum(d.amount or 0 for d in decisions if d.success is True)
    
    # Calculate success rate
    metrics.success_rate = (metrics.total_won / metrics.total_submitted * 100) if metrics.total_submitted > 0 else 0
    
    # Calculate average response time (days between submission and decision)
    response_times = [
        (d.date_decision - d.date_submitted).days 
        for d in decisions 
        if d.date_decision and d.date_submitted
    ]
    metrics.avg_response_time = sum(response_times) // len(response_times) if response_times else None
    
    # Calculate success by category/focus area
    categories = defaultdict(lambda: {"submitted": 0, "won": 0, "declined": 0, "success_rate": 0})
    
    # Get all grants with decisions in this period
    grant_ids = [d.grant_id for d in decisions]
    grants = Grant.query.filter(Grant.id.in_(grant_ids)).all()
    
    for grant in grants:
        # For each focus area of the grant
        focus_areas = grant.focus_areas or []
        for area in focus_areas:
            # Find the corresponding analytics entry
            analytics = next((d for d in decisions if d.grant_id == grant.id), None)
            if analytics:
                categories[area]["submitted"] += 1
                if analytics.success:
                    categories[area]["won"] += 1
                else:
                    categories[area]["declined"] += 1
    
    # Calculate success rates for each category
    for category, data in categories.items():
        if data["submitted"] > 0:
            data["success_rate"] = (data["won"] / data["submitted"]) * 100
    
    metrics.categories = dict(categories)
    
    # Save metrics
    db.session.add(metrics)
    db.session.commit()


def get_success_metrics(period='all', limit=None, include_categories=True):
    """
    Retrieve success metrics for analysis
    
    Args:
        period (str): Type of period to retrieve ('monthly', 'quarterly', 'yearly', 'all-time')
        limit (int, optional): Number of periods to return (most recent first)
        include_categories (bool): Whether to include category-specific metrics
    
    Returns:
        dict: Success metrics data
    """
    try:
        query = GrantSuccessMetrics.query
        
        # Filter by period type
        if period != 'all':
            query = query.filter_by(period=period)
        
        # Order by period key descending (most recent first)
        query = query.order_by(GrantSuccessMetrics.period_key.desc())
        
        # Limit results if specified
        if limit:
            query = query.limit(limit)
        
        metrics = query.all()
        result = []
        
        for metric in metrics:
            metric_dict = metric.to_dict()
            
            # Exclude categories if not requested
            if not include_categories:
                metric_dict.pop('categories', None)
            
            result.append(metric_dict)
        
        return {
            "success": True,
            "period": period,
            "metrics": result
        }
    
    except Exception as e:
        logger.error(f"Error retrieving success metrics: {str(e)}")
        return {"success": False, "error": str(e)}


def get_trend_data(metric_type='success_rate', period='monthly', months=12):
    """
    Get trend data for a specific metric over time
    
    Args:
        metric_type (str): Type of metric ('success_rate', 'total_funding_received', etc.)
        period (str): Type of period ('monthly', 'quarterly', 'yearly')
        months (int): Number of periods to include
    
    Returns:
        dict: Trend data
    """
    try:
        query = GrantSuccessMetrics.query.filter_by(period=period)
        
        # Order by period key descending (most recent first) and limit
        metrics = query.order_by(GrantSuccessMetrics.period_key.desc()).limit(months).all()
        
        # Reverse to get chronological order
        metrics.reverse()
        
        labels = []
        data = []
        
        for metric in metrics:
            labels.append(metric.period_key)
            
            # Get the specified metric value
            if hasattr(metric, metric_type):
                data.append(getattr(metric, metric_type))
            else:
                data.append(0)
        
        return {
            "success": True,
            "metric": metric_type,
            "period": period,
            "labels": labels,
            "data": data
        }
    
    except Exception as e:
        logger.error(f"Error retrieving trend data: {str(e)}")
        return {"success": False, "error": str(e)}


def get_category_comparison():
    """
    Get success metrics comparison across different focus areas/categories
    
    Returns:
        dict: Category comparison data
    """
    try:
        # Get the most recent all-time metrics
        metrics = GrantSuccessMetrics.query.filter_by(
            period='all-time',
            period_key='all-time'
        ).first()
        
        if not metrics or not metrics.categories:
            return {"success": True, "categories": [], "metrics": []}
        
        categories = []
        success_rates = []
        counts = []
        
        # Sort categories by success rate
        sorted_categories = sorted(
            metrics.categories.items(),
            key=lambda x: x[1].get('success_rate', 0),
            reverse=True
        )
        
        for category, data in sorted_categories:
            categories.append(category)
            success_rates.append(data.get('success_rate', 0))
            counts.append(data.get('submitted', 0))
        
        return {
            "success": True,
            "categories": categories,
            "metrics": {
                "success_rates": success_rates,
                "counts": counts
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving category comparison: {str(e)}")
        return {"success": False, "error": str(e)}


def get_grant_timeline(grant_id):
    """
    Get the timeline of status changes for a specific grant
    
    Args:
        grant_id (int): ID of the grant
    
    Returns:
        dict: Timeline data
    """
    try:
        # Get the grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return {"success": False, "error": "Grant not found"}
        
        # Get analytics entries for this grant
        entries = GrantAnalytics.query.filter_by(
            grant_id=grant_id
        ).order_by(GrantAnalytics.recorded_at).all()
        
        timeline = []
        for entry in entries:
            timeline.append({
                'date': entry.recorded_at.isoformat(),
                'status': entry.status,
                'previous_status': entry.previous_status,
                'metadata': entry.meta_data
            })
        
        return {
            "success": True,
            "grant_id": grant_id,
            "grant_title": grant.title,
            "timeline": timeline
        }
    
    except Exception as e:
        logger.error(f"Error retrieving grant timeline: {str(e)}")
        return {"success": False, "error": str(e)}


def create_report(grant_history):
    """
    Create an analytics report from grant history data using OpenAI
    
    Args:
        grant_history (list): List of grant history objects with focus_area, submitted_count, 
                             approved_count, and total_amount_awarded
    
    Returns:
        dict: Report data with summary text, chart data, and chart image
    """
    try:
        import json
        import os
        from openai import OpenAI
        
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        if not openai_client:
            logger.error("OpenAI API key not configured")
            return {
                "summary_text": "Could not generate report. OpenAI API key is not configured.",
                "chart_data": [],
                "chart_image_base64": None
            }
        
        # System prompt for OpenAI
        system_prompt = """You are an analytics AI. Input a JSON array of past grant outcomes each with:
1. focus_area
2. submitted_count
3. approved_count
4. total_amount_awarded
Return:
1. A summary paragraph of success rates
2. A JSON array for a bar chart with objects of focus_area and success_rate
3. A base64 encoded PNG chart image"""
        
        # Format grant_history for OpenAI
        input_data = json.dumps(grant_history)
        
        # Make API call to OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_data}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        # Parse the response
        # Typically the response would have three parts: summary text, JSON data, and base64 image
        # For simplicity, we'll extract these using basic string operations - in a real implementation
        # you might want more robust parsing
        
        # Initialize return values
        summary_text = ""
        chart_data = []
        chart_image_base64 = None
        
        # Parse the summary (first paragraph before any JSON or base64 data)
        if response_text:
            # Split by double newlines to find paragraphs
            parts = response_text.split("\n\n")
            if parts:
                summary_text = parts[0].strip()
            
            # Try to find JSON data
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                try:
                    chart_data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.error("Failed to parse chart data JSON from OpenAI response")
            
            # Try to find base64 image data
            base64_match = re.search(r'data:image\/png;base64,([A-Za-z0-9+/=]+)', response_text)
            if base64_match:
                chart_image_base64 = base64_match.group(1)
        
        return {
            "summary_text": summary_text,
            "chart_data": chart_data,
            "chart_image_base64": chart_image_base64
        }
        
    except Exception as e:
        logger.error(f"Error creating analytics report: {str(e)}")
        return {
            "summary_text": f"Error generating report: {str(e)}",
            "chart_data": [],
            "chart_image_base64": None
        }