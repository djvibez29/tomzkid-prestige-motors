from flask import Flask, render_template, request, redirect, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

# ---------------- APP SETUP ----------------

app = Flask(__name__)
app.secret_key = "change-this-later"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static/uploads")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------- MODELS ----------------

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200))
    brand = db.Column(db.String(100))
    body_type = db.Column(db.String(100))

    price_usd = db.Column(db.Integer)
    miles = db.Column(db.Integer)

    description = db.Column(db.Text)
    image = db.Column(db.String(300))


# ---------------- ADMIN LOGIN ----------------

ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"


# ---------------- ROUTES ----------------

@app.route("/")
def index():

    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)

    brand = request.args.get("brand")
    brand_custom = request.args.get("brand_custom")
    body_type = request.args.get("body_type")

    query = Car.query

    if min_price:
        query = query.filter(Car.price_usd >= min_price)

    if max_price:
        query = query.filter(Car.price_usd <= max_price)

    if body_type:
        query = query.filter(Car.body_type == body_type)

    if brand_custom:
        query = query.filter(Car.brand.ilike(f"%{brand_custom}%"))
    elif brand:
        query = query.filter(Car.brand == brand)

    cars = query.all()

    return render_template("index.html", cars=cars)


@app.route("/car/<int:car_id>")
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car.html", car=car)


@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":

        file = request.files["image"]

        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        car = Car(
            name=request.form["name"],
            brand=request.form["brand"],
            body_type=request.form["body_type"],
            price_usd=int(request.form["price_usd"]),
            miles=int(request.form["miles"]),
            description=request.form["description"],
            image=filename
        )

        db.session.add(car)
        db.session.commit()

        return redirect("/admin")

    cars = Car.query.all()
    return render_template("admin.html", cars=cars)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        if (
            request.form["username"] == ADMIN_USER
            and request.form["password"] == ADMIN_PASS
        ):
            session["admin"] = True
            return redirect("/admin")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- DB INIT ----------------

with app.app_context():
    db.create_all()
