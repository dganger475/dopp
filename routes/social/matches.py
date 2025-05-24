"""
Matches Routes Module
===================

This module contains routes related to user matches and connections.
"""

from flask import Blueprint, jsonify, request, current_app, session
from models.user_match import UserMatch
from routes.auth import login_required

matches = Blueprint('matches', __name__)

@matches.route('/api/matches/sync', methods=['GET'])
def sync_matches():
    """Sync user matches."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                "error": "User not authenticated",
                "status": "error"
            }), 401

        # Get current user's matches
        user_matches = UserMatch.get_by_user_id(user_id)
        
        # Format matches for frontend
        formatted_matches = []
        for match in user_matches:
            formatted_matches.append({
                'id': match.id,
                'face_id': match.face_id,
                'similarity': match.similarity,
                'added_at': match.added_at,
                'is_visible': match.is_visible,
                'privacy_level': match.privacy_level,
                'type': 'added'  # For frontend display
            })

        return jsonify({
            "matches": formatted_matches,
            "status": "success"
        })
    except Exception as e:
        current_app.logger.error(f"Error syncing matches: {str(e)}")
        return jsonify({
            "error": "Failed to fetch matches",
            "status": "error"
        }), 500
