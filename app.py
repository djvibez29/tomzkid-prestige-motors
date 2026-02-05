from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "cars.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads/cars")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


class EngineType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


class FuelType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


class VehicleType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)

    brand_id = db.Column(db.Integer, db.ForeignKey("brand.id"))
    engine_id = db.Column(db.Integer, db.ForeignKey("engine_type.id"))
    fuel_id = db.Column(db.Integer, db.ForeignKey("fuel_type.id"))
    type_id = db.Column(db.Integer, db.ForeignKey("vehicle_type.id"))

    brand = db.relationship("Brand")
    engine = db.relationship("EngineType")
    fuel = db.relationship("FuelType")
    type = db.relationship("VehicleType")


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))

    car = db.relationship("Car", backref="images")


# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    page = request.args.get("page", 1, type=int)

    pagination = Car.query.order_by(Car.id.desc()).paginate(page=page, per_page=12)

    brands = Brand.query.all()

    return render_template(
        "home.html",
        cars=pagination.items,
        pagination=pagination,
        brands=brands
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():

    brands = Brand.query.all()
    engines = EngineType.query.all()
    fuels = FuelType.query.all()
    types = VehicleType.query.all()

    if request.method == "POST":

        title = request.form["title"]
        price = int(request.form["price"])
        description = request.form["description"]

        brand_id = request.form["brand"]
        engine_id = request.form["engine"]
        fuel_id = request.form["fuel"]
        type_id = request.form["type"]

        car = Car(
            title=title,
            price=price,
            description=description,
            brand_id=brand_id,
            engine_id=engine_id,
            fuel_id=fuel_id,
            type_id=type_id,
        )

        db.session.add(car)
        db.session.commit()

        files = request.files.getlist("images")

        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(path)

                img = CarImage(filename=filename, car_id=car.id)
                db.session.add(img)

        db.session.commit()

        return redirect(url_for("admin"))

    return render_template(
        "admin.html",
        brands=brands,
        engines=engines,
        fuels=fuels,
        types=types
    )


@app.route("/seed")
def seed():

    if Brand.query.first():
        return "Already seeded."

    brands = ["Lamborghini", "Ferrari", "Mercedes", "BMW", "Porsche"]
    engines = ["V6", "V8", "V10", "V12", "Inline-6", "Electric"]
    fuels = ["Petrol", "Diesel", "Hybrid", "Electric"]
    types = ["Sedan", "Coupe", "SUV", "Convertible", "Hypercar"]

    for b in brands:
        db.session.add(Brand(name=b))
    for e in engines:
        db.session.add(EngineType(name=e))
    for f in fuels:
        db.session.add(FuelType(name=f))
    for t in types:
        db.session.add(VehicleType(name=t))

    db.session.commit()

    return "Seeded successfully ✅"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
