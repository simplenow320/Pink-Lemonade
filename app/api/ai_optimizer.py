"""
AI Optimizer API - Test endpoint for cost optimization
Shows real-time cost savings from intelligent model routing
"""
from flask import Blueprint, jsonify, request
from app.services.ai_optimizer_service import ai_optimizer
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('ai_optimizer', __name__, url_prefix='/api/ai-optimizer')

@bp.route('/test-routing', methods=['POST'])
def test_routing():
    """
    Test the AI optimizer's intelligent model routing
    Shows which model would be used for different task types
    """
    try:
        data = request.get_json()
        task_type = data.get('task_type', 'summarize_grant')
        test_prompt = data.get('prompt', 'Summarize this grant opportunity in 2-3 sentences.')
        
        # Get routing decision without making actual API call
        complexity = ai_optimizer.determine_complexity(task_type, {})
        model, explanation = ai_optimizer.select_model(complexity)
        
        return jsonify({
            'success': True,
            'task_type': task_type,
            'complexity': complexity.value,
            'model_selected': model.value,
            'explanation': explanation,
            'estimated_cost_per_1k_tokens': {
                'gpt-3.5-turbo': '$0.0015',
                'gpt-4o': '$0.01',
                'savings': '85% cheaper with GPT-3.5-turbo'
            }
        })
        
    except Exception as e:
        logger.error(f"Error testing AI routing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/usage-report', methods=['GET'])
def get_usage_report():
    """
    Get detailed usage statistics and cost savings
    Shows how much money saved by intelligent routing
    """
    try:
        report = ai_optimizer.get_usage_report()
        
        return jsonify({
            'success': True,
            'usage_report': report,
            'message': 'Cost optimization report generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error getting usage report: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/test-tasks', methods=['GET'])
def test_different_tasks():
    """
    Test different task types to show routing decisions
    Demonstrates how the optimizer routes various grant tasks
    """
    test_cases = [
        # Simple tasks - should use GPT-3.5-turbo
        {'task': 'summarize_grant', 'description': 'Summarize grant in 2-3 sentences'},
        {'task': 'extract_keywords', 'description': 'Extract key terms from grant'},
        {'task': 'classify_grant_type', 'description': 'Categorize grant type'},
        
        # Moderate tasks - should use GPT-3.5-turbo
        {'task': 'generate_outline', 'description': 'Create grant proposal outline'},
        {'task': 'create_checklist', 'description': 'Generate submission checklist'},
        
        # Complex tasks - should use GPT-4o
        {'task': 'generate_narrative', 'description': 'Write full grant narrative'},
        {'task': 'create_reacto_prompt', 'description': 'Generate REACTO prompt'},
        {'task': 'write_case_support', 'description': 'Write case for support'},
        
        # Critical tasks - should use GPT-4o
        {'task': 'score_grant_match', 'description': 'Score grant-org alignment'},
        {'task': 'analyze_grant_fit', 'description': 'Deep grant fit analysis'}
    ]
    
    results = []
    for test in test_cases:
        complexity = ai_optimizer.determine_complexity(test['task'], {})
        model, explanation = ai_optimizer.select_model(complexity)
        
        results.append({
            'task': test['task'],
            'description': test['description'],
            'complexity': complexity.value,
            'model': model.value,
            'cost_per_1k': '$0.0015' if model.value == 'gpt-3.5-turbo' else '$0.01'
        })
    
    # Calculate potential savings
    turbo_count = sum(1 for r in results if r['model'] == 'gpt-3.5-turbo')
    gpt4_count = len(results) - turbo_count
    
    return jsonify({
        'success': True,
        'test_results': results,
        'summary': {
            'total_tasks': len(results),
            'using_turbo_35': turbo_count,
            'using_gpt_4o': gpt4_count,
            'cost_optimization': f'{(turbo_count/len(results)*100):.0f}% of tasks use cheaper model',
            'estimated_savings': '30-60% reduction in AI costs'
        }
    })

@bp.route('/execute-with-optimizer', methods=['POST'])
def execute_with_optimizer():
    """
    Execute an actual AI request using the optimizer
    Shows real cost savings in action
    """
    try:
        data = request.get_json()
        task_type = data.get('task_type', 'summarize_grant')
        prompt = data.get('prompt', 'Summarize this grant opportunity focusing on eligibility.')
        
        # Execute request through optimizer
        result = ai_optimizer.optimize_request(
            task_type=task_type,
            prompt=prompt,
            context={'max_tokens': 500}
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'result': result.get('content'),
                'model_used': result.get('model_used'),
                'explanation': result.get('explanation'),
                'tokens_used': result.get('tokens_used'),
                'estimated_cost': result.get('estimated_cost'),
                'task_type': task_type
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error'),
                'model_attempted': result.get('model_attempted')
            }), 500
            
    except Exception as e:
        logger.error(f"Error executing with optimizer: {str(e)}")
        return jsonify({'error': str(e)}), 500