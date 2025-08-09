from flask import Blueprint, jsonify, request
from app import db

bp = Blueprint('ai', __name__)

@bp.route('/match', methods=['POST'])
def get_match_score():
    """Get AI match score for a grant"""
    return jsonify({"message": "AI matching not implemented"}), 501

@bp.route('/extract', methods=['POST'])
def extract_grant_info():
    """Extract grant information from text/URL"""
    return jsonify({"message": "Grant extraction not implemented"}), 501

@bp.route('/generate', methods=['POST'])
def generate_narrative():
    """Generate grant narrative"""
    return jsonify({"message": "Narrative generation not implemented"}), 501