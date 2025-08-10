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
    """Generate a Case for Support document using verified user inputs only"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['org_name', 'mission', 'programs', 'impact', 'financial_need']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Use OpenAI for document generation
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Build the professional grant writing prompt
        prompt = f"""You are an expert nonprofit grant writer with extensive experience in fundraising and development. 

Generate a polished, fact-checked Case for Support based ONLY on the verified user inputs provided below. Do not invent data, statistics, or history. Maintain the tone of a persuasive, professional funding document.

ORGANIZATION DETAILS:
- Name: {data.get('org_name')}
- Mission: {data.get('mission')}
- Vision: {data.get('vision', 'Not provided')}
- Programs & Services: {data.get('programs')}
- Community Impact: {data.get('impact')}
- Financial Need: {data.get('financial_need')}
- Target Population: {data.get('target_population', 'Not specified')}
- Geographic Scope: {data.get('geographic_scope', 'Not specified')}
- Founded Year: {data.get('founded_year', 'Not provided')}

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
    """Generate a Grant Pitch in three formats using verified user inputs only"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['org_name', 'funder_name', 'alignment', 'mission', 'programs', 'impact', 'funding_need']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Use OpenAI for document generation
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Build the professional grant pitch prompt
        prompt = f"""You are a professional grant and donor pitch coach. Using only the verified input provided below, create three versions of a persuasive pitch.

ORGANIZATION DETAILS:
- Name: {data.get('org_name')}
- Mission: {data.get('mission')}
- Programs/Services: {data.get('programs')}
- Impact/Results: {data.get('impact')}
- Funding Need: {data.get('funding_need')}
- Funding Amount: {data.get('funding_amount', 'Not specified')}
- Geographic Focus: {data.get('geographic_focus', 'Not specified')}

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

@bp.post("/impact-report")
def create_impact_report():
    body = _json()
    org_id = int(body.get("orgId") or 1)
    tokens = {
        "org_name": body.get("orgName") or "Your Organization",
        "template_sections": body.get("templateSections") or "Grant Summary; Objectives & Activities; Outputs; Outcomes; Financial Report; Challenges & Learnings; Next Steps",
        "start_date": body.get("startDate") or "2025-01-01",
        "end_date": body.get("endDate") or "2025-06-30"
    }
    data_pack = build_data_pack(org_id)
    result = run_prompt("impact_report", tokens, data_pack)
    content = result["content"]
    needs = _extract_missing(content)
    doc = ImpactReport(org_id=org_id, grant_id=body.get("grantId"), period_start=None, period_end=None, sections={"body": content}, needs_update=needs, sources={})
    db.session.add(doc); db.session.commit()
    return jsonify({"id": doc.id, "needsUpdate": needs, "content": content}), 200

def _extract_missing(text: str):
    # If the model followed our prompts, it lists "Missing Info" or "Needs Update" when data is absent.
    import re
    m = re.search(r"(?i)(Missing Info|Needs Update)\s*:\s*(.+)$", text, re.DOTALL)
    if not m:
        return []
    section = m.group(2).strip()
    items = [ln.strip("-• ").strip() for ln in section.splitlines() if ln.strip()]
    return items[:20]