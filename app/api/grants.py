from flask import Blueprint, jsonify, request
from app import db

bp = Blueprint('grants', __name__)

@bp.route('/', methods=['GET'])
def get_grants():
    """Get all grants"""
    return jsonify([])

@bp.route('/', methods=['POST'])
def create_grant():
    """Create a new grant"""
    return jsonify({"message": "Grant creation not implemented"}), 501

@bp.route('/<int:grant_id>', methods=['GET'])
def get_grant(grant_id):
    """Get a specific grant"""
    return jsonify({"message": f"Grant {grant_id} not found"}), 404