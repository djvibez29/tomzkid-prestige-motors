from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-later"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static/uploads")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 500  # 500MB safety limit

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship(
        "CarImage",
        backref="car",
        cascade="all, delete",
        lazy=True
    )


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(300))
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))


# ---------------- ADMIN LOGIN ----------------

ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"


# ---------------- HOME ----------------

@app.route("/")
def home():

    cars = Car.query.order_by(Car.created_at.desc()).all()
    return render_template("home.html", cars=cars)


# ---------------- CAR PAGE ----------------

@app.route("/car/<int:car_id>")
def car_page(car_id):

    car = Car.query.get_or_404(car_id)
    return render_template("car.html", car=car)


# ---------------- ADMIN ----------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":

        files = request.files.getlist("images")

        if not files:
            return "No files uploaded", 400

        if len(files) > 50:
            return "Maximum 50 images allowed", 400

        car = Car(
            name=request.form["name"],
            brand=request.form["brand"],
            price_usd=int(request.form["price_usd"]),
            miles=int(request.form["miles"]),
            description=request.form["description"]
        )

        db.session.add(car)
        db.session.commit()

        for file in files:
            if file.filename == "":
                continue

            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            base, ext = os.path.splitext(filename)
            counter = 1

            while os.path.exists(save_path):
                filename = f"{base}_{counter}{ext}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                counter += 1

            file.save(save_path)

            img = CarImage(
                filename=filename,
                car_id=car.id
            )

            db.session.add(img)

        db.session.commit()

        return redirect("/admin")

    cars = Car.query.order_by(Car.created_at.desc()).all()
    return render_template("admin.html", cars=cars)


@app.route("/delete-car/<int:car_id>")
def delete_car(car_id):

    if not session.get("admin"):
        return redirect("/login")

    car = Car.query.get_or_404(car_id)

    for img in car.images:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], img.filename))
        except:
            pass

    db.session.delete(car)
    db.session.commit()

    return redirect("/admin")


# ---------------- LOGIN ----------------

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


# ---------------- INIT DB ----------------

with app.app_context():
    db.create_all()
