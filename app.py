import os
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy import asc, desc

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "cars.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads/cars")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# ---------------------------------------------------
# MODELS
# ---------------------------------------------------

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class EngineType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class FuelType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class VehicleType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
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

    images = db.relationship("CarImage", cascade="all,delete")


# ---------------------------------------------------
# CREATE TABLES
# ---------------------------------------------------

with app.app_context():
    db.create_all()


# ---------------------------------------------------
# HOME (SEARCH + FILTER + PAGINATION)
# ---------------------------------------------------

@app.route("/")
def home():

    query = Car.query

    search = request.args.get("search")
    if search:
        query = query.filter(Car.title.ilike(f"%{search}%"))

    brand = request.args.get("brand")
    if brand:
        query = query.filter(Car.brand_id == brand)

    engine = request.args.get("engine")
    if engine:
        query = query.filter(Car.engine_id == engine)

    fuel = request.args.get("fuel")
    if fuel:
        query = query.filter(Car.fuel_id == fuel)

    vtype = request.args.get("type")
    if vtype:
        query = query.filter(Car.type_id == vtype)

    min_price = request.args.get("min_price")
    if min_price:
        query = query.filter(Car.price >= min_price)

    max_price = request.args.get("max_price")
    if max_price:
        query = query.filter(Car.price <= max_price)

    sort = request.args.get("sort")

    if sort == "price_asc":
        query = query.order_by(asc(Car.price))
    elif sort == "price_desc":
        query = query.order_by(desc(Car.price))
    else:
        query = query.order_by(desc(Car.id))

    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=12)

    cars = pagination.items

    saved = session.get("saved", [])

    return render_template(
        "home.html",
        cars=cars,
        pagination=pagination,
        saved=saved,
        brands=Brand.query.all(),
        engines=EngineType.query.all(),
        fuels=FuelType.query.all(),
        types=VehicleType.query.all(),
    )


# ---------------------------------------------------
# SAVE LISTING
# ---------------------------------------------------

@app.route("/save/<int:car_id>")
def save_car(car_id):

    saved = session.get("saved", [])

    if car_id not in saved:
        saved.append(car_id)

    session["saved"] = saved

    return redirect(request.referrer or "/")


# ---------------------------------------------------
# ADMIN UPLOAD
# ---------------------------------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        title = request.form["title"]
        price = request.form["price"]
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

        images = request.files.getlist("images")

        for image in images:
            if image.filename:
                filename = secure_filename(image.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                image.save(path)

                db.session.add(CarImage(filename=filename, car_id=car.id))

        db.session.commit()

        return redirect("/admin")

    return render_template(
        "admin.html",
        brands=Brand.query.all(),
        engines=EngineType.query.all(),
        fuels=FuelType.query.all(),
        types=VehicleType.query.all(),
    )


# ---------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
