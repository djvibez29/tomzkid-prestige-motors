import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "cars")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)

app.secret_key = "super-secret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 500  # 500MB

db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    price = db.Column(db.Integer)
    description = db.Column(db.Text)

    images = db.relationship(
        "CarImage",
        backref="car",
        cascade="all, delete",
        lazy=True
    )


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))


# ---------------- HELPERS ---------------- #

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("home.html", cars=cars)


@app.route("/car/<int:car_id>")
def car_page(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car.html", car=car)


# ---------------- ADMIN ---------------- #

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        brand = request.form.get("brand")
        model = request.form.get("model")
        year = request.form.get("year")
        price = request.form.get("price")
        description = request.form.get("description")

        car = Car(
            brand=brand,
            model=model,
            year=year,
            price=price,
            description=description
        )

        db.session.add(car)
        db.session.commit()

        files = request.files.getlist("images")

        for file in files:

            if file and allowed_file(file.filename):

                filename = secure_filename(file.filename)

                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(save_path)

                img = CarImage(
                    filename=filename,
                    car_id=car.id
                )

                db.session.add(img)

        db.session.commit()

        flash("Vehicle added successfully ✅")

        return redirect(url_for("admin"))

    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("admin.html", cars=cars)


# ---------------- INIT DB ---------------- #

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
