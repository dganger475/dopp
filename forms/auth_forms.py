"""Authentication Forms
==================

This module contains the forms used for user authentication.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    """Form for user login."""
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    """Form for user registration."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    profile_photo = FileField('Profile Photo', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Register') 