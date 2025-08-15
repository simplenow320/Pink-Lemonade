"""
Payment-related models for Phase 3
These models should be imported into main models.py
"""

from datetime import datetime
from app import db

class PaymentMethod(db.Model):
    """Store user payment methods"""
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_payment_method_id = db.Column(db.String(255))
    type = db.Column(db.String(50))  # card, bank_account
    last4 = db.Column(db.String(4))
    brand = db.Column(db.String(50))  # visa, mastercard, etc
    exp_month = db.Column(db.Integer)
    exp_year = db.Column(db.Integer)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'last4': self.last4,
            'brand': self.brand,
            'exp_month': self.exp_month,
            'exp_year': self.exp_year,
            'is_default': self.is_default
        }

class PaymentHistory(db.Model):
    """Track all payment transactions"""
    __tablename__ = 'payment_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_invoice_id = db.Column(db.String(255))
    stripe_payment_intent_id = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(50))  # succeeded, failed, pending, refunded
    description = db.Column(db.Text)
    failure_reason = db.Column(db.String(255))
    refund_amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Invoice(db.Model):
    """Store invoice records"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscriptions.id'))
    stripe_invoice_id = db.Column(db.String(255))
    invoice_number = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(50))  # draft, pending, paid, void
    due_date = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    pdf_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'amount': self.amount,
            'total_amount': self.total_amount or self.amount,
            'currency': self.currency,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }