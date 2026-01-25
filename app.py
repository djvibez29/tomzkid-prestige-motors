from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

from models import db, Car

app = Flask(__name__)
app.secret_key = "change-this-later"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------- AUTO RESET TABLES (TEMP FIX) ----------------
with app.app_context():
    try:
        db.create_all()
    except:
        db.drop_all()
        db.create_all()

# ---------------- ROUTES ----------------

@app.route("/")
def index():
    cars = Car.query.all()
    return render_template("index.html", cars=cars)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        file = request.files["image"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        brand = request.form.get("brand")
        custom_brand = request.form.get("custom_brand")

        car = Car(
            brand=brand,
            custom_brand=custom_brand,
            name=request.form["name"],
            year=request.form["year"],
            body_type=request.form["body_type"],
            mileage_miles=request.form["mileage_miles"],
            price_usd=request.form["price_usd"],
            transmission=request.form["transmission"],
            drivetrain=request.form["drivetrain"],
            engine=request.form["engine"],
            description=request.form["description"],
            image=filename
        )

        db.session.add(car)
        db.session.commit()

        return redirect("/admin")

    cars = Car.query.all()
    return render_template("admin.html", cars=cars)

# ---------------- LOGIN ----------------

ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        if (
            request.form["username"] == ADMIN_USER
            and request.form["password"] == ADMIN_PASS
        ):
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Invalid credentials"

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run()

@app.route("/car/<int:car_id>")
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car_detail.html", car=car)
