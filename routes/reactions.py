"""
Reactions Blueprint
==================

Handles routes for post reactions (like, amazing, related, wow).

Notes:
- All business logic is delegated to models or utility functions.
- No business logic in routes; routes only handle request/response and session.
"""

# === Third-Party Imports ===
from flask import Blueprint, current_app, jsonify, request, session

# === Project Imports ===
from models.reaction import Reaction
from models.social import Post
from routes.auth import login_required

# === Blueprint Definition ===
reactions = Blueprint("reactions", __name__)


# =============================
# REACT TO POST ROUTE
# =============================
@reactions.route("/api/posts/<int:post_id>/react", methods=["POST"])
@login_required
def react_to_post(post_id):
    """
    React to a post (add or update a reaction).
    Request: JSON with {"reaction_type": str}, must be one of Reaction.TYPES.
    Response: JSON with {success, reactions, user_reaction}.
    Returns 400 for invalid input, 404 for missing post, 500 for DB errors.
    All business logic is delegated to the Reaction model.
    """
    user_id = session.get("user_id")
    reaction_type = request.json.get("reaction_type")
    # Validate reaction type
    if not reaction_type or reaction_type not in Reaction.TYPES:
        current_app.logger.warning(
            f"User {user_id} attempted invalid reaction type '{reaction_type}' on post {post_id}"
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": f'Invalid reaction type. Must be one of: {", ".join(Reaction.TYPES)}',
                }
            ),
            400,
        )
    post = Post.get_by_id(post_id)
    if not post:
        current_app.logger.warning(
            f"User {user_id} attempted to react to non-existent post {post_id}"
        )
        return jsonify({"success": False, "error": "Post not found"}), 404
    # Delegate to model
    reaction = Reaction.create(user_id, post_id, reaction_type)
    if not reaction:
        current_app.logger.error(
            f"Failed to create reaction for user {user_id} on post {post_id}"
        )
        return jsonify({"success": False, "error": "Failed to react"}), 500
    reactions = post.get_reactions()
    return jsonify(
        {"success": True, "reactions": reactions, "user_reaction": reaction_type}
    )


@reactions.route("/api/posts/<int:post_id>/unreact", methods=["POST"])
@login_required
def remove_reaction(post_id):
    """
    Remove a reaction from a post.
    Request: No body required; uses session for user_id.
    Response: JSON with {success, reactions, user_reaction}.
    Returns 404 if no reaction found, 500 for DB errors.
    All business logic is delegated to the Reaction model.
    """
    user_id = session.get("user_id")
    # Find reaction to remove
    reaction = Reaction.get_by_user_and_post(user_id, post_id)
    if not reaction:
        current_app.logger.warning(
            f"User {user_id} tried to remove non-existent reaction on post {post_id}"
        )
        return jsonify({"success": False, "error": "No reaction found"}), 404
    # Delegate deletion to model
    if not reaction.delete():
        current_app.logger.error(
            f"Failed to delete reaction for user {user_id} on post {post_id}"
        )
        return jsonify({"success": False, "error": "Failed to remove reaction"}), 500
    post = Post.get_by_id(post_id)
    reactions = post.get_reactions() if post else {rtype: 0 for rtype in Reaction.TYPES}
    return jsonify({"success": True, "reactions": reactions, "user_reaction": None})
