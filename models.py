from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ================= USERS =================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")

    vehicles = db.relationship("Vehicle", backref="dealer", lazy=True)
    orders = db.relationship("Order", backref="user", lazy=True)


# ================= VEHICLES =================
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    price = db.Column(db.Float)
    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)

    description = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    images = db.Column(db.Text)

    is_approved = db.Column(db.Boolean, default=False)

    dealer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


# ================= ORDERS =================
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
