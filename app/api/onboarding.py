"""
Onboarding API endpoints for gamified journey
"""
from flask import Blueprint, request, jsonify, session
from app.services.onboarding_service import onboarding_service
from app import db
import logging

logger = logging.getLogger(__name__)

onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route('/api/onboarding/progress', methods=['GET'])
def get_progress():
    """Get user's onboarding progress and character info"""
    try:
        # Get user ID from session or default to 1 for testing
        user_id = session.get('user_id', 1)
        
        progress = onboarding_service.get_user_progress(user_id)
        
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/steps', methods=['GET'])
def get_steps():
    """Get onboarding steps with completion status"""
    try:
        user_id = session.get('user_id', 1)
        
        steps = onboarding_service.get_onboarding_steps(user_id)
        
        return jsonify({
            'success': True,
            'steps': steps
        })
    except Exception as e:
        logger.error(f"Error getting steps: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/complete-task', methods=['POST'])
def complete_task():
    """Mark a task as complete and award XP"""
    try:
        data = request.json
        user_id = session.get('user_id', 1)
        step_id = data.get('step_id')
        task_id = data.get('task_id')
        
        if not step_id or not task_id:
            return jsonify({'success': False, 'error': 'Missing step_id or task_id'}), 400
        
        result = onboarding_service.complete_task(user_id, step_id, task_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/award-achievement', methods=['POST'])
def award_achievement():
    """Award an achievement to user"""
    try:
        data = request.json
        user_id = session.get('user_id', 1)
        achievement_id = data.get('achievement_id')
        
        if not achievement_id:
            return jsonify({'success': False, 'error': 'Missing achievement_id'}), 400
        
        result = onboarding_service.award_achievement(user_id, achievement_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error awarding achievement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/update-streak', methods=['POST'])
def update_streak():
    """Update login streak"""
    try:
        user_id = session.get('user_id', 1)
        
        result = onboarding_service.update_login_streak(user_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error updating streak: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@onboarding_bp.route('/api/onboarding/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top users by XP"""
    try:
        from app.models import UserProgress, User
        
        # Get top 10 users by XP
        top_users = db.session.query(
            UserProgress, User
        ).join(
            User, UserProgress.user_id == User.id
        ).order_by(
            UserProgress.total_xp.desc()
        ).limit(10).all()
        
        leaderboard = []
        for progress, user in top_users:
            level = onboarding_service.calculate_level(progress.total_xp)
            leaderboard.append({
                'username': user.username,
                'total_xp': progress.total_xp,
                'level': level['level'],
                'title': level['title'],
                'icon': level['icon']
            })
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        })
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500