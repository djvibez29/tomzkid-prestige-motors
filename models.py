from extensions import db
from flask_login import UserMixin
from datetime import datetime


class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), default="dealer")


class Vehicle(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    trim = db.Column(db.String(50))

    price = db.Column(db.Integer)

    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)

    transmission = db.Column(db.String(20))
    drivetrain = db.Column(db.String(20))
    body_style = db.Column(db.String(20))

    engine_type = db.Column(db.String(50))
    engine_layout = db.Column(db.String(10))

    interior_color = db.Column(db.String(30))
    exterior_color = db.Column(db.String(30))

    image_url = db.Column(db.String(300))

    is_approved = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    dealer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
