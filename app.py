import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------
# APP CONFIG
# -----------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL or "sqlite:///dev.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------------
# LOGIN MANAGER
# -----------------------------------

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# -----------------------------------
# MODELS
# -----------------------------------


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255))
    price = db.Column(db.Integer)

    drivetrain = db.Column(db.String(50))
    engine = db.Column(db.String(100))
    fuel = db.Column(db.String(50))
    vehicle_type = db.Column(db.String(50))

    image_main = db.Column(db.String(255))


# -----------------------------------
# USER LOADER  (🔥 THIS FIXES YOUR CRASH)
# -----------------------------------


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# -----------------------------------
# CREATE TABLES
# -----------------------------------

with app.app_context():
    db.create_all()

# -----------------------------------
# ROUTES
# -----------------------------------


@app.route("/")
def home():
    vehicles = Vehicle.query.all()
    return render_template("home.html", vehicles=vehicles)


@app.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for("home"))

    vehicles = Vehicle.query.all()
    return render_template("admin.html", vehicles=vehicles)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("admin"))

        flash("Invalid credentials", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# -----------------------------------
# UPLOADS
# -----------------------------------


UPLOAD_FOLDER = "static/uploads/cars"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/upload-vehicle", methods=["POST"])
@login_required
def upload_vehicle():
    if not current_user.is_admin:
        return redirect(url_for("home"))

    title = request.form.get("title")
    price = request.form.get("price")

    drivetrain = request.form.get("drivetrain")
    engine = request.form.get("engine")
    fuel = request.form.get("fuel")
    vehicle_type = request.form.get("vehicle_type")

    image = request.files.get("image")

    filename = None
    if image:
        filename = image.filename
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    vehicle = Vehicle(
        title=title,
        price=price,
        drivetrain=drivetrain,
        engine=engine,
        fuel=fuel,
        vehicle_type=vehicle_type,
        image_main=filename,
    )

    db.session.add(vehicle)
    db.session.commit()

    return redirect(url_for("admin"))


# -----------------------------------
# RUN LOCAL ONLY
# -----------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
