from flask_login import UserMixin
from extensions import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(120))
    price = db.Column(db.Integer)

    engine = db.Column(db.String(80))
    drivetrain = db.Column(db.String(50))
    fuel = db.Column(db.String(40))

    image_main = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, server_default=db.func.now())
