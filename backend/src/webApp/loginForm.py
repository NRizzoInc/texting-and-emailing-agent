#-----------------------------3RD PARTY DEPENDENCIES-----------------------------#
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
# https://wtforms.readthedocs.io/en/2.3.x/validators/
# If StopValidation is raised, no more validators in the validation chain are called
from wtforms.validators import ValidationError, StopValidation, DataRequired, Email, EqualTo
from flask import flash, Flask

#--------------------------------OUR DEPENDENCIES--------------------------------#
from backend.src.webApp.userManager import UserManager

class LoginForm(FlaskForm, UserManager):
    """Generates a quick and dirty login form to authenticate for the webapp"""
    #-----------------------------------Form Fields-----------------------------------#
    # To be redefined
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password',  validators=[DataRequired()])
    # Constant
    rememberMe = BooleanField('Remember Me')
    submit = SubmitField('Submit')

    def __init__(self, flaskApp:Flask, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        UserManager.__init__(self, flaskApp)
        cls = self.__class__ # get reference to cls
        cls.username = StringField('Username', validators=[DataRequired()])
        cls.password = PasswordField('Password',  validators=[DataRequired(), self.validateUsername, self.validatePassword])

    def validatePassword(self, form, field)->bool():
        typedUsername = form.username.data
        typedPassword = field.data
        correctPassword = self.getPasswordFromUsername(typedUsername)
        isValidPassword = typedPassword == correctPassword
        if not isValidPassword: 
            errMsg = f"Invalid password for username '{typedUsername}"
            flash(errMsg)
            raise StopValidation(message=errMsg)
        else:
            return True

    def validateUsername(self, form, field)->bool():
        """
            \n@Returns True = Exists
            \n@Note: This will be part of the password's validation (chain both to avoid double flashes)
        """
        # prove that username is not already taken (if taken != None & not taken == None)
        typedUsername = form.username.data # use generic 'form' variable
        usernameExists = self.isUsernameInUse(typedUsername)
        if not usernameExists:
            errMsg = f"Username '{typedUsername}' does not exist, try again"
            flash(errMsg)
            raise StopValidation(message=errMsg)
        else:
            return True

