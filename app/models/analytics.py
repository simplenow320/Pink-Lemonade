"""
Grant Analytics Model

This module contains models for tracking grant application outcomes and analytics.
"""

from app import db
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime

class GrantAnalytics(db.Model):
    """
    Model for tracking grant application outcomes and analytics
    Used for historical tracking and success rate analysis
    """
    __tablename__ = 'grant_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # Current status snapshot
    previous_status = db.Column(db.String(50))  # Previous status for tracking changes
    amount = db.Column(db.Float)  # Grant amount at time of recording
    date_submitted = db.Column(db.Date)  # When the grant was submitted
    date_decision = db.Column(db.Date)  # When a decision was received
    success = db.Column(db.Boolean)  # Whether the grant was successful (won)
    meta_data = db.Column(JSON, default=dict)  # Additional data like reviewers, reasons, etc.
    recorded_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship with Grant
    grant = db.relationship('Grant', backref=db.backref('analytics', cascade='all, delete-orphan'))
    
    def to_dict(self):
        """Convert analytics entry to dictionary"""
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'status': self.status,
            'previous_status': self.previous_status,
            'amount': self.amount,
            'date_submitted': self.date_submitted.isoformat() if self.date_submitted else None,
            'date_decision': self.date_decision.isoformat() if self.date_decision else None,
            'success': self.success,
            'meta_data': self.meta_data,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


class GrantSuccessMetrics(db.Model):
    """
    Model for storing aggregated grant success metrics to avoid recalculation
    """
    __tablename__ = 'grant_success_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    period = db.Column(db.String(20), nullable=False)  # 'monthly', 'quarterly', 'yearly'
    period_key = db.Column(db.String(20), nullable=False)  # e.g., '2025-05' for monthly, '2025-Q2' for quarterly
    total_submitted = db.Column(db.Integer, default=0)  # Total grants submitted in period
    total_won = db.Column(db.Integer, default=0)  # Total grants won in period
    total_declined = db.Column(db.Integer, default=0)  # Total grants declined in period
    total_funding_requested = db.Column(db.Float, default=0)  # Total funding requested in period
    total_funding_received = db.Column(db.Float, default=0)  # Total funding received in period
    success_rate = db.Column(db.Float, default=0)  # Percentage of successful applications
    avg_response_time = db.Column(db.Integer)  # Average days from submission to decision
    categories = db.Column(JSON, default=dict)  # Success metrics by focus area/category
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Convert metrics to dictionary"""
        return {
            'id': self.id,
            'period': self.period,
            'period_key': self.period_key,
            'total_submitted': self.total_submitted,
            'total_won': self.total_won,
            'total_declined': self.total_declined,
            'total_funding_requested': self.total_funding_requested,
            'total_funding_received': self.total_funding_received,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'categories': self.categories,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }