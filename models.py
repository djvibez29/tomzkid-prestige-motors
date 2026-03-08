from datetime import datetime
from extensions import db
from flask_login import UserMixin

# ---------------- USER ----------------
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="user")  # user, dealer, admin

    vehicles = db.relationship("Vehicle", backref="dealer", lazy=True)
    orders = db.relationship(
        "Order",
        backref="buyer",
        lazy=True,
        foreign_keys="Order.buyer_id"  # important fix
    )

# ---------------- VEHICLE ----------------
class Vehicle(db.Model):
    __tablename__ = "vehicle"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    mileage = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Single image for now (can extend to multi-images below)
    image_url = db.Column(db.String(300), nullable=True)

    # Optional: store multiple images as comma-separated URLs
    images = db.Column(db.Text, nullable=True)

    is_approved = db.Column(db.Boolean, default=False)
    dealer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    orders = db.relationship("Order", backref="vehicle", lazy=True)

# ---------------- ORDER ----------------
class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # fix FK
    buyer_email = db.Column(db.String(120), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    commission = db.Column(db.Integer, default=0)
    dealer_earnings = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="pending")  # pending, paid

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
