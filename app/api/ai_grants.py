"""
AI-Powered Grant Matching API Endpoints
Using REACTO structure for all AI operations
"""

from flask import Blueprint, jsonify, request, current_app, copy_current_request_context
from app.services.ai_grant_matcher import AIGrantMatcher
from app.services.historical_intelligence import get_intelligence_service
from app.models import Grant, Organization, db
import logging
from datetime import datetime
import time
import concurrent.futures
from functools import wraps

logger = logging.getLogger(__name__)

ai_grants_bp = Blueprint('ai_grants', __name__)

def run_with_flask_context(func, *args, **kwargs):
    """Run a function with Flask application context for ThreadPoolExecutor operations"""
    # Simplified approach: always use app context for threaded operations
    # This avoids complex request context copying issues while maintaining database access
    from flask import current_app
    app = current_app._get_current_object()  # Get the actual app instance
    
    with app.app_context():
        return func(*args, **kwargs)

def request_timeout_protection(max_seconds=6):
    """Decorator to ensure entire request never exceeds max_seconds with HARD timeout"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            import threading
            
            def timeout_handler(signum, frame):
                logger.error(f"HARD TIMEOUT - Request killed after {max_seconds}s to prevent worker timeout")
                raise TimeoutError(f"Request timeout after {max_seconds} seconds")
            
            start_time = time.time()
            try:
                # Set up hard timeout using signal (only works on main thread)
                if threading.current_thread() is threading.main_thread():
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(max_seconds)
                
                # Ensure Flask context is available
                from flask import current_app
                if not current_app:
                    logger.error("No Flask application context available")
                    return jsonify({
                        'success': False,
                        'error': 'Application context error',
                        'emergency_response': True
                    }), 500
                
                # Execute with Flask context preserved
                with current_app.app_context():
                    result = func(*args, **kwargs)
                
                total_time = time.time() - start_time
                logger.info(f"Request completed in {total_time:.2f}s (limit: {max_seconds}s)")
                
                return result
                
            except TimeoutError as e:
                total_time = time.time() - start_time
                logger.error(f"HARD TIMEOUT - Request killed after {total_time:.2f}s: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Request timeout - terminated to prevent worker timeout',
                    'emergency_response': True,
                    'system_status': 'hard_timeout'
                }), 504
            except Exception as e:
                total_time = time.time() - start_time
                logger.error(f"Request error after {total_time:.2f}s: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Internal server error',
                    'emergency_response': True,
                    'system_status': 'request_error'
                }), 500
            finally:
                # Cancel alarm if it was set
                if threading.current_thread() is threading.main_thread():
                    signal.alarm(0)
                    
        return wrapper
    return decorator

@ai_grants_bp.route('/match/<int:org_id>', methods=['GET', 'POST'])
@request_timeout_protection(max_seconds=6)  # CRITICAL: 6-second max for entire request
def get_ai_matched_grants(org_id):
    """Get AI-matched grants for an organization using REACTO with strict timeout protection"""
    request_start = time.time()
    try:
        # Initialize AI matcher
        matcher = AIGrantMatcher()
        
        # Use fast intelligence service with built-in resilience
        intelligence_service = get_intelligence_service()
        logger.info("Using fast historical intelligence service with caching and timeouts")
        
        # Check if organization exists
        org = Organization.query.get(org_id)
        if not org:
            # Try the organizations table instead
            from sqlalchemy import text
            result = db.session.execute(
                text("SELECT * FROM organizations WHERE id = :org_id"),
                {'org_id': org_id}
            ).first()
            
            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Organization not found'
                }), 404
            
            # Create org context from raw result
            org_context = {
                'name': result.name if hasattr(result, 'name') else 'Organization',
                'mission': result.mission if hasattr(result, 'mission') else '',
                'focus_areas': result.primary_focus_areas if hasattr(result, 'primary_focus_areas') else [],
                'geographic_focus': f"{result.primary_city if hasattr(result, 'primary_city') else ''}, {result.primary_state if hasattr(result, 'primary_state') else ''}",
                'annual_budget': result.annual_budget_range if hasattr(result, 'annual_budget_range') else 'Unknown'
            }
        else:
            org_context = org.to_ai_context()
        
        # Get grants for matching with smart limit for performance (<6 second requirement)
        # Restore full grant matching breadth - allow multiple grants while maintaining performance
        grants = Grant.query.limit(50).all()  # Process up to 50 grants with per-grant timeouts
        
        # Score each grant and gather historical intelligence
        matched_grants = []
        intelligence_metadata = {
            'intelligence_requests': 0,
            'intelligence_successes': 0,
            'intelligence_failures': 0,
            'intelligence_available_count': 0
        }
        
        for grant in grants:
            try:
                # Generate REACTO prompt and get match
                from app.services.reacto_prompts import ReactoPrompts
                prompts = ReactoPrompts()
                
                prompt = prompts.grant_matching_prompt(
                    org_context=org_context,
                    grant_data=grant.to_dict()
                )
                
                # Get AI response with Flask context protection (CRITICAL FIX)
                response = None
                start_time = time.time()
                try:
                    # Ensure we're in Flask app context for AI service
                    from flask import current_app
                    with current_app.app_context():
                        response = matcher.ai_service.generate_json_response(prompt)
                    ai_time = time.time() - start_time
                    logger.info(f"AI processing completed in {ai_time:.2f}s for grant {grant.id}")
                except Exception as e:
                    ai_time = time.time() - start_time
                    logger.warning(f"AI processing FAILED after {ai_time:.2f}s for grant {grant.id}: {str(e)} - using fallback")
                    # Use immediate error fallback
                    response = {
                        "match_score": 2,
                        "match_percentage": 40,
                        "verdict": "Error - Analysis failed",
                        "recommendation": "AI analysis failed. Manual review required.",
                        "key_alignments": ["System error occurred"],
                        "potential_challenges": ["AI service error"],
                        "next_steps": ["Manual review required", "Check system status"],
                        "application_tips": "Manual evaluation required due to system error",
                        "system_status": "api_error_fallback"
                    }
                
                if response and 'match_score' in response:
                    grant_dict = grant.to_dict()
                    grant_dict.update({
                        'match_score': response['match_score'],
                        'match_percentage': response.get('match_percentage', response['match_score'] * 20),
                        'match_verdict': response.get('verdict', 'Not Evaluated'),
                        'match_reason': response.get('recommendation', ''),
                        'key_alignments': response.get('key_alignments', []),
                        'potential_challenges': response.get('potential_challenges', []),
                        'next_steps': response.get('next_steps', []),
                        'application_tips': response.get('application_tips', '')
                    })
                    
                    # Add historical intelligence (safe implementation)
                    historical_intelligence = {
                        'analysis_period': '',
                        'generated_at': '',
                        'confidence_score': 0.0,
                        'intelligence_available': False,
                        'message': 'No funder information available'
                    }
                    
                    # Fast intelligence gathering with simplified approach (CRITICAL FIX)
                    if grant.funder and grant.funder.strip():
                        try:
                            intelligence_metadata['intelligence_requests'] += 1
                            current_year = datetime.now().year
                            intelligence_start = time.time()
                            
                            # Direct intelligence calls with Flask context preserved - simplified approach
                            try:
                                patterns = intelligence_service.analyze_funder_patterns(grant.funder, current_year)
                                insights = intelligence_service.generate_intelligence_insights(patterns, org_context)
                            except Exception as intel_error:
                                intel_time = time.time() - intelligence_start
                                logger.warning(f"Intelligence service failed after {intel_time:.2f}s for {grant.funder}: {str(intel_error)}")
                                patterns = {'intelligence_available': False, 'total_awards': 0}
                                insights = {'match_likelihood': 0, 'timing_recommendation': 'Service unavailable', 'strategic_actions': [], 'success_indicators': [], 'intelligence_summary': 'Service error'}
                            
                            # Populate with real data from service responses
                            if patterns.get('intelligence_available', False) or patterns.get('total_awards', 0) > 0:
                                historical_intelligence = {
                                    'analysis_period': patterns.get('analysis_period', f"{current_year-3}-{current_year}"),
                                    'generated_at': datetime.utcnow().isoformat() + 'Z',
                                    'confidence_score': patterns.get('confidence_score', 0.0),
                                    'intelligence_available': True,
                                    'total_awards': patterns.get('total_awards', 0),
                                    'average_amount': patterns.get('average_amount', 0),
                                    'typical_recipients': patterns.get('typical_recipients', []),
                                    'geographic_patterns': patterns.get('geographic_patterns', []),
                                    'award_timing': patterns.get('award_timing', []),
                                    'focus_areas': patterns.get('focus_areas', []),
                                    'match_likelihood': insights.get('match_likelihood', 0),
                                    'timing_recommendation': insights.get('timing_recommendation', ''),
                                    'strategic_actions': insights.get('strategic_actions', []),
                                    'success_indicators': insights.get('success_indicators', []),
                                    'intelligence_summary': insights.get('intelligence_summary', ''),
                                    'message': f"Historical analysis complete for {grant.funder}"
                                }
                                intelligence_metadata['intelligence_available_count'] += 1
                            else:
                                # No historical data found, but service responded
                                historical_intelligence = {
                                    'analysis_period': f"{current_year-3}-{current_year}",
                                    'generated_at': datetime.utcnow().isoformat() + 'Z',
                                    'confidence_score': 0.0,
                                    'intelligence_available': False,
                                    'message': f"No historical data found for funder '{grant.funder}' in past 3 years"
                                }
                            
                            intelligence_metadata['intelligence_successes'] += 1
                            
                        except Exception as e:
                            intelligence_metadata['intelligence_failures'] += 1
                            logger.warning(f"Historical intelligence gathering failed for funder '{grant.funder}': {str(e)}")
                            historical_intelligence['message'] = 'Intelligence system temporarily unavailable'
                    
                    grant_dict['historical_intelligence'] = historical_intelligence
                    matched_grants.append(grant_dict)
            except Exception as e:
                logger.error(f"Error matching grant {grant.id}: {str(e)}")
                # Add grant without score
                grant_dict = grant.to_dict()
                grant_dict['match_score'] = 0
                grant_dict['match_reason'] = 'Unable to score'
                matched_grants.append(grant_dict)
        
        # Sort by match score
        matched_grants.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'organization': org_context.get('name', 'Organization'),
            'total_grants': len(matched_grants),
            'matched_grants': matched_grants[:10],  # Top 10 matches
            'intelligence_metadata': {
                'intelligence_requests': intelligence_metadata.get('intelligence_requests', 0),
                'intelligence_successes': intelligence_metadata.get('intelligence_successes', 0), 
                'intelligence_failures': intelligence_metadata.get('intelligence_failures', 0),
                'intelligence_available_count': intelligence_metadata.get('intelligence_available_count', 0),
                'system_status': 'operational' if intelligence_service else 'disabled'
            }
        })
        
    except Exception as e:
        logger.error(f"Error in AI grant matching: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_grants_bp.route('/analyze/<int:grant_id>/<int:org_id>', methods=['GET', 'POST'])
def analyze_grant_fit(grant_id, org_id):
    """Get detailed AI analysis of grant-organization fit"""
    try:
        matcher = AIGrantMatcher()
        
        # Get grant and org
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        # Try to get organization
        org = Organization.query.get(org_id)
        if not org:
            # Create minimal context
            org_context = {
                'name': 'Organization',
                'mission': 'Not specified',
                'focus_areas': [],
                'geographic_focus': 'Not specified',
                'annual_budget': 'Unknown'
            }
        else:
            org_context = org.to_ai_context()
        
        # Generate detailed analysis
        from app.services.reacto_prompts import ReactoPrompts
        prompts = ReactoPrompts()
        
        # Get match analysis
        match_prompt = prompts.grant_matching_prompt(org_context, grant.to_dict())
        match_response = matcher.ai_service.generate_json_response(match_prompt)
        
        # Get intelligence analysis
        intelligence_prompt = prompts.grant_intelligence_prompt(
            f"{grant.title}\n{grant.eligibility or ''}\n{grant.source_url or ''}"
        )
        intelligence_response = matcher.ai_service.generate_json_response(intelligence_prompt)
        
        return jsonify({
            'success': True,
            'grant': grant.to_dict(),
            'organization': org_context.get('name'),
            'match_analysis': match_response or {},
            'intelligence': intelligence_response or {},
            'recommended_action': _determine_action(match_response.get('match_score', 0) if match_response else 0)
        })
        
    except Exception as e:
        logger.error(f"Error analyzing grant fit: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_grants_bp.route('/generate-narrative', methods=['POST'])
def generate_narrative():
    """Generate grant narrative section using REACTO"""
    try:
        data = request.get_json() or {}
        grant_id = data.get('grant_id')
        org_id = data.get('org_id')
        section = data.get('section', 'executive_summary')
        
        if not grant_id or not org_id:
            return jsonify({
                'success': False,
                'error': 'grant_id and org_id required'
            }), 400
        
        matcher = AIGrantMatcher()
        
        # Get grant
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'success': False, 'error': 'Grant not found'}), 404
        
        # Get organization context
        org = Organization.query.get(org_id)
        if not org:
            org_context = {
                'name': 'Organization',
                'mission': 'Not specified',
                'unique_capabilities': '',
                'unique_factors': {},
                'current_needs': 'General operating support'
            }
        else:
            org_context = org.to_ai_context()
        
        # Generate narrative
        from app.services.reacto_prompts import ReactoPrompts
        prompts = ReactoPrompts()
        
        prompt = prompts.narrative_generation_prompt(
            org_context=org_context,
            grant_data=grant.to_dict(),
            section=section
        )
        
        response = matcher.ai_service.generate_json_response(prompt)
        
        if response:
            return jsonify({
                'success': True,
                'section': section,
                'narrative': response.get('narrative_text', ''),
                'word_count': response.get('word_count', 0),
                'key_points': response.get('key_points_covered', []),
                'metrics': response.get('metrics_included', []),
                'suggestions': response.get('suggested_attachments', [])
            })
        
        return jsonify({
            'success': False,
            'error': 'Failed to generate narrative'
        }), 500
        
    except Exception as e:
        logger.error(f"Error generating narrative: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _determine_action(score):
    """Determine recommended action based on match score"""
    if score >= 4:
        return "Apply Immediately - Excellent match"
    elif score == 3:
        return "Consider Applying - Good potential"
    elif score == 2:
        return "Review Carefully - Some alignment"
    else:
        return "Skip - Poor match"