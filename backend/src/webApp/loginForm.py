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
        \n@Returns True = Exists
    """
    # prove that username is not already taken (if taken != None & not taken == None)
    typedUsername = field.data
    inUse = UserManager.isUsernameInUse(typedUsername)
    if not inUse:
        errMsg = f"Username '{typedUsername}' does not exist"
        raise ValidationError(f"{errMsg}, try again")
    else:
        return True

def validatePassword(form, field)->bool():
    typedUsername = field.data.username
    typedPassword = field.data.password
    correctPassword = UserManager.getPasswordFromUsername(username)
    isValidPassword = typedPassword == correctPassword
    if not isValidPassword: 
        errMsg = f"Invalid password for username '{typedUsername}"
        print(errMsg)
        raise ValidationError(errMsg)
    else:
        return True

class LoginForm(FlaskForm):
    """Generates a quick and dirty login form to authenticate for the webapp"""
    username = StringField('Username', validators=[DataRequired(), validateUsername])
    password = PasswordField('Password',  validators=[DataRequired(), validatePassword])
    rememberMe = BooleanField('Remember Me')
    submit = SubmitField('Submit')
