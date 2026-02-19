from extensions import db
from flask_login import UserMixin
from datetime import datetime


# 👤 USERS
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")


# 🚗 VEHICLES
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)

    image_url = db.Column(db.String(300))

    is_approved = db.Column(db.Boolean, default=False)

    dealer_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ❤️ WISHLIST
class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vehicle = db.relationship("Vehicle")


# 🛒 ORDERS (PAYMENTS)
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    buyer_email = db.Column(db.String(150), nullable=False)

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))
    vehicle = db.relationship("Vehicle")

    amount = db.Column(db.Integer, nullable=False)

    status = db.Column(db.String(50), default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
