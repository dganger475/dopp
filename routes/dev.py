"""
Development/Test Blueprint for DoppleGanger
Contains endpoints only available in development mode.
"""

import os

from flask import Blueprint, jsonify

dev = Blueprint("dev", __name__)


@dev.route("/test-reset-field-defaults")
def test_reset_field_defaults():
    """Dev/test endpoint: Reset field defaults (only available in development mode)."""
    if os.environ.get("FLASK_ENV", "development") != "development":
        return (
            jsonify({"status": "error", "message": "Not available in production."}),
            403,
        )
    try:
        from utils.emergency_fix import reset_field_defaults

        result = reset_field_defaults()
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        import traceback

        return (
            jsonify(
                {
                    "status": "error",
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                }
            ),
            500,
        )
