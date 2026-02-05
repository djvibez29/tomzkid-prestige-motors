import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

from models import (
    db,
    Car,
    CarImage,
    Brand,
    EngineType,
    Drivetrain,
    FuelType,
    VehicleType,
)

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads/cars")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

# Render PostgreSQL or fallback local
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///dev.db",
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Create tables on boot (important for Render)
with app.app_context():
    db.create_all()


# ---------------- HOME / LISTINGS ---------------- #

@app.route("/")
def home():
    query = Car.query

    search = request.args.get("search")
    if search:
        query = query.filter(Car.title.ilike(f"%{search}%"))

    brand = request.args.get("brand")
    if brand:
        query = query.filter(Car.brand_id == brand)

    cars = query.order_by(Car.id.desc()).all()

    brands = Brand.query.all()

    return render_template("home.html", cars=cars, brands=brands)


# ---------------- ADMIN ---------------- #

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        car = Car(
            title=request.form["title"],
            price=request.form["price"],
            description=request.form["description"],
            brand_id=request.form["brand"],
            engine_id=request.form["engine"],
            drivetrain_id=request.form["drivetrain"],
            fuel_id=request.form["fuel"],
            type_id=request.form["type"],
        )

        db.session.add(car)
        db.session.commit()

        files = request.files.getlist("images")

        for f in files:
            if f.filename:
                filename = secure_filename(f.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                f.save(path)

                img = CarImage(filename=filename, car_id=car.id)
                db.session.add(img)

        db.session.commit()

        return redirect(url_for("admin"))

    return render_template(
        "admin.html",
        brands=Brand.query.all(),
        engines=EngineType.query.all(),
        drivetrains=Drivetrain.query.all(),
        fuels=FuelType.query.all(),
        types=VehicleType.query.all(),
    )


# ------------- FIRST DATA SEED ---------------- #

@app.route("/seed")
def seed():
    if not Brand.query.first():
        brands = ["Mercedes", "BMW", "Audi", "Porsche", "Lamborghini"]
        for b in brands:
            db.session.add(Brand(name=b))

        engines = ["V8", "V6", "Inline-6", "Electric"]
        fuels = ["Petrol", "Diesel", "Hybrid", "EV"]
        drivetrains = ["AWD", "RWD", "FWD"]
        types = ["SUV", "Sedan", "Coupe", "Truck"]

        for e in engines:
            db.session.add(EngineType(name=e))
        for f in fuels:
            db.session.add(FuelType(name=f))
        for d in drivetrains:
            db.session.add(Drivetrain(name=d))
        for t in types:
            db.session.add(VehicleType(name=t))

        db.session.commit()

    return "Seeded ✅"


if __name__ == "__main__":
    app.run(debug=True)
