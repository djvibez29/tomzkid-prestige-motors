from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    brand = db.Column(db.String(100))
    custom_brand = db.Column(db.String(100))

    name = db.Column(db.String(200))
    year = db.Column(db.Integer)

    body_type = db.Column(db.String(50))

    mileage_miles = db.Column(db.Integer)

    price_usd = db.Column(db.Integer)

    transmission = db.Column(db.String(50))
    drivetrain = db.Column(db.String(50))
    engine = db.Column(db.String(100))

    description = db.Column(db.Text)

    image = db.Column(db.String(300))
