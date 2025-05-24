from flask import render_template, request, redirect, url_for
from . import profile
from utils.csrf import csrf

@profile.route('/create', methods=['GET', 'POST'])
@csrf.exempt
def create_profile():
    if request.method == 'POST':
        # Handle form submission
        # Create new user profile
        new_user_id = 1  # Replace with actual new user ID
        return redirect(url_for('profile.view_profile', user_id=new_user_id))
    # GET request
    return render_template('profile/create.html')