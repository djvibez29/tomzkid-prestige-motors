import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from functools import wraps

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads/cars")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cars.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.secret_key = os.environ.get("SECRET_KEY", "dev-key")

db = SQLAlchemy(app)

# ================= MODELS =================

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    brand = db.Column(db.String(100))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)

    images = db.relationship("CarImage", backref="car", cascade="all, delete")


class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))


class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    message = db.Column(db.Text)
    car_id = db.Column(db.Integer)


# ================= AUTH =================

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "password")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ================= ROUTES =================

@app.route("/")
def home():
    page = request.args.get("page", 1, type=int)

    cars = Car.query.order_by(Car.id.desc()).paginate(page=page, per_page=9)

    return render_template("home.html", cars=cars)


@app.route("/car/<int:car_id>")
def car_page(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car.html", car=car)


# ================= ADMIN LOGIN =================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":

        if (
            request.form["username"] == ADMIN_USER
            and request.form["password"] == ADMIN_PASS
        ):
            session["admin"] = True
            return redirect(url_for("admin"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))


# ================= ADMIN DASHBOARD =================

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():

    if request.method == "POST":

        title = request.form.get("title")
        brand = request.form.get("brand")
        description = request.form.get("description")

        # ---------- SAFE PRICE PARSING ----------
        raw_price = request.form.get("price", "").replace(",", "").strip()

        try:
            price = int(float(raw_price))
        except ValueError:
            return redirect(url_for("admin"))

        car = Car(
            title=title,
            brand=brand,
            price=price,
            description=description,
        )

        db.session.add(car)
        db.session.commit()

        # ---------- IMAGES ----------
        files = request.files.getlist("images")

        for file in files:
            if file and file.filename:

                filename = secure_filename(file.filename)

                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                file.save(save_path)

                img = CarImage(
                    filename=filename,
                    car_id=car.id,
                )

                db.session.add(img)

        db.session.commit()

        return redirect(url_for("admin"))

    cars = Car.query.order_by(Car.id.desc()).all()
    leads = Lead.query.order_by(Lead.id.desc()).all()

    return render_template("admin.html", cars=cars, leads=leads)


# ================= INIT =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
