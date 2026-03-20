from extensions import db
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSON

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="user")

    # Relationships
    vehicles = db.relationship("Vehicle", backref="dealer", lazy=True)
    orders = db.relationship("Order", backref="buyer", lazy=True, foreign_keys="Order.user_id")


class Vehicle(db.Model):
    __tablename__ = "vehicle"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    mileage = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(300), nullable=True)
    images = db.Column(JSON, nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    orders = db.relationship("Order", backref="vehicle_ref", lazy=True)


class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # <-- Added
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    buyer_email = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    commission = db.Column(db.Integer, default=0)
    dealer_earnings = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="pending")
