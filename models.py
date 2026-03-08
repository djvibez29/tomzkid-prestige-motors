# models.py
import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user")  # admin, dealer, user

    vehicles = db.relationship("Vehicle", backref="dealer", lazy=True)
    orders = db.relationship("Order", backref="buyer", lazy=True, foreign_keys="Order.buyer_id")


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    mileage = db.Column(db.Integer, nullable=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    is_approved = db.Column(db.Boolean, default=False)

    images = db.relationship("VehicleImage", backref="vehicle", lazy=True)
    orders = db.relationship("Order", backref="vehicle_obj", lazy=True)


class VehicleImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))
    image_url = db.Column(db.String(255), nullable=False)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"))  # LINK TO USER
    buyer_email = db.Column(db.String(120))
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))
    amount = db.Column(db.Integer, nullable=False)
    commission = db.Column(db.Integer, default=0)
    dealer_earnings = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="pending")  # pending, paid
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
