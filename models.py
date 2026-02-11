from extensions import db
from flask_login import UserMixin


favorites = db.Table(
    "favorites",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("vehicle_id", db.Integer, db.ForeignKey("vehicle.id")),
)


class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    is_admin = db.Column(db.Boolean, default=False)

    favorites = db.relationship(
        "Vehicle",
        secondary=favorites,
        backref="liked_by",
    )


class Vehicle(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    price = db.Column(db.Integer, nullable=False)

    year = db.Column(db.Integer)
    mileage = db.Column(db.Integer)

    image_url = db.Column(db.String(400))

    created_at = db.Column(db.DateTime, server_default=db.func.now())
