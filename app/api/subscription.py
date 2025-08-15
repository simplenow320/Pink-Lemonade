"""
Subscription Management API Endpoints
Phase 2: Authentication & User Management
"""

from flask import Blueprint, jsonify, request, session
from app import db
from app.services.subscription_service import SubscriptionService
from app.services.rbac_service import RBACService, require_permission, require_role
from app.api.auth import login_required
import logging

logger = logging.getLogger(__name__)

# Create blueprint
subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscription')

# Initialize services
subscription_service = SubscriptionService()

@subscription_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get all available subscription plans"""
    try:
        plans = subscription_service.get_available_plans()
        
        return jsonify({
            'success': True,
            'plans': plans,
            'comparison_message': 'Our plans are 25-67% cheaper than competitors!',
            'savings_highlights': {
                'vs_instrumentl': 'Save up to 67% compared to Instrumentl ($999/mo)',
                'vs_grantscope': 'Save up to 50% compared to GrantScope ($500/mo)',
                'vs_grantstation': 'Save up to 40% compared to GrantStation ($299/mo)'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting plans: {e}")
        return jsonify({'error': 'Failed to get subscription plans'}), 500

@subscription_bp.route('/current', methods=['GET'])
@login_required
def get_current_subscription():
    """Get current user's subscription details"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get subscription details
        from app.models import UserSubscription
        subscription = UserSubscription.query.filter_by(user_id=user_id).first()
        
        if not subscription:
            # Create trial subscription if none exists
            subscription = subscription_service.create_trial_subscription(user_id)
        
        # Get usage summary
        usage_summary = subscription_service.get_usage_summary(user_id)
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict() if subscription else None,
            'usage': usage_summary
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        return jsonify({'error': 'Failed to get subscription details'}), 500

@subscription_bp.route('/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    """Upgrade or downgrade subscription plan"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        new_plan_tier = data.get('plan_tier')
        if not new_plan_tier:
            return jsonify({'error': 'Plan tier required'}), 400
        
        result = subscription_service.upgrade_subscription(user_id, new_plan_tier)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        return jsonify({'error': 'Failed to upgrade subscription'}), 500

@subscription_bp.route('/usage', methods=['GET'])
@login_required
def get_usage():
    """Get detailed usage statistics"""
    try:
        user_id = session.get('user_id')
        usage_summary = subscription_service.get_usage_summary(user_id)
        
        return jsonify({
            'success': True,
            'usage': usage_summary
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting usage: {e}")
        return jsonify({'error': 'Failed to get usage data'}), 500

@subscription_bp.route('/track-usage', methods=['POST'])
@login_required
def track_usage():
    """Track feature usage (internal endpoint)"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        feature_type = data.get('feature_type')
        if not feature_type:
            return jsonify({'error': 'Feature type required'}), 400
        
        # Track the usage
        success = subscription_service.track_usage(
            user_id=user_id,
            feature_type=feature_type,
            feature_name=data.get('feature_name'),
            ai_model_used=data.get('ai_model_used'),
            ai_tokens_used=data.get('ai_tokens_used'),
            ai_cost_estimate=data.get('ai_cost_estimate'),
            metadata=data.get('metadata')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Usage tracked'}), 200
        else:
            return jsonify({'error': 'Failed to track usage'}), 400
            
    except Exception as e:
        logger.error(f"Error tracking usage: {e}")
        return jsonify({'error': 'Failed to track usage'}), 500

@subscription_bp.route('/check-feature/<feature>', methods=['GET'])
@login_required
def check_feature_access(feature):
    """Check if user has access to a specific feature"""
    try:
        user_id = session.get('user_id')
        has_access = subscription_service.check_feature_access(user_id, feature)
        
        return jsonify({
            'success': True,
            'feature': feature,
            'has_access': has_access
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        return jsonify({'error': 'Failed to check feature access'}), 500

# Team management endpoints
@subscription_bp.route('/team/members', methods=['GET'])
@login_required
@require_permission('team.manage')
def get_team_members():
    """Get team members for organization"""
    try:
        organization_id = session.get('organization_id')
        if not organization_id:
            return jsonify({'error': 'No organization selected'}), 400
        
        from app.models import TeamMember
        members = TeamMember.query.filter_by(
            organization_id=organization_id,
            is_active=True
        ).all()
        
        return jsonify({
            'success': True,
            'members': [member.to_dict() for member in members]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting team members: {e}")
        return jsonify({'error': 'Failed to get team members'}), 500

@subscription_bp.route('/team/invite', methods=['POST'])
@login_required
@require_permission('team.invite')
def invite_team_member():
    """Invite a new team member"""
    try:
        user_id = session.get('user_id')
        organization_id = session.get('organization_id')
        data = request.get_json()
        
        email = data.get('email')
        role = data.get('role', 'member')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Check subscription limits
        from app.models import UserSubscription
        subscription = UserSubscription.query.filter_by(user_id=user_id).first()
        if subscription and subscription.plan:
            from app.models import TeamMember
            current_members = TeamMember.query.filter_by(
                organization_id=organization_id,
                is_active=True
            ).count()
            
            if current_members >= subscription.plan.max_users:
                return jsonify({
                    'error': f'Team member limit reached ({subscription.plan.max_users}). Upgrade to add more members.'
                }), 400
        
        # Create invitation (simplified for now)
        return jsonify({
            'success': True,
            'message': f'Invitation sent to {email}',
            'note': 'Full email integration pending'
        }), 200
        
    except Exception as e:
        logger.error(f"Error inviting team member: {e}")
        return jsonify({'error': 'Failed to invite team member'}), 500

# Permission check endpoints
@subscription_bp.route('/permissions', methods=['GET'])
@login_required
def get_user_permissions():
    """Get current user's permissions"""
    try:
        user_id = session.get('user_id')
        organization_id = session.get('organization_id')
        
        permissions = RBACService.get_user_permissions(user_id, organization_id)
        
        return jsonify({
            'success': True,
            'permissions': permissions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting permissions: {e}")
        return jsonify({'error': 'Failed to get permissions'}), 500

@subscription_bp.route('/role/assign', methods=['POST'])
@login_required
@require_role('admin')
def assign_role():
    """Assign role to a user"""
    try:
        assigner_id = session.get('user_id')
        organization_id = session.get('organization_id')
        data = request.get_json()
        
        target_user_id = data.get('user_id')
        new_role = data.get('role')
        
        if not target_user_id or not new_role:
            return jsonify({'error': 'User ID and role required'}), 400
        
        result = RBACService.assign_role(
            user_id=target_user_id,
            role=new_role,
            organization_id=organization_id,
            assigned_by_user_id=assigner_id
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error assigning role: {e}")
        return jsonify({'error': 'Failed to assign role'}), 500