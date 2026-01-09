from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
import datetime

app = Flask(__name__)
app.secret_key = "change-this-later"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------- MODELS ----------------
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price_usd = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(300), nullable=False)

# ---------------- ADMIN (TEMP) ----------------
ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"

# ---------------- EXCHANGE RATE LOGIC ----------------
cached_rate = None
last_updated = None

def get_usd_to_ngn_rate():
    global cached_rate, last_updated

    if cached_rate and last_updated:
        if datetime.datetime.now() - last_updated < datetime.timedelta(hours=1):
            return cached_rate

    try:
        response = requests.get(
            "https://api.exchangerate.host/latest?base=USD&symbols=NGN",
            timeout=10
        )
        data = response.json()
        cached_rate = data["rates"]["NGN"]
        last_updated = datetime.datetime.now()
    except:
        cached_rate = 1500  # fallback (current realistic rate)
        last_updated = datetime.datetime.now()

    return cached_rate

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    cars = Car.query.all()
    rate = get_usd_to_ngn_rate()

    for car in cars:
        car.price_ngn = round(car.price_usd * rate)

    return render_template(
        "index.html",
        cars=cars,
        usd_to_ngn_rate=rate
    )

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
    error = None
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Invalid login"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- SCHEDULER ----------------
def reset_rate():
    global cached_rate, last_updated
    cached_rate = None
    last_updated = None
    print("Weekly USD→NGN rate reset")

scheduler = BackgroundScheduler()
scheduler.add_job(reset_rate, "cron", day_of_week="thu", hour=0)
scheduler.start()

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
