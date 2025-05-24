"""Profile Forms
============

This module contains forms for profile management.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired, Length, Optional, URL, Email

class ProfileEditForm(FlaskForm):
    """Form for editing user profile."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=32)
    ])
    first_name = StringField('First Name', validators=[
        Optional(),
        Length(max=32)
    ])
    last_name = StringField('Last Name', validators=[
        Optional(),
        Length(max=32)
    ])
    email = StringField('Email', validators=[
        Optional(),
        Email(),
        Length(max=120)
    ])
    birthdate = DateField('Birthdate', validators=[
        Optional()
    ])
    bio = TextAreaField('Bio', validators=[
        Optional(),
        Length(max=500)
    ])
    current_location_city = StringField('Current City', validators=[
        Optional(),
        Length(max=100)
    ])
    current_location_state = StringField('Current State', validators=[
        Optional(),
        Length(max=100)
    ])
    hometown = StringField('Hometown', validators=[
        Optional(),
        Length(max=100)
    ])
    website = StringField('Website', validators=[
        Optional(),
        URL(),
        Length(max=128)
    ])
    interests = TextAreaField('Interests', validators=[
        Optional(),
        Length(max=200)
    ])
    profile_photo = FileField('Profile Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Save Changes') 