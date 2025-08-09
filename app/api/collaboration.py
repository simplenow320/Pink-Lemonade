"""
Team Collaboration API
Comments, tasks, and activity feeds
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app import db
from app.models.grant import Grant
from app.models.user import User
import logging
import json

logger = logging.getLogger(__name__)

bp = Blueprint('collaboration', __name__, url_prefix='/api/collaboration')

# In-memory storage for collaboration features (should be in database in production)
comments_storage = {}
tasks_storage = {}
activity_feed = []

@bp.route('/grants/<int:grant_id>/comments', methods=['GET'])
def get_comments(grant_id):
    """Get comments for a grant"""
    try:
        grant = Grant.query.get_or_404(grant_id)
        comments = comments_storage.get(grant_id, [])
        
        return jsonify({
            'grant_id': grant_id,
            'comments': comments,
            'total': len(comments)
        })
        
    except Exception as e:
        logger.error(f"Error fetching comments: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/grants/<int:grant_id>/comments', methods=['POST'])
def add_comment(grant_id):
    """Add comment to a grant"""
    try:
        grant = Grant.query.get_or_404(grant_id)
        data = request.get_json()
        
        user_id = session.get('user_id', 'default')
        user = User.query.get(user_id) if user_id != 'default' else None
        
        comment = {
            'id': len(comments_storage.get(grant_id, [])) + 1,
            'grant_id': grant_id,
            'user_id': user_id,
            'username': user.username if user else 'Anonymous',
            'text': data.get('text'),
            'mentions': data.get('mentions', []),
            'created_at': datetime.now().isoformat(),
            'edited': False
        }
        
        # Store comment
        if grant_id not in comments_storage:
            comments_storage[grant_id] = []
        comments_storage[grant_id].append(comment)
        
        # Add to activity feed
        add_activity('comment', f"{comment['username']} commented on {grant.title}", grant_id)
        
        # Handle @mentions
        for mention in comment['mentions']:
            # Send notification to mentioned user
            logger.info(f"Notifying {mention} about comment")
        
        return jsonify({
            'success': True,
            'comment': comment
        })
        
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/grants/<int:grant_id>/tasks', methods=['GET'])
def get_tasks(grant_id):
    """Get tasks for a grant"""
    try:
        grant = Grant.query.get_or_404(grant_id)
        tasks = tasks_storage.get(grant_id, [])
        
        return jsonify({
            'grant_id': grant_id,
            'tasks': tasks,
            'total': len(tasks)
        })
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/grants/<int:grant_id>/tasks', methods=['POST'])
def create_task(grant_id):
    """Create task for a grant"""
    try:
        grant = Grant.query.get_or_404(grant_id)
        data = request.get_json()
        
        user_id = session.get('user_id', 'default')
        
        task = {
            'id': len(tasks_storage.get(grant_id, [])) + 1,
            'grant_id': grant_id,
            'title': data.get('title'),
            'description': data.get('description'),
            'assigned_to': data.get('assigned_to'),
            'due_date': data.get('due_date'),
            'status': 'pending',
            'created_by': user_id,
            'created_at': datetime.now().isoformat(),
            'completed_at': None
        }
        
        # Store task
        if grant_id not in tasks_storage:
            tasks_storage[grant_id] = []
        tasks_storage[grant_id].append(task)
        
        # Add to activity feed
        add_activity('task', f"New task created for {grant.title}", grant_id)
        
        return jsonify({
            'success': True,
            'task': task
        })
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark task as complete"""
    try:
        # Find task
        task_found = None
        grant_id = None
        
        for gid, tasks in tasks_storage.items():
            for task in tasks:
                if task['id'] == task_id:
                    task_found = task
                    grant_id = gid
                    break
        
        if not task_found:
            return jsonify({'error': 'Task not found'}), 404
        
        # Update task status
        task_found['status'] = 'completed'
        task_found['completed_at'] = datetime.now().isoformat()
        
        # Add to activity feed
        grant = Grant.query.get(grant_id)
        add_activity('task', f"Task completed for {grant.title if grant else 'grant'}", grant_id)
        
        return jsonify({
            'success': True,
            'task': task_found
        })
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/activity-feed', methods=['GET'])
def get_activity_feed():
    """Get recent activity feed"""
    try:
        # Get pagination
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # Calculate pagination
        start = (page - 1) * per_page
        end = start + per_page
        
        # Get paginated activities
        paginated = activity_feed[start:end]
        
        return jsonify({
            'activities': paginated,
            'total': len(activity_feed),
            'page': page,
            'pages': (len(activity_feed) + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Error fetching activity feed: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/calendar', methods=['GET'])
def get_calendar_events():
    """Get team calendar events"""
    try:
        # Get date range
        start_date = request.args.get('start', datetime.now().isoformat())
        end_date = request.args.get('end', (datetime.now() + timedelta(days=30)).isoformat())
        
        events = []
        
        # Add grant deadlines
        grants = Grant.query.filter(
            Grant.deadline != None,
            Grant.deadline >= datetime.fromisoformat(start_date),
            Grant.deadline <= datetime.fromisoformat(end_date)
        ).all()
        
        for grant in grants:
            events.append({
                'id': f'grant-{grant.id}',
                'title': f"Deadline: {grant.title}",
                'start': grant.deadline.isoformat(),
                'type': 'deadline',
                'grant_id': grant.id
            })
        
        # Add tasks with due dates
        for grant_id, tasks in tasks_storage.items():
            for task in tasks:
                if task.get('due_date'):
                    due = datetime.fromisoformat(task['due_date'])
                    if start_date <= task['due_date'] <= end_date:
                        events.append({
                            'id': f'task-{task["id"]}',
                            'title': task['title'],
                            'start': task['due_date'],
                            'type': 'task',
                            'grant_id': grant_id
                        })
        
        return jsonify({
            'events': events,
            'total': len(events)
        })
        
    except Exception as e:
        logger.error(f"Error fetching calendar: {e}")
        return jsonify({'error': str(e)}), 500

def add_activity(activity_type, description, grant_id=None):
    """Add item to activity feed"""
    activity = {
        'id': len(activity_feed) + 1,
        'type': activity_type,
        'description': description,
        'grant_id': grant_id,
        'timestamp': datetime.now().isoformat(),
        'user_id': session.get('user_id', 'default')
    }
    
    # Add to beginning of feed (most recent first)
    activity_feed.insert(0, activity)
    
    # Keep only last 100 activities
    if len(activity_feed) > 100:
        activity_feed.pop()
    
    return activity