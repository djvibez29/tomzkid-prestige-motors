import os
import requests
from werkzeug.utils import secure_filename

import os

db_url = os.environ.get("DATABASE_URL")

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    
from flask import (
    Flask, render_template, redirect,
    request, url_for, flash
)

from flask_login import (
    login_user, logout_user,
    login_required, current_user
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from extensions import db, login_manager
from models import User, Vehicle, Order


# ---------------- CONFIG ----------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")

db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY")


# ---------------- INIT ----------------

db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()

    ADMIN_EMAIL = "tomzkidprestigegroups@gmail.com"
    ADMIN_PASSWORD = "OGTomzkid 29"

    admin = User.query.filter_by(email=ADMIN_EMAIL).first()

    if not admin:
        admin = User(
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()


# ---------------- HOME ----------------

@app.route("/")
def home():
    vehicles = Vehicle.query.filter_by(is_approved=True)\
        .order_by(Vehicle.created_at.desc()).all()

    return render_template("home.html", vehicles=vehicles)


# ---------------- VEHICLE DETAIL ----------------

@app.route("/vehicle/<int:id>")
def vehicle_detail(id):

    vehicle = Vehicle.query.get_or_404(id)

    if not vehicle.is_approved:
        return redirect("/")

    dealer = User.query.get(vehicle.dealer_id)

    return render_template(
        "vehicle_detail.html",
        vehicle=vehicle,
        dealer=dealer,
    )


# ---------------- AUTH ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = User.query.filter_by(
            email=request.form["email"]
        ).first()

        if user and check_password_hash(
            user.password_hash,
            request.form["password"],
        ):
            login_user(user)

            if user.role == "admin":
                return redirect("/admin")

            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


# ---------------- BUY → PAYSTACK ----------------

@app.route("/buy/<int:vehicle_id>")
@login_required
def buy(vehicle_id):

    vehicle = Vehicle.query.get_or_404(vehicle_id)

    order = Order(
        buyer_email=current_user.email,
        vehicle_id=vehicle.id,
        amount=vehicle.price,
        status="pending"
    )

    db.session.add(order)
    db.session.commit()

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }

    data = {
        "email": current_user.email,
        "amount": vehicle.price * 100,
        "callback_url": url_for(
            "verify_payment",
            order_id=order.id,
            _external=True
        )
    }

    res = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=data,
        headers=headers
    ).json()

    return redirect(res["data"]["authorization_url"])


# ---------------- VERIFY PAYMENT ----------------

@app.route("/verify/<int:order_id>")
@login_required
def verify_payment(order_id):

    reference = request.args.get("reference")

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}"
    }

    res = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers=headers
    ).json()

    if res["data"]["status"] == "success":

        order = Order.query.get(order_id)
        order.status = "paid"
        db.session.commit()

        flash("Payment successful!", "success")

    return redirect("/dashboard")


# ---------------- USER DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():

    orders = Order.query.filter_by(
        buyer_email=current_user.email
    ).order_by(Order.id.desc()).all()

    return render_template(
        "dashboard.html",
        orders=orders
    )


# ---------------- ADMIN ----------------

@app.route("/admin")
@login_required
def admin():

    if current_user.role != "admin":
        return redirect("/")

    vehicles = Vehicle.query.all()
    orders = Order.query.order_by(Order.id.desc()).all()

    revenue = db.session.query(
        db.func.sum(Order.amount)
    ).filter(Order.status == "paid").scalar() or 0

    return render_template(
        "admin.html",
        vehicles=vehicles,
        orders=orders,
        revenue=revenue
    )


# ---------------- ADMIN ADD VEHICLE ----------------

@app.route("/admin/add", methods=["POST"])
@login_required
def admin_add():

    if current_user.role != "admin":
        return redirect("/")

    file = request.files.get("image")

    image_url = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )
        file.save(filepath)
        image_url = f"/static/uploads/{filename}"

    vehicle = Vehicle(
        title=request.form["title"],
        price=int(request.form["price"]),
        year=int(request.form["year"]),
        mileage=int(request.form["mileage"]),
        image_url=image_url,
        dealer_id=current_user.id,
        is_approved=True,
    )

    db.session.add(vehicle)
    db.session.commit()

    return redirect("/admin")
