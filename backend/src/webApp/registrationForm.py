"""
    @file Responsible for creating the registration page for the web app
"""

#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask import flash

#--------------------------------OUR DEPENDENCIES--------------------------------#
from userManager import UserManager

#-----------------------------------Validators-----------------------------------#

def validateUsername(form, field)->bool():
    """
        \n@Note: To validate successfully, has to raise ValidationError(<msg>) on taken
    """
    # prove that username is not already taken (if taken != None & not taken == None)
    typedUsername = field.data
    usernameInUse = UserManager.isUsernameInUse(typedUsername)
    # print(f"validating username: {typedUsername}")
    if usernameInUse:
        errMsg = f"Username '{typedUsername}' is already taken"
        # print(errMsg)
        flash(msgToPrint)
        raise ValidationError(f"{errMsg}, choose another one")
    else:
        # print(f"Username '{typedUsername} is free!")
        pass


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), validateUsername])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
