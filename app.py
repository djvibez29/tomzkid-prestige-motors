import os
from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from functools import wraps

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads/cars")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    brand = db.Column(db.String(80))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)

    images = db.relationship("CarImage", backref="car", cascade="all,delete")

class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    car_id = db.Column(db.Integer, db.ForeignKey("car.id"))

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    message = db.Column(db.Text)
    car_id = db.Column(db.Integer)

# ---------------- UTILS ---------------- #

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    page = request.args.get("page", 1, type=int)

    cars = Car.query.paginate(page=page, per_page=9)

    return render_template("home.html", cars=cars)

@app.route("/car/<int:car_id>")
def car_page(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car.html", car=car)

# ---------------- ADMIN AUTH ---------------- #

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

# ---------------- ADMIN PANEL ---------------- #

@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    if request.method == "POST":

        title = request.form["title"]
        brand = request.form["brand"]
        price = int(request.form["price"])
        description = request.form["description"]

        car = Car(
            title=title,
            brand=brand,
            price=price,
            description=description,
        )

        db.session.add(car)
        db.session.commit()

        files = request.files.getlist("images")

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                base, ext = os.path.splitext(filename)
                i = 1
                while os.path.exists(path):
                    filename = f"{base}_{i}{ext}"
                    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    i += 1

                file.save(path)

                img = CarImage(filename=filename, car_id=car.id)
                db.session.add(img)

        db.session.commit()

        return redirect(url_for("admin"))

    cars = Car.query.all()
    leads = Lead.query.order_by(Lead.id.desc()).all()

    return render_template("admin.html", cars=cars, leads=leads)

# ---------------- LEADS ---------------- #

@app.route("/inquire/<int:car_id>", methods=["POST"])
def inquire(car_id):
    lead = Lead(
        name=request.form["name"],
        email=request.form["email"],
        phone=request.form["phone"],
        message=request.form["message"],
        car_id=car_id,
    )

    db.session.add(lead)
    db.session.commit()

    return redirect(url_for("car_page", car_id=car_id))

# ---------------- INIT ---------------- #

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
