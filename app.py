from flask import Flask, render_template, request, redirect, session, abort, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import uuid

# ---------------- APP ----------------

app = Flask(__name__)
app.secret_key = "change-this-later"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

db = SQLAlchemy(app)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------- MODELS ----------------

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=False)

    price_usd = db.Column(db.Integer, nullable=False)
    miles = db.Column(db.Integer, nullable=False)

    description = db.Column(db.Text, nullable=False)
    main_image = db.Column(db.String(300), nullable=False)

    images = db.relationship(
        "CarImage",
        backref="car",
        cascade="all, delete-orphan",
    )

    video = db.relationship(
        "CarVideo",
        backref="car",
        cascade="all, delete-orphan",
        uselist=False,
    )


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)

    car_id = db.Column(
        db.Integer,
        db.ForeignKey("car.id"),
        nullable=False,
    )


class CarVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300))

    car_id = db.Column(
        db.Integer,
        db.ForeignKey("car.id"),
        nullable=False,
    )

# ---------------- ADMIN ----------------

ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"

# ---------------- HELPERS ----------------

def save_file(file):
    if not file or file.filename == "":
        return None

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    unique_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)

    file.save(path)
    return unique_name

# ---------------- ROUTES ----------------

@app.route("/")
def index():

    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    brand = request.args.get("brand")
    max_miles = request.args.get("max_miles", type=int)

    query = Car.query

    if min_price:
        query = query.filter(Car.price_usd >= min_price)

    if max_price:
        query = query.filter(Car.price_usd <= max_price)

    if brand:
        query = query.filter(Car.brand == brand)

    if max_miles:
        query = query.filter(Car.miles <= max_miles)

    cars = query.order_by(Car.id.desc()).all()

    brands = [b[0] for b in db.session.query(Car.brand).distinct()]

    return render_template("index.html", cars=cars, brands=brands)


@app.route("/brand/<brand>")
def brand_page(brand):
    cars = Car.query.filter_by(brand=brand).all()
    return render_template("brand.html", cars=cars, brand=brand)


@app.route("/car/<int:car_id>")
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car.html", car=car)


@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get("admin"):
        return redirect(url_for("login"))

    brands = [b[0] for b in db.session.query(Car.brand).distinct()]

    if request.method == "POST":

        main_file = request.files.get("main_image")
        gallery_files = request.files.getlist("gallery")
        video_file = request.files.get("video")

        if not main_file or main_file.filename == "":
            abort(400, "Main image is required")

        brand = request.form.get("brand")
        custom_brand = request.form.get("custom_brand")

        final_brand = custom_brand.strip() if custom_brand else brand

        main_name = save_file(main_file)

        car = Car(
            name=request.form["name"],
            brand=final_brand,
            price_usd=int(request.form["price_usd"]),
            miles=int(request.form["miles"]),
            description=request.form["description"],
            main_image=main_name,
        )

        db.session.add(car)
        db.session.flush()

        for img in gallery_files:
            if img and img.filename:
                fname = save_file(img)
                db.session.add(CarImage(filename=fname, car=car))

        if video_file and video_file.filename:
            vname = save_file(video_file)
            db.session.add(CarVideo(filename=vname, car=car))

        db.session.commit()

        return redirect(url_for("admin"))

    cars = Car.query.order_by(Car.id.desc()).all()

    return render_template("admin.html", cars=cars, brands=brands)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        if (
            request.form["username"] == ADMIN_USER
            and request.form["password"] == ADMIN_PASS
        ):
            session["admin"] = True
            return redirect(url_for("admin"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- INIT ----------------

with app.app_context():
    db.create_all()
