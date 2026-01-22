from flask import Flask, render_template, request, redirect, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "change-this-later"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static/uploads")

db = SQLAlchemy(app)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------- MODELS ----------------

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    brand = db.Column(db.String(100))
    model = db.Column(db.String(150))
    year = db.Column(db.Integer)

    body_type = db.Column(db.String(50))

    mileage = db.Column(db.Integer)  # miles
    transmission = db.Column(db.String(50))
    drivetrain = db.Column(db.String(50))
    engine = db.Column(db.String(120))

    exterior_color = db.Column(db.String(80))
    interior_color = db.Column(db.String(80))

    vin = db.Column(db.String(80))

    price_usd = db.Column(db.Integer)

    description = db.Column(db.Text)

    image = db.Column(db.String(300))

    featured = db.Column(db.Boolean, default=False)


# ---------------- ADMIN LOGIN ----------------

ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"


# ---------------- ROUTES ----------------

@app.route("/")
def index():
    cars = Car.query.filter_by(featured=True).all()
    return render_template("index.html", cars=cars)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":

        file = request.files["image"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        car = Car(
            brand=request.form["brand"],
            model=request.form["model"],
            year=request.form["year"],
            body_type=request.form["body_type"],
            mileage=request.form["mileage"],
            transmission=request.form["transmission"],
            drivetrain=request.form["drivetrain"],
            engine=request.form["engine"],
            exterior_color=request.form["exterior_color"],
            interior_color=request.form["interior_color"],
            vin=request.form["vin"],
            price_usd=request.form["price_usd"],
            description=request.form["description"],
            image=filename,
            featured=True if request.form.get("featured") else False,
        )

        db.session.add(car)
        db.session.commit()

        return redirect("/admin")

    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("admin.html", cars=cars)


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
            error = "Invalid login"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- RUN ----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
