from datetime import date

from flask import g
from flask_wtf import FlaskForm

from wtforms import StringField, SelectField, DateField, SubmitField, PasswordField, IntegerField
from wtforms.validators import DataRequired, NumberRange, ValidationError

from logistics.db import get_db

# Custom validators
def validate_collectionBy(form, field):
    today = date.today()
    print(field.data)
    if field.data < today:
        raise ValidationError("The must be in the future")
    
def validate_deliveryBy(form, field):
    if field.data <= form.collection_date.data:
        raise ValidationError("The delivery date must not be prior to the collection date")


# Flask forms
class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    company = StringField("Company", validators=[DataRequired()])
    user_type = SelectField("User Type", validators=[DataRequired()], choices=["Customer", "Supplier"])
    submit = SubmitField("Sign Up")
    
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")  
    
class RequestForm(FlaskForm):
    collection_address = SelectField("Collection Address", validators=[DataRequired()])
    delivery_address = SelectField("Delivery Address", validators=[DataRequired()])
    pallets = SelectField("Pallets", validators=[DataRequired()], choices=(range(1,11)))
    weight = IntegerField("Weight (kg)", validators=[DataRequired(), NumberRange(min=1, max=10000)])
    collection_date = DateField("Collection Date", format="%Y-%m-%d", validators=[DataRequired(), validate_collectionBy])
    delivery_date = DateField("Delivery Date", format="%Y-%m-%d", validators=[DataRequired(), validate_deliveryBy])
    submit = SubmitField("Create Request")
    
    def __init__(self, *args, **kwargs):
        super(RequestForm, self).__init__(*args, **kwargs)
        db = get_db()
        query = db.execute(
            """
            SELECT name || ', ' || street || ', ' || city || ', ' || country || ', ' || zipcode AS full_address
            FROM location l
            LEFT JOIN user u 
                ON u.id = l.created_by
            WHERE u.company = ?
            ORDER BY l.id
            """, (g.user["company"],)
        ).fetchall()
        all_locations = [(row["full_address"], row["full_address"]) for row in query]
        self.collection_address.choices = all_locations
        self.delivery_address.choices = all_locations
            

class BidForm(FlaskForm):
    bid_amount = StringField("Bid Amount", validators=[DataRequired()])
    submit = SubmitField("Submit Bid")


class LocationForm(FlaskForm):
    name = StringField("Company Name", validators=[DataRequired()])
    street = StringField("Street", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired()])
    country = StringField("Country", validators=[DataRequired()])
    zipcode = StringField("Zip Code", validators=[DataRequired()])
    submit = SubmitField("Create Location")