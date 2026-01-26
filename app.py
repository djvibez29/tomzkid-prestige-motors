from flask import Flask, render_template, request, redirect, session, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static/uploads")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB uploads

db = SQLAlchemy(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

logging.basicConfig(level=logging.INFO)

# ---------------- MODELS ----------------

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=False)

    price_usd = db.Column(db.Integer, nullable=False)
    miles = db.Column(db.Integer, nullable=False)

    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(300), nullable=True)


# ---------------- ADMIN LOGIN ----------------

ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"


# ---------------- ROUTES ----------------

@app.route("/")
def index():

    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)

    query = Car.query

    if min_price is not None:
        query = query.filter(Car.price_usd >= min_price)

    if max_price is not None:
        query = query.filter(Car.price_usd <= max_price)

    cars = query.all()

    return render_template("index.html", cars=cars)


@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":

        try:

            file = request.files.get("image")

            filename = None
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            car = Car(
                name=request.form.get("name"),
                brand=request.form.get("brand"),
                price_usd=int(request.form.get("price_usd", 0)),
                miles=int(request.form.get("miles", 0)),
                description=request.form.get("description"),
                image=filename
            )

            db.session.add(car)
            db.session.commit()

            return redirect("/admin")

        except Exception as e:
            app.logger.error(f"ADMIN UPLOAD ERROR: {e}")
            abort(500)

    cars = Car.query.all()
    return render_template("admin.html", cars=cars)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        if (
            request.form.get("username") == ADMIN_USER
            and request.form.get("password") == ADMIN_PASS
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


if __name__ == "__main__":
    app.run(debug=True)
