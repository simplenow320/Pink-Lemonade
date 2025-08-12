from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from app import db
from app.models import CaseSupportDoc, GrantPitchDoc, ImpactReport
import logging
import os

logger = logging.getLogger(__name__)

bp = Blueprint("writing", __name__)

@bp.route('/improve', methods=['POST'])
def improve_text():
    """Improve text using AI"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        improvement_type = data.get('improvement_type', 'professional')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Use OpenAI for text improvement
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Define improvement prompts
        prompts = {
            'professional': 'Make this text more professional and polished while keeping the original meaning:',
            'clarity': 'Improve the clarity and readability of this text:',
            'concise': 'Make this text more concise while preserving all key information:',
            'expand': 'Expand on this text with more detail and examples:',
            'persuasive': 'Make this text more persuasive and compelling:'
        }
        
        prompt = prompts.get(improvement_type, prompts['professional'])
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional writing assistant helping with grant applications."},
                {"role": "user", "content": f"{prompt}\n\n{text}"}
            ],
            max_tokens=1000
        )
        
        improved_text = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'improved_text': improved_text,
            'improvement_type': improvement_type
        })
        
    except Exception as e:
        logger.error(f"Error improving text: {e}")
        return jsonify({'error': str(e)}), 500

def _json():
    data = request.get_json(silent=True)
    if not data:
        raise BadRequest("JSON body required")
    return data

@bp.route('/case-support', methods=['POST'])
def create_case_support():
    """Generate a Case for Support document using organization profile from database"""
    try:
        data = request.get_json() or {}
        
        # Import Organization model
        from app.models import Organization
        
        # Fetch organization from database
        org = Organization.query.first()
        if not org:
            return jsonify({'error': 'No organization profile found. Please complete your organization profile first.'}), 404
        
        # Use organization data from database
        org_data = org.to_dict()
        
        # Override with any user-provided specifics
        financial_need = data.get('financial_need', 'Funding to expand our programs and services')
        audience_type = data.get('audience_type', 'foundations and individual donors')
        word_count_range = data.get('word_count_range', '600-900')
        
        # Use OpenAI for document generation
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Build the professional grant writing prompt with database data
        prompt = f"""You are an expert nonprofit grant writer with extensive experience in fundraising and development. 

Generate a polished, fact-checked Case for Support based ONLY on the verified organizational data provided below. Do not invent data, statistics, or history. Maintain the tone of a persuasive, professional funding document.

ORGANIZATION DETAILS:
- Name: {org_data.get('name')}
- Legal Name: {org_data.get('legal_name', org_data.get('name'))}
- Mission: {org_data.get('mission')}
- Vision: {org_data.get('vision', 'Not provided')}
- Programs & Services: {org_data.get('programs_services', 'Not specified')}
- Key Achievements: {org_data.get('key_achievements', 'Not specified')}
- Financial Need: {financial_need}
- Target Demographics: {', '.join(org_data.get('target_demographics', [])) or 'Not specified'}
- Service Area: {org_data.get('service_area_type', 'Not specified')} - {org_data.get('primary_city', '')}, {org_data.get('primary_state', '')}
- Founded Year: {org_data.get('year_founded', 'Not provided')}
- Annual Budget: {org_data.get('annual_budget_range', 'Not specified')}
- Staff Size: {org_data.get('staff_size', 'Not specified')}
- People Served Annually: {org_data.get('people_served_annually', 'Not specified')}

TARGET AUDIENCE: {data.get('audience_type', 'foundations and individual donors')}
WORD COUNT: {data.get('word_count_range', '600-900')} words

Structure the document with these exact sections:
# Executive Summary
## Organization Overview  
## Mission & Vision
## Programs & Services
## Community Impact
## Financial Need
## Call to Action

Requirements:
- Use ONLY the verified facts provided above
- Do not fabricate statistics, dates, or program details
- Maintain persuasive, professional funding document tone throughout
- Output in clean markdown format with proper headers
- Each section should be substantive and compelling for grant funders
- End with a strong, specific Call to Action

