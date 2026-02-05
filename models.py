from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class EngineType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class Drivetrain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class FuelType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class VehicleType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)

    brand_id = db.Column(db.Integer, db.ForeignKey("brand.id"))
    engine_id = db.Column(db.Integer, db.ForeignKey("engine_type.id"))
    drivetrain_id = db.Column(db.Integer, db.ForeignKey("drivetrain.id"))
    fuel_id = db.Column(db.Integer, db.ForeignKey("fuel_type.id"))
    type_id = db.Column(db.Integer, db.ForeignKey("vehicle_type.id"))

    brand = db.relationship("Brand")
    engine = db.relationship("EngineType")
    drivetrain = db.relationship("Drivetrain")
    fuel = db.relationship("FuelType")
    vehicle_type = db.relationship("VehicleType")

    images = db.relationship("CarImage", backref="car", cascade="all,delete")


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))
