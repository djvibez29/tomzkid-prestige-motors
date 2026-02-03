from flask import Flask, render_template, request, redirect, session, url_for
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

    price_usd = db.Column(db.Integer)
    miles = db.Column(db.Integer)

    description = db.Column(db.Text)
    image = db.Column(db.String(300))


# ---------------- ADMIN LOGIN ----------------

ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"


# ---------------- ROUTES ----------------

@app.route("/")
def home():

    search = request.args.get("search", "").strip()

    query = Car.query

    if search:
        query = query.filter(
            (Car.name.ilike(f"%{search}%")) |
            (Car.brand.ilike(f"%{search}%")) |
            (Car.description.ilike(f"%{search}%"))
        )

    cars = query.order_by(Car.id.desc()).all()

    return render_template("home.html", cars=cars, search=search)


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

        if not file or file.filename == "":
            return redirect("/admin")

        filename = secure_filename(file.filename)

        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        car = Car(
            name=request.form["name"],
            brand=request.form["brand"],
            price_usd=int(request.form["price_usd"]),
            miles=int(request.form["miles"]),
            description=request.form["description"],
            image=filename
        )

        db.session.add(car)
        db.session.commit()

        return redirect("/admin")

    cars = Car.query.order_by(Car.id.desc()).all()

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
