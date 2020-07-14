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
        \n@Returns True = Exists
    """
    # prove that username is not already taken (if taken != None & not taken == None)
    inUse = UserManager.isUsernameInUse(field.data)
    if not inUse: ValidationError("Username does not exist, try again")
    return inUse

# done in webApp
# def validatePassword(form, field)->bool():
#     potentialUser = UserManager.getUserByUsername(field.data.username)
#     correctPassword = potentialUser.checkPassword(field.data.password)

class LoginForm(FlaskForm):
    """Generates a quick and dirty login form to authenticate for the webapp"""
    username = StringField('Username', validators=[DataRequired(), validateUsername])
    password = PasswordField('Password',  validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Submit')
