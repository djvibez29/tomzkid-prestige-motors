import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from dotenv import load_dotenv

# ---------------------------
# ENV
# ---------------------------
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")

# ---------------------------
# APP
# ---------------------------
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB

# ---------------------------
# MAIL CONFIG (GMAIL)
# ---------------------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("EMAIL_USER")
app.config["MAIL_PASSWORD"] = os.environ.get("EMAIL_PASS")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("EMAIL_USER")

mail = Mail(app)

# ---------------------------
# DB
# ---------------------------
db = SQLAlchemy(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------
# MODELS
# ---------------------------

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(120), nullable=False)

    price_usd = db.Column(db.Integer, nullable=False)
    miles = db.Column(db.Integer, nullable=False)

    description = db.Column(db.Text, nullable=False)

    image = db.Column(db.String(300), nullable=False)


class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    message = db.Column(db.Text)

    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))
    car = db.relationship("Car")

# ---------------------------
# CREATE TABLES
# ---------------------------

with app.app_context():
    db.create_all()

# ---------------------------
# ROUTES
# ---------------------------

@app.route("/")
def home():
    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("home.html", cars=cars)


@app.route("/car/<int:car_id>")
def car_page(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car.html", car=car)


# ---------------------------
# ADMIN UPLOAD
# ---------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        if "image" not in request.files:
            flash("No image uploaded")
            return redirect("/admin")

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

        flash("Vehicle uploaded successfully!")
        return redirect("/admin")

    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("admin.html", cars=cars)


# ---------------------------
# DELETE CAR
# ---------------------------

@app.route("/delete-car/<int:car_id>")
def delete_car(car_id):

    car = Car.query.get_or_404(car_id)

    try:
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], car.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    except:
        pass

    db.session.delete(car)
    db.session.commit()

    flash("Vehicle deleted")
    return redirect("/admin")


# ---------------------------
# INQUIRY FORM
# ---------------------------

@app.route("/inquire/<int:car_id>", methods=["POST"])
def inquire(car_id):

    car = Car.query.get_or_404(car_id)

    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]

    inquiry = Inquiry(
        name=name,
        email=email,
        message=message,
        car=car,
    )

    db.session.add(inquiry)
    db.session.commit()

    # EMAIL SEND
    try:

        msg = Message(
            subject=f"New Car Inquiry — {car.name}",
            recipients=[os.environ.get("EMAIL_USER")],
        )

        msg.body = f"""
New inquiry for {car.name}

Name: {name}
Email: {email}

Message:
{message}
"""

        mail.send(msg)

    except Exception as e:
        print("Email error:", e)

    flash("Inquiry sent successfully!")
    return redirect(url_for("car_page", car_id=car.id))


# ---------------------------
# LEADS DASHBOARD
# ---------------------------

@app.route("/leads")
def leads():

    inquiries = Inquiry.query.order_by(Inquiry.id.desc()).all()
    return render_template("leads.html", inquiries=inquiries)


# ---------------------------
# RUN LOCAL
# ---------------------------

if __name__ == "__main__":
    app.run(debug=True)
