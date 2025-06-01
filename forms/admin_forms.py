"""
Admin Forms
==========

This module contains forms used in the admin interface.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class AdminLoginForm(FlaskForm):
    """Form for admin login."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AdminMatchForm(FlaskForm):
    """Form for admin face matching."""
    admin_image = FileField('Upload Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Find Matches') 