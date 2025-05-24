from flask import render_template, request, redirect, url_for
from flask_login import login_required

@login_required
def create_post():
    if request.method == 'POST':
        # Handle post creation
        pass
    return render_template('social/create_post.html')