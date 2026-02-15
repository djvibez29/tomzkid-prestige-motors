from datetime import datetime
from flask_login import UserMixin
from extensions import db


# ---------------- USER ----------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default="user")  
    plan = db.Column(db.String(20), default="free")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- VEHICLE ----------------

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    price = db.Column(db.Integer)

    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)

    image_url = db.Column(db.String(300))

    is_approved = db.Column(db.Boolean, default=False)

    dealer_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- WISHLIST ----------------

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))

    vehicle = db.relationship("Vehicle")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
