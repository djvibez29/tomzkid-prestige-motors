import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# ======================
# CONFIG
# ======================

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "database.db")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB

db = SQLAlchemy(app)

# ======================
# MODEL
# ======================

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(120), nullable=False)

    price_usd = db.Column(db.Integer, nullable=False)
    miles = db.Column(db.Integer, nullable=False)

    description = db.Column(db.Text, nullable=False)

    image = db.Column(db.String(300), nullable=False)

# ======================
# CREATE TABLES
# ======================

with app.app_context():
    db.create_all()

# ======================
# ROUTES
# ======================

@app.route("/")
def index():
    min_price = request.args.get("min")
    max_price = request.args.get("max")

    cars = Car.query

    if min_price:
        cars = cars.filter(Car.price_usd >= int(min_price))

    if max_price:
        cars = cars.filter(Car.price_usd <= int(max_price))

    cars = cars.all()

    brands = sorted({c.brand for c in cars})

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

    if request.method == "POST":

        # ------------------
        # FORM DATA
        # ------------------

        name = request.form.get("name")
        brand = request.form.get("brand")
        price_usd = request.form.get("price_usd")
        miles = request.form.get("miles")
        description = request.form.get("description")

        # ------------------
        # FILE CHECK
        # ------------------

        if "image" not in request.files:
            return "No image uploaded", 400

        file = request.files["image"]

        if file.filename == "":
            return "Empty filename", 400

        filename = secure_filename(file.filename)

        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        # ------------------
        # SAVE TO DB
        # ------------------

        car = Car(
            name=name,
            brand=brand,
            price_usd=int(price_usd),
            miles=int(miles),
            description=description,
            image=filename,
        )

        db.session.add(car)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("admin.html")


# ======================
# RUN LOCAL
# ======================

if __name__ == "__main__":
    app.run(debug=True)
