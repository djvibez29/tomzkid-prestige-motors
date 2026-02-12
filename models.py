from extensions import db
from flask_login import UserMixin


class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    role = db.Column(db.String(20), default="user")
    # roles: user, dealer, admin

    vehicles = db.relationship("Vehicle", backref="dealer")


class Vehicle(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)

    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)

    image_url = db.Column(db.String(400))

    is_approved = db.Column(db.Boolean, default=False)

    dealer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
    )
