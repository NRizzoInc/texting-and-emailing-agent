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
        \n@Note: To validate successfully, has to raise ValidationError(<msg>) on return False
    """
    # prove that username is not already taken (if taken != None & not taken == None)
    username = field.data
    usernameInUse = UserManager.dbManager.isUsernameInUse(username)
    print(f"validating username: {username}")
    if usernameInUse:
        msgToPrint = f"Username '{username}' is already taken"
        print(msgToPrint)
        flash(msgToPrint)
        raise ValidationError(f"{msgToPrint}, choose another one")
    else:
        print(f"Username '{username} is free!")
    return not usernameInUse


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), validateUsername])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
