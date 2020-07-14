"""
    @file Responsible for creating the registration page for the web app
"""

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask import flash

#--------------------------------OUR DEPENDENCIES--------------------------------#
from webAppUsers import UserManager

#-----------------------------------Validators-----------------------------------#

def validateUsername(form, field)->bool():
    """
        \n@Returns True = Not Taken & False = Taken
    """
    # prove that username is not already taken (if taken != None & not taken == None)
    inUse = UserManager.isUsernameInUse(field.data)
    if inUse: ValidationError("Username already taken, choose another one")
    return not inUse


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), validateUsername])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
