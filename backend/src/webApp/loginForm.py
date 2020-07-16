#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
# https://wtforms.readthedocs.io/en/2.3.x/validators/
# If StopValidation is raised, no more validators in the validation chain are called
from wtforms.validators import ValidationError, StopValidation, DataRequired, Email, EqualTo
from flask import flash

#--------------------------------OUR DEPENDENCIES--------------------------------#
from userManager import UserManager

#-----------------------------------Validators-----------------------------------#
def validateUsername(form, field)->bool():
    """
        \n@Returns True = Exists
        \n@Note: This will be part of the password's validation
    """
    # prove that username is not already taken (if taken != None & not taken == None)
    typedUsername = form.username.data # use generic 'form' variable
    usernameExists = UserManager.isUsernameInUse(typedUsername)
    if not usernameExists:
        errMsg = f"Username '{typedUsername}' does not exist"
        raise StopValidation(message=f"{errMsg}, try again")
    else:
        return True

def validatePassword(form, field)->bool():
    typedUsername = form.username.data
    typedPassword = field.data
    correctPassword = UserManager.getPasswordFromUsername(typedUsername)
    isValidPassword = typedPassword == correctPassword
    if not isValidPassword: 
        errMsg = f"Invalid password for username '{typedUsername}"
        print(errMsg)
        raise StopValidation(errMsg)
    else:
        return True

class LoginForm(FlaskForm):
    """Generates a quick and dirty login form to authenticate for the webapp"""
    #-----------------------------------Form Fields-----------------------------------#
    username = StringField('Username', validators=[DataRequired(), validateUsername])
    password = PasswordField('Password',  validators=[DataRequired(), validateUsername, validatePassword])
    rememberMe = BooleanField('Remember Me')
    submit = SubmitField('Submit')
