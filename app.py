from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import os

# ---------------- APP SETUP ----------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static/uploads")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Mail
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME")

mail = Mail(app)

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

    featured = db.Column(db.Boolean, default=False)

    image = db.Column(db.String(300))


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300))
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))

    car = db.relationship("Car", backref=db.backref("gallery", lazy=True))


class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    message = db.Column(db.Text)

    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("home.html", cars=cars)


@app.route("/car/<int:car_id>")
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car.html", car=car)


# ---------------- ADMIN ----------------

ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"


@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":

        files = request.files.getlist("images")

        if not files or files[0].filename == "":
            flash("No images selected")
            return redirect("/admin")

        filenames = []

        for file in files:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            filenames.append(filename)

        car = Car(
            name=request.form["name"],
            brand=request.form["brand"],
            price_usd=int(request.form["price_usd"]),
            miles=int(request.form["miles"]),
            description=request.form["description"],
        )

        db.session.add(car)
        db.session.commit()

        for fname in filenames:
            img = CarImage(filename=fname, car_id=car.id)
            db.session.add(img)

        db.session.commit()

        flash("Vehicle uploaded successfully")

        return redirect("/admin")

    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("admin.html", cars=cars)


@app.route("/delete/<int:car_id>")
def delete_car(car_id):

    if not session.get("admin"):
        return redirect("/login")

    car = Car.query.get_or_404(car_id)

    for img in car.gallery:
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
