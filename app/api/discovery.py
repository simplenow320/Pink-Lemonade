from flask import Blueprint, jsonify, request
from app import db

bp = Blueprint('discovery', __name__)

@bp.route('/run', methods=['POST'])
def run_discovery():
    """Run grant discovery process"""
    return jsonify({"message": "Discovery process not implemented"}), 501

@bp.route('/status', methods=['GET'])
def get_discovery_status():
    """Get discovery status"""
    return jsonify({"status": "idle", "last_run": None})