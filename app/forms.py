from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, ValidationError, TextAreaField,SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length , InputRequired
from .models import User

class SignupForm(FlaskForm):
    class Meta():
        csrf= False
    sname = StringField('User name', validators=[DataRequired()])
    semail =    StringField('Email', validators=[DataRequired(), Email("This field require an email address")])
    spassword = PasswordField("Password", validators=[DataRequired()])
    sconfirm = PasswordField("ConFirmPassword", validators=[DataRequired(), EqualTo('spassword')])
    saddress = StringField("Address", validators=[DataRequired()])
    submit =SubmitField('Sign Up')
    def validate_sname(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError("Your username has been registered!!!")

    def validate_semail(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Your email has been registered!!!")

class SigninForm(FlaskForm):
    class Meta:
        csrf = False
    username = StringField('User name', validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit =SubmitField('Sign In')



class EditProfileForm(FlaskForm):
    class Meta:
        csrf = False
    firstname = StringField('Name', validators=[DataRequired()])
    lastname = StringField('Name', validators=[DataRequired()])
    email =    StringField('Email', validators=[DataRequired()])
    phone =     StringField('Phone')
    avatar =    StringField('Avatar')
    address =   StringField('Address')
    # submit = SubmitField('Change')
    # password = PasswordField("Password", validators=[DataRequired()])



