from flask import request, jsonify
from . import profile
from utils.csrf import csrf

@profile.route('/update/<int:user_id>', methods=['POST'])
@csrf.exempt
def update_profile(user_id):
    # Handle profile update (e.g., for AJAX requests)
    # Update user data
    return jsonify({"status": "success", "message": "Profile updated"})