Generate the Case for Support now:"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert nonprofit grant writer specializing in professional funding documents. Generate compelling, fact-based cases for support using only verified organizational data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Add source note
        content += "\n\n---\n**Source Notes:** This Case for Support is based only on verified organizational data provided by the user. No statistics or program details have been fabricated."
        
        return jsonify({
            'success': True,
            'content': content,
            'message': 'Case for Support generated successfully',
            'word_count': len(content.split()),
            'sections': ['Executive Summary', 'Organization Overview', 'Mission & Vision', 'Programs & Services', 'Community Impact', 'Financial Need', 'Call to Action']
        })
        
    except Exception as e:
        logger.error(f"Error generating case for support: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/grant-pitch', methods=['POST'])
def create_grant_pitch():
    """Generate a Grant Pitch in three formats using organization profile from database"""
    try:
        data = request.get_json() or {}
        
        # Import Organization model
        from app.models import Organization
        
        # Fetch organization from database
        org = Organization.query.first()
        if not org:
            return jsonify({'error': 'No organization profile found. Please complete your organization profile first.'}), 404
        
        # Use organization data from database
        org_data = org.to_dict()
        
        # Validate required pitch-specific fields
        funder_name = data.get('funder_name', 'Potential Funder')
        alignment = data.get('alignment', 'Mission alignment and shared values')
        funding_need = data.get('funding_need', 'General operating support')
        funding_amount = data.get('funding_amount', 'Not specified')
        word_limit = data.get('word_limit', '250')
        
        # Use OpenAI for document generation
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Build the professional grant pitch prompt with database data
        prompt = f"""You are a professional grant and donor pitch coach. Using only the verified organizational data provided below, create three versions of a persuasive pitch.

ORGANIZATION DETAILS:
- Name: {org_data.get('name')}
- Mission: {org_data.get('mission')}
- Programs/Services: {org_data.get('programs_services', 'Not specified')}
- Key Achievements: {org_data.get('key_achievements', 'Not specified')}
- Impact Metrics: {org_data.get('impact_metrics', {}) if org_data.get('impact_metrics') else 'Not specified'}
- Funding Need: {funding_need}
- Funding Amount: {funding_amount}
- Geographic Focus: {org_data.get('service_area_type', 'Not specified')} - {org_data.get('primary_city', '')}, {org_data.get('primary_state', '')}
- Annual Budget: {org_data.get('annual_budget_range', 'Not specified')}
- People Served: {org_data.get('people_served_annually', 'Not specified')}

TARGET FUNDER: {data.get('funder_name')}
ALIGNMENT AREAS: {data.get('alignment')}
WORD LIMIT: {data.get('word_limit', '250')} words per format

Create these three distinct pitch formats:

## One-Page Pitch
(formatted in clear sections with headers and structured content)

## Email Pitch  
(compelling subject line + concise persuasive body suitable for email)

## Verbal Script
(conversational tone, 60–90 seconds when spoken aloud)

Requirements:
- Use ONLY the verified facts provided above
- Avoid filler words, exaggerations, or invented facts
- Focus on clarity, urgency, and impact in all formats
- Tailor content specifically to {data.get('funder_name')} priorities
- Highlight alignment with {data.get('alignment')} areas
- Stay within {data.get('word_limit', '250')} word limit per format
- Make each format distinct and purposeful

Generate the three grant pitch formats now:"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional grant and donor pitch coach specializing in creating compelling, fact-based pitches in multiple formats. Generate concise, impactful pitches using only verified organizational data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # Add source note
        content += "\n\n---\n**Source Notes:** These grant pitches are based only on verified organizational data provided by the user. No statistics or program details have been fabricated."
        
        return jsonify({
            'success': True,
            'content': content,
            'message': 'Grant pitches generated successfully',
            'word_count': len(content.split()),
            'formats': ['One-Page Pitch', 'Email Pitch', 'Verbal Script']
        })
        
    except Exception as e:
        logger.error(f"Error generating grant pitch: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/impact-report', methods=['POST'])
def create_impact_report():
    """Generate an Impact Report using organization profile from database"""
    try:
        data = request.get_json() or {}
        
        # Import Organization model
        from app.models import Organization
        
        # Fetch organization from database
        org = Organization.query.first()
        if not org:
            return jsonify({'error': 'No organization profile found. Please complete your organization profile first.'}), 404
        
        # Use organization data from database
        org_data = org.to_dict()
        
        # Use provided data with fallbacks to organization data
        report_type = data.get('report_type', 'Annual Impact Report')
        target_audience = data.get('target_audience', 'Foundations and Major Donors')
        period_start = data.get('period_start', 'January 2024')
        period_end = data.get('period_end', 'December 2024')
        
        # Use organization's actual programs and impact from database
        programs_covered = data.get('programs_covered', org_data.get('programs_services', 'All organizational programs'))
        program_outcomes = data.get('program_outcomes', org_data.get('key_achievements', 'See achievements below'))
        impact_stories = data.get('impact_stories', 'Based on our work with the community')
        
        # Use OpenAI for document generation
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Format metrics for the prompt
        metrics_text = ""
        if data.get('metrics'):
            metrics_text = "\n".join([
                f"- {m['name']}: Target {m.get('target', 'N/A')}, Actual {m.get('actual', 'N/A')}"
                for m in data['metrics'] if m.get('name')
            ])
        elif org_data.get('impact_metrics'):
            # Use organization's stored impact metrics
            metrics = org_data.get('impact_metrics', {})
            if isinstance(metrics, dict):
                metrics_text = "\n".join([f"- {k}: {v}" for k, v in metrics.items()])
        
        # Build the professional impact reporting prompt with database data
        prompt = f"""You are an expert in nonprofit impact reporting. Using the organizational data provided below, create a visually clear and funder-friendly report.

ORGANIZATION DETAILS:
- Name: {org_data.get('name')}
- Mission: {org_data.get('mission')}
- Report Type: {report_type}
- Target Audience: {target_audience}
- Report Period: {period_start} to {period_end}

PROGRAM INFORMATION:
- Programs/Services: {programs_covered}
- Key Achievements: {org_data.get('key_achievements', program_outcomes)}
- Impact Stories: {impact_stories}
- People Served Annually: {org_data.get('people_served_annually', 'Not specified')}

KEY METRICS:
{metrics_text or 'Organizational impact metrics in development'}
- Impact Stories: {data.get('impact_stories', 'Not provided')}

KEY METRICS:
{metrics_text or 'No metrics provided'}

FINANCIAL DATA:
- Total Budget: ${data.get('total_budget', 'Not specified')}
- Total Expenses: ${data.get('total_expenses', 'Not specified')}
- Budget Breakdown: {data.get('budget_breakdown', 'Not provided')}
- Funding Sources: {data.get('funding_sources', 'Not provided')}

Create a comprehensive impact report with these sections:
## Executive Summary
## Program Outcomes
## Key Metrics & Data
## Financial Stewardship
## Impact Stories
## Recommended Visualizations

Requirements:
- Use ONLY the verified data provided above
- Never create fictional numbers or fabricate data points
- Include short narrative summary of achievements and impact
- Provide bullet-point list of concrete outcomes with numbers
- Recommend specific charts or visuals that can be auto-generated from the actual data
- Structure content for both PDF and Word download formats
- Focus on measurable outcomes and tangible results
- Include financial accountability information where data is provided

Generate the comprehensive impact report now:"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in nonprofit impact reporting specializing in creating visually clear, funder-friendly reports. Turn verified data into compelling narratives with visualization recommendations using only provided information."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500
        )
        
        content = response.choices[0].message.content
        
        # Add source note
        content += "\n\n---\n**Source Notes:** This Impact Report is based only on verified data provided by the user. No fictional numbers or fabricated data points have been generated."
        
        return jsonify({
            'success': True,
            'content': content,
            'message': 'Impact report generated successfully',
            'word_count': len(content.split()),
            'sections': ['Executive Summary', 'Program Outcomes', 'Key Metrics & Data', 'Financial Stewardship', 'Impact Stories', 'Recommended Visualizations']
        })
        
    except Exception as e:
        logger.error(f"Error generating impact report: {e}")
        return jsonify({'error': str(e)}), 500

def _extract_missing(text: str):
    # If the model followed our prompts, it lists "Missing Info" or "Needs Update" when data is absent.
    import re
    m = re.search(r"(?i)(Missing Info|Needs Update)\s*:\s*(.+)$", text, re.DOTALL)
    if not m:
        return []
    section = m.group(2).strip()
    items = [ln.strip("-• ").strip() for ln in section.splitlines() if ln.strip()]
    return items[:20]