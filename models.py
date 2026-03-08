from extensions import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), default="buyer")


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    price = db.Column(db.Integer, nullable=False)

    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)

    image_url = db.Column(db.String(300))

    dealer_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    is_approved = db.Column(db.Boolean, default=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    buyer_email = db.Column(db.String(150))

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"))

    amount = db.Column(db.Integer)

    commission = db.Column(db.Integer)

    dealer_earnings = db.Column(db.Integer)

    status = db.Column(db.String(20), default="pending")
