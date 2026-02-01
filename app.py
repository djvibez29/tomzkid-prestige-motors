from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import smtplib
from email.message import EmailMessage

# ---------------- CONFIG ----------------

app = Flask(__name__)
app.secret_key = "change-this-later"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static/uploads")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Email ENV (Render)
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_TO = os.getenv("MAIL_TO")

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
    image = db.Column(db.String(300))


class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(80))

    message = db.Column(db.Text)

    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))
    car = db.relationship("Car")

# ---------------- ADMIN LOGIN ----------------

ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"

# ---------------- DB INIT ----------------

with app.app_context():
    db.create_all()

# ---------------- EMAIL FUNCTION ----------------

def send_email(subject, body):

    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("⚠️ EMAIL ENV NOT SET")
        return

    msg = EmailMessage()
    msg["From"] = MAIL_USERNAME
    msg["To"] = MAIL_TO
    msg["Subject"] = subject

    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)

# ---------------- ROUTES ----------------

@app.route("/")
def index():

    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)

    query = Car.query

    if min_price:
        query = query.filter(Car.price_usd >= min_price)

    if max_price:
        query = query.filter(Car.price_usd <= max_price)

    cars = query.all()

    return render_template("index.html", cars=cars)


# ----------- CAR PAGE -----------

@app.route("/car/<int:car_id>", methods=["GET", "POST"])
def car_detail(car_id):

    car = Car.query.get_or_404(car_id)

    if request.method == "POST":

        inquiry = Inquiry(
            name=request.form["name"],
            email=request.form["email"],
            phone=request.form["phone"],
            message=request.form["message"],
            car=car,
        )

        db.session.add(inquiry)
        db.session.commit()

        email_body = f"""
NEW VEHICLE INQUIRY 🚘

Car: {car.name}
Brand: {car.brand}
Price: ${car.price_usd}

Customer:
Name: {inquiry.name}
Email: {inquiry.email}
Phone: {inquiry.phone}

Message:
{inquiry.message}
"""

        send_email(
            subject=f"New Inquiry – {car.name}",
            body=email_body,
        )

        flash("Inquiry sent successfully! We'll contact you shortly.")
        return redirect(url_for("car_detail", car_id=car.id))

    return render_template("car.html", car=car)


# ----------- ADMIN -----------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":

        file = request.files["image"]

        if file.filename == "":
            flash("No image selected")
            return redirect("/admin")

        filename = secure_filename(file.filename)

        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        car = Car(
            name=request.form["name"],
            brand=request.form["brand"],
            price_usd=int(request.form["price_usd"]),
            miles=int(request.form["miles"]),
            description=request.form["description"],
            image=filename,
        )

        db.session.add(car)
        db.session.commit()

        return redirect("/admin")

    cars = Car.query.all()
    return render_template("admin.html", cars=cars)


# ----------- ADMIN LEADS -----------

@app.route("/admin/inquiries")
def admin_inquiries():

    if not session.get("admin"):
        return redirect("/login")

    inquiries = Inquiry.query.order_by(Inquiry.id.desc()).all()

    return render_template("admin_inquiries.html", inquiries=inquiries)


# ----------- AUTH -----------

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


# ---------------- RUN LOCAL ----------------

if __name__ == "__main__":
    app.run(debug=True)
