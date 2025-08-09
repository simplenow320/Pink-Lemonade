"""
Interactive Onboarding Journey Service
Manages user onboarding with character progression and achievements
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.models import User, UserProgress, Achievement, OnboardingStep
from app import db
import logging
import json

logger = logging.getLogger(__name__)

class OnboardingService:
    """Manages interactive onboarding journey with gamification"""
    
    # Character levels based on XP
    CHARACTER_LEVELS = [
        {'level': 1, 'title': 'Grant Seeker', 'xp_required': 0, 'icon': '🌱', 'color': '#9CA3AF'},
        {'level': 2, 'title': 'Grant Explorer', 'xp_required': 100, 'icon': '🔍', 'color': '#3B82F6'},
        {'level': 3, 'title': 'Grant Navigator', 'xp_required': 250, 'icon': '🧭', 'color': '#8B5CF6'},
        {'level': 4, 'title': 'Grant Strategist', 'xp_required': 500, 'icon': '📊', 'color': '#F59E0B'},
        {'level': 5, 'title': 'Grant Expert', 'xp_required': 1000, 'icon': '⭐', 'color': '#10B981'},
        {'level': 6, 'title': 'Grant Master', 'xp_required': 2000, 'icon': '👑', 'color': '#EF4444'},
        {'level': 7, 'title': 'Grant Champion', 'xp_required': 3500, 'icon': '🏆', 'color': '#6366F1'},
        {'level': 8, 'title': 'Grant Legend', 'xp_required': 5000, 'icon': '🌟', 'color': '#F97316'}
    ]
    
    # Onboarding journey steps
    ONBOARDING_STEPS = [
        {
            'id': 'welcome',
            'title': 'Welcome to Pink Lemonade',
            'description': 'Start your grant discovery journey',
            'xp_reward': 50,
            'icon': '👋',
            'category': 'getting_started',
            'order': 1,
            'tasks': [
                {'id': 'view_dashboard', 'title': 'View your dashboard', 'xp': 10},
                {'id': 'complete_profile', 'title': 'Complete your organization profile', 'xp': 40}
            ]
        },
        {
            'id': 'discover_grants',
            'title': 'Discover Your First Grant',
            'description': 'Learn how to find relevant grants',
            'xp_reward': 100,
            'icon': '🔍',
            'category': 'discovery',
            'order': 2,
            'tasks': [
                {'id': 'search_grants', 'title': 'Search for grants', 'xp': 20},
                {'id': 'use_filters', 'title': 'Apply filters to refine results', 'xp': 30},
                {'id': 'save_grant', 'title': 'Save your first grant', 'xp': 50}
            ]
        },
        {
            'id': 'ai_features',
            'title': 'Unlock AI Powers',
            'description': 'Use AI to enhance your grant applications',
            'xp_reward': 150,
            'icon': '🤖',
            'category': 'ai',
            'order': 3,
            'tasks': [
                {'id': 'ai_match', 'title': 'Get AI match scores', 'xp': 40},
                {'id': 'extract_grant', 'title': 'Extract grant from text/URL', 'xp': 50},
                {'id': 'generate_narrative', 'title': 'Generate your first narrative', 'xp': 60}
            ]
        },
        {
            'id': 'application_workflow',
            'title': 'Master the Workflow',
            'description': 'Track grants through the application process',
            'xp_reward': 200,
            'icon': '📝',
            'category': 'workflow',
            'order': 4,
            'tasks': [
                {'id': 'move_to_research', 'title': 'Move a grant to research phase', 'xp': 50},
                {'id': 'add_document', 'title': 'Upload a document', 'xp': 50},
                {'id': 'set_deadline', 'title': 'Set a deadline reminder', 'xp': 50},
                {'id': 'submit_application', 'title': 'Mark as submitted', 'xp': 50}
            ]
        },
        {
            'id': 'live_data',
            'title': 'Connect to Live Sources',
            'description': 'Fetch real grants from live data sources',
            'xp_reward': 250,
            'icon': '🌐',
            'category': 'advanced',
            'order': 5,
            'tasks': [
                {'id': 'fetch_live', 'title': 'Fetch grants from live sources', 'xp': 100},
                {'id': 'sync_sources', 'title': 'Sync all data sources', 'xp': 150}
            ]
        }
    ]
    
    # Achievements
    ACHIEVEMENTS = [
        {'id': 'first_login', 'name': 'Welcome Aboard', 'description': 'Complete your first login', 'xp': 25, 'icon': '🎉'},
        {'id': 'profile_complete', 'name': 'Identity Established', 'description': 'Complete your organization profile', 'xp': 50, 'icon': '✅'},
        {'id': 'first_save', 'name': 'Grant Collector', 'description': 'Save your first grant', 'xp': 30, 'icon': '📌'},
        {'id': 'five_saves', 'name': 'Grant Curator', 'description': 'Save 5 grants', 'xp': 75, 'icon': '📚'},
        {'id': 'first_ai_use', 'name': 'AI Pioneer', 'description': 'Use AI features for the first time', 'xp': 50, 'icon': '🤖'},
        {'id': 'first_submission', 'name': 'Application Submitted', 'description': 'Submit your first grant application', 'xp': 100, 'icon': '✉️'},
        {'id': 'week_streak', 'name': 'Dedicated Seeker', 'description': 'Login for 7 consecutive days', 'xp': 100, 'icon': '🔥'},
        {'id': 'high_match', 'name': 'Perfect Match', 'description': 'Find a grant with 5/5 match score', 'xp': 75, 'icon': '💯'},
        {'id': 'document_master', 'name': 'Document Master', 'description': 'Upload 10 documents', 'xp': 60, 'icon': '📄'},
        {'id': 'speed_reader', 'name': 'Speed Reader', 'description': 'Review 20 grants in one session', 'xp': 50, 'icon': '⚡'}
    ]
    
    def __init__(self):
        self.levels = self.CHARACTER_LEVELS
        self.steps = self.ONBOARDING_STEPS
        self.achievements = self.ACHIEVEMENTS
    
    def get_user_progress(self, user_id: int) -> Dict:
        """Get comprehensive user progress data"""
        try:
            # Get or create user progress
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            if not progress:
                progress = self.initialize_user_progress(user_id)
            
            # Calculate current level
            current_level = self.calculate_level(progress.total_xp)
            next_level = self.get_next_level(current_level['level'])
            
            # Get completed steps
            completed_steps = json.loads(progress.completed_steps) if progress.completed_steps else []
            
            # Get achievements
            user_achievements = json.loads(progress.achievements) if progress.achievements else []
            
            # Calculate progress percentage
            if next_level:
                xp_for_current = current_level['xp_required']
                xp_for_next = next_level['xp_required']
                xp_progress = progress.total_xp - xp_for_current
                xp_needed = xp_for_next - xp_for_current
                progress_percentage = int((xp_progress / xp_needed) * 100) if xp_needed > 0 else 100
            else:
                progress_percentage = 100
            
            return {
                'user_id': user_id,
                'total_xp': progress.total_xp,
                'current_level': current_level,
                'next_level': next_level,
                'progress_percentage': progress_percentage,
                'completed_steps': completed_steps,
                'achievements': user_achievements,
                'streak_days': progress.streak_days,
                'last_login': progress.last_login.isoformat() if progress.last_login else None,
                'onboarding_complete': progress.onboarding_complete,
                'character': {
                    'title': current_level['title'],
                    'icon': current_level['icon'],
                    'color': current_level['color'],
                    'level': current_level['level']
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            return {}
    
    def initialize_user_progress(self, user_id: int) -> UserProgress:
        """Initialize progress for new user"""
        try:
            progress = UserProgress()
            progress.user_id = user_id
            progress.total_xp = 0
            progress.current_level = 1
            progress.completed_steps = json.dumps([])
            progress.achievements = json.dumps([])
            progress.streak_days = 0
            progress.last_login = datetime.now()
            progress.onboarding_complete = False
            progress.created_at = datetime.now()
            
            db.session.add(progress)
            db.session.commit()
            
            # Award first login achievement
            self.award_achievement(user_id, 'first_login')
            
            return progress
            
        except Exception as e:
            logger.error(f"Error initializing user progress: {e}")
            db.session.rollback()
            return None
    
    def complete_task(self, user_id: int, step_id: str, task_id: str) -> Dict:
        """Mark a task as complete and award XP"""
        try:
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            if not progress:
                progress = self.initialize_user_progress(user_id)
            
            # Find the step and task
            step = next((s for s in self.steps if s['id'] == step_id), None)
            if not step:
                return {'success': False, 'error': 'Step not found'}
            
            task = next((t for t in step['tasks'] if t['id'] == task_id), None)
            if not task:
                return {'success': False, 'error': 'Task not found'}
            
            # Check if already completed
            completed_steps = json.loads(progress.completed_steps) if progress.completed_steps else []
            task_key = f"{step_id}.{task_id}"
            
            if task_key in completed_steps:
                return {'success': False, 'error': 'Task already completed'}
            
            # Award XP
            old_level = self.calculate_level(progress.total_xp)
            progress.total_xp += task['xp']
            new_level = self.calculate_level(progress.total_xp)
            
            # Mark as complete
            completed_steps.append(task_key)
            progress.completed_steps = json.dumps(completed_steps)
            
            # Check if step is fully complete
            step_complete = all(f"{step_id}.{t['id']}" in completed_steps for t in step['tasks'])
            
            # Award bonus XP for completing the step
            bonus_xp = 0
            if step_complete and f"{step_id}_complete" not in completed_steps:
                bonus_xp = step['xp_reward']
                progress.total_xp += bonus_xp
                completed_steps.append(f"{step_id}_complete")
                progress.completed_steps = json.dumps(completed_steps)
            
            # Check if leveled up
            leveled_up = new_level['level'] > old_level['level']
            
            progress.updated_at = datetime.now()
            db.session.commit()
            
            return {
                'success': True,
                'xp_earned': task['xp'] + bonus_xp,
                'total_xp': progress.total_xp,
                'step_complete': step_complete,
                'leveled_up': leveled_up,
                'new_level': new_level if leveled_up else None
            }
            
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def award_achievement(self, user_id: int, achievement_id: str) -> Dict:
        """Award an achievement to user"""
        try:
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            if not progress:
                progress = self.initialize_user_progress(user_id)
            
            # Find achievement
            achievement = next((a for a in self.achievements if a['id'] == achievement_id), None)
            if not achievement:
                return {'success': False, 'error': 'Achievement not found'}
            
            # Check if already earned
            user_achievements = json.loads(progress.achievements) if progress.achievements else []
            if achievement_id in user_achievements:
                return {'success': False, 'error': 'Achievement already earned'}
            
            # Award achievement
            old_level = self.calculate_level(progress.total_xp)
            progress.total_xp += achievement['xp']
            new_level = self.calculate_level(progress.total_xp)
            
            user_achievements.append(achievement_id)
            progress.achievements = json.dumps(user_achievements)
            
            leveled_up = new_level['level'] > old_level['level']
            
            progress.updated_at = datetime.now()
            db.session.commit()
            
            return {
                'success': True,
                'achievement': achievement,
                'xp_earned': achievement['xp'],
                'total_xp': progress.total_xp,
                'leveled_up': leveled_up,
                'new_level': new_level if leveled_up else None
            }
            
        except Exception as e:
            logger.error(f"Error awarding achievement: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def calculate_level(self, xp: int) -> Dict:
        """Calculate character level based on XP"""
        current_level = self.levels[0]
        for level in reversed(self.levels):
            if xp >= level['xp_required']:
                current_level = level
                break
        return current_level
    
    def get_next_level(self, current_level_num: int) -> Optional[Dict]:
        """Get the next level information"""
        if current_level_num < len(self.levels):
            return self.levels[current_level_num]  # Index is level - 1
        return None
    
    def get_onboarding_steps(self, user_id: int) -> List[Dict]:
        """Get onboarding steps with completion status"""
        try:
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            completed_steps = json.loads(progress.completed_steps) if progress and progress.completed_steps else []
            
            steps_with_status = []
            for step in self.steps:
                # Calculate task completion
                completed_tasks = []
                for task in step['tasks']:
                    task_key = f"{step['id']}.{task['id']}"
                    task_status = {
                        **task,
                        'completed': task_key in completed_steps
                    }
                    completed_tasks.append(task_status)
                
                # Check if step is complete
                step_complete = f"{step['id']}_complete" in completed_steps
                tasks_complete = all(t['completed'] for t in completed_tasks)
                
                steps_with_status.append({
                    **step,
                    'tasks': completed_tasks,
                    'completed': step_complete,
                    'progress': sum(1 for t in completed_tasks if t['completed']) / len(completed_tasks) * 100
                })
            
            return steps_with_status
            
        except Exception as e:
            logger.error(f"Error getting onboarding steps: {e}")
            return []
    
    def update_login_streak(self, user_id: int) -> Dict:
        """Update login streak and check for streak achievement"""
        try:
            progress = UserProgress.query.filter_by(user_id=user_id).first()
            if not progress:
                progress = self.initialize_user_progress(user_id)
            
            now = datetime.now()
            
            # Check if this is a consecutive day login
            if progress.last_login:
                days_since_last = (now.date() - progress.last_login.date()).days
                
                if days_since_last == 1:
                    # Consecutive day
                    progress.streak_days += 1
                elif days_since_last > 1:
                    # Streak broken
                    progress.streak_days = 1
                # If same day, don't update streak
            else:
                progress.streak_days = 1
            
            progress.last_login = now
            
            # Check for streak achievement
            achievement_awarded = None
            if progress.streak_days >= 7:
                result = self.award_achievement(user_id, 'week_streak')
                if result['success']:
                    achievement_awarded = result['achievement']
            
            db.session.commit()
            
            return {
                'success': True,
                'streak_days': progress.streak_days,
                'achievement_awarded': achievement_awarded
            }
            
        except Exception as e:
            logger.error(f"Error updating login streak: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

# Singleton instance
onboarding_service = OnboardingService()