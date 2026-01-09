from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)
app.secret_key = "change-this-later"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# --- MODELS ---
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    price_ngn = db.Column(db.Integer)
    price_usd = db.Column(db.Integer)
    description = db.Column(db.Text)
    image = db.Column(db.String(300))

# --- ADMIN CREDENTIALS (TEMP – we will secure later) ---
ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"

# --- ROUTES ---
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

        car = Car(
            name=request.form["name"],
            price_ngn=request.form["price_ngn"],
            price_usd=request.form["price_usd"],
            description=request.form["description"],
            image=filename
        )
        db.session.add(car)
        db.session.commit()
        return redirect("/admin")

    cars = Car.query.all()
    return render_template("admin.html", cars=cars)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()

from utils import get_usd_to_ngn_rate

@app.route("/")
def index():
    cars = Car.query.all()

        usd_to_ngn_rate = get_usd_to_ngn_rate()

            # Dynamically calculate Naira price
                for car in cars:
                        car.price_ngn_calculated = round(car.price_usd * usd_to_ngn_rate, 2)

                            return render_template("index.html", cars=cars)