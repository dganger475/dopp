from flask import redirect, url_for
from . import profile
from utils.csrf import csrf

@profile.route('/delete/<int:user_id>', methods=['POST'])
@csrf.exempt
def delete_profile(user_id):
    # Delete user profile logic
    return redirect(url_for('home'))  # Redirect to home page after deletion
