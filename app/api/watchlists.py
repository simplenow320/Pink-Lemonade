from flask import Blueprint, jsonify, request
from app import db

bp = Blueprint('watchlists', __name__)

@bp.route('/', methods=['GET'])
def get_watchlists():
    """Get all watchlists"""
    return jsonify([])

@bp.route('/', methods=['POST'])
def create_watchlist():
    """Create a new watchlist"""
    return jsonify({"message": "Watchlist creation not implemented"}), 501

@bp.route('/<int:watchlist_id>', methods=['GET'])
def get_watchlist(watchlist_id):
    """Get a specific watchlist"""
    return jsonify({"message": f"Watchlist {watchlist_id} not found"}), 404