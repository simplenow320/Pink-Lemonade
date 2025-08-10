"""
AI Prompter Self-Test API
Tests the prompt system with a simple case support generation
"""
from flask import Blueprint, jsonify
from app import db
from app.models import Organization
from app.services.ai_prompter import get_prompter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('ai_test', __name__)

@bp.route('/selftest', methods=['GET'])
def selftest():
    """
    Self-test the AI prompter system
    - Builds a tiny data_pack from current org
    - Runs case_support prompt with 300-500 word target
    - Verifies output contains "Source Notes" and no "Missing Info"
    - Returns test results
    """
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': [],
        'overall_status': 'PASS'
    }
    
    try:
        # 1. Get the first organization (or create test data)
        org = Organization.query.first()
        if not org:
            # Create minimal test org
            test_results['tests'].append({
                'name': 'Organization Data',
                'status': 'SKIP',
                'message': 'No organization found, using test data'
            })
            org_name = "Test Organization"
            org_mission = "We help communities thrive through education and support."
        else:
            org_name = org.name
            org_mission = org.mission or "Helping communities thrive."
            test_results['tests'].append({
                'name': 'Organization Data',
                'status': 'PASS',
                'message': f'Found org: {org_name}'
            })
        
        # 2. Build minimal data_pack
        data_pack = {
            'voice_profile': {
                'reading_level': 'grade 8-10',
                'formality': 3,
                'faith_language': 'no',
                'sentence_length': 'medium',
                'cta_style': 'Join us in making a difference'
            },
            'kpis': [
                {'metric': 'Families Served', 'value': 250, 'period': 'last 12 months'},
                {'metric': 'Programs Delivered', 'value': 15, 'period': 'last 12 months'}
            ],
            'testimonies': [
                {
                    'name': 'Maria S.',
                    'quote': 'This program changed my family\'s life. We now have stable housing and my children are thriving in school.',
                    'date': '2024-11'
                }
            ],
            'budget': {
                'total_annual': 500000,
                'program_percentage': 75,
                'admin_percentage': 15,
                'fundraising_percentage': 10
            }
        }
        
        # 3. Set up tokens
        tokens = {
            'org_name': org_name,
            'target_words': '400',
            'purpose': 'general support appeal'
        }
        
        # 4. Get prompter and run the prompt
        prompter = get_prompter()
        
        # Test prompt loading
        try:
            template = prompter.load_prompt_template('case_support')
            test_results['tests'].append({
                'name': 'Prompt Template Loading',
                'status': 'PASS',
                'message': 'Successfully loaded case_support.json'
            })
        except Exception as e:
            test_results['tests'].append({
                'name': 'Prompt Template Loading',
                'status': 'FAIL',
                'message': str(e)
            })
            test_results['overall_status'] = 'FAIL'
            
        # Test prompt execution
        result = prompter.run_prompt('case_support', tokens, data_pack)
        
        if result['success']:
            output = result['output']
            
            # Verify Source Notes present
            if 'Source Notes' in output:
                test_results['tests'].append({
                    'name': 'Source Notes Validation',
                    'status': 'PASS',
                    'message': 'Output contains required Source Notes'
                })
            else:
                test_results['tests'].append({
                    'name': 'Source Notes Validation',
                    'status': 'FAIL',
                    'message': 'Output missing required Source Notes'
                })
                test_results['overall_status'] = 'FAIL'
            
            # Verify no Missing Info
            if 'Missing Info' not in output and 'Missing Assets' not in output:
                test_results['tests'].append({
                    'name': 'Complete Information',
                    'status': 'PASS',
                    'message': 'No missing information detected'
                })
            else:
                test_results['tests'].append({
                    'name': 'Complete Information',
                    'status': 'FAIL',
                    'message': f'Missing items detected: {result["needs_input"]}'
                })
                test_results['overall_status'] = 'FAIL'
            
            # Check word count (approximate)
            word_count = len(output.split())
            if 350 <= word_count <= 450:
                test_results['tests'].append({
                    'name': 'Word Count',
                    'status': 'PASS',
                    'message': f'Word count: {word_count} (target: 400 ±50)'
                })
            else:
                test_results['tests'].append({
                    'name': 'Word Count',
                    'status': 'WARN',
                    'message': f'Word count: {word_count} (target: 400 ±50)'
                })
            
            # Store output sample
            test_results['output_sample'] = output[:500] + '...' if len(output) > 500 else output
            
        else:
            test_results['tests'].append({
                'name': 'Prompt Execution',
                'status': 'FAIL',
                'message': result.get('error', 'Unknown error')
            })
            test_results['overall_status'] = 'FAIL'
        
        # 5. Write test report
        report_path = 'web/tests/PROMPTS_TEST_REPORT.md'
        write_test_report(test_results, report_path)
        test_results['report_written'] = report_path
        
    except Exception as e:
        logger.error(f"Selftest error: {str(e)}")
        test_results['tests'].append({
            'name': 'System Error',
            'status': 'FAIL',
            'message': str(e)
        })
        test_results['overall_status'] = 'FAIL'
    
    return jsonify(test_results)

def write_test_report(results, filepath):
    """Write test results to markdown report"""
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        f.write("# AI Prompter Test Report\n\n")
        f.write(f"**Generated:** {results['timestamp']}\n\n")
        f.write(f"## Overall Status: {results['overall_status']}\n\n")
        
        f.write("## Test Results\n\n")
        for test in results['tests']:
            status_emoji = '✅' if test['status'] == 'PASS' else '❌' if test['status'] == 'FAIL' else '⚠️'
            f.write(f"- {status_emoji} **{test['name']}**: {test['status']}\n")
            f.write(f"  - {test['message']}\n")
        
        if 'output_sample' in results:
            f.write("\n## Output Sample\n\n")
            f.write("```\n")
            f.write(results['output_sample'])
            f.write("\n```\n")
        
        f.write("\n## Summary\n\n")
        if results['overall_status'] == 'PASS':
            f.write("✅ All tests passed. The AI prompter system is working correctly.\n")
        else:
            f.write("❌ Some tests failed. Please review the errors above.\n")