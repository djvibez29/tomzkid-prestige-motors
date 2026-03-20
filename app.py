import os
import requests
from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import text, or_, func

from extensions import db, login_manager
from models import User, Vehicle, Order

# ---------------- APP SETUP ----------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecret")

# ---------------- DATABASE ----------------

db_url = os.environ.get("DATABASE_URL")

if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------------- UPLOADS (FIXED) ----------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- PAYSTACK ----------------

PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY")

# ---------------- MARKETPLACE ----------------

COMMISSION_PERCENT = 10

# ---------------- INIT ----------------

db.init_app(app)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- SAFE DB FIX ----------------

with app.app_context():
    db.create_all()

    fixes = [
        'ALTER TABLE vehicle ADD COLUMN IF NOT EXISTS description TEXT',
        'ALTER TABLE vehicle ADD COLUMN IF NOT EXISTS images JSON',
        'ALTER TABLE "order" ADD COLUMN IF NOT EXISTS commission INTEGER DEFAULT 0',
        'ALTER TABLE "order" ADD COLUMN IF NOT EXISTS dealer_earnings INTEGER DEFAULT 0',
        'ALTER TABLE "order" ADD COLUMN IF NOT EXISTS user_id INTEGER'
    ]

    for stmt in fixes:
        try:
            db.session.execute(text(stmt))
            db.session.commit()
        except:
            db.session.rollback()

    # Create admin
    if not User.query.filter_by(email="admin@gmail.com").first():
        admin = User(
            email="admin@gmail.com",
            password_hash=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

# ---------------- HOME ----------------

@app.route("/")
def home():
    brand = request.args.get("brand")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")

    query = Vehicle.query.filter(
        or_(Vehicle.is_approved == True, Vehicle.is_approved == None)
    )

    if brand:
        query = query.filter(Vehicle.title.ilike(f"%{brand}%"))
    if min_price:
        query = query.filter(Vehicle.price >= int(min_price))
    if max_price:
        query = query.filter(Vehicle.price <= int(max_price))

    vehicles = query.order_by(Vehicle.id.desc()).all()

    return render_template("home.html", vehicles=vehicles)

# ---------------- VEHICLE DETAIL ----------------

@app.route("/vehicle/<int:id>")
def vehicle_detail(id):
    vehicle = Vehicle.query.get_or_404(id)
    return render_template("vehicle_detail.html", vehicle=vehicle)

# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()

        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)

            if user.role == "admin":
                return redirect("/admin")
            elif user.role == "dealer":
                return redirect("/dealer")
            else:
                return redirect("/dashboard")

    return render_template("login.html")

# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# ---------------- BUY ----------------

@app.route("/buy/<int:vehicle_id>")
@login_required
def buy(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    commission = int(vehicle.price * COMMISSION_PERCENT / 100)
    dealer_earnings = vehicle.price - commission

    order = Order(
        user_id=current_user.id,
        buyer_email=current_user.email,
        vehicle_id=vehicle.id,
        amount=vehicle.price,
        commission=commission,
        dealer_earnings=dealer_earnings,
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
        "callback_url": url_for("verify_payment", order_id=order.id, _external=True)
    }

    res = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=data,
        headers=headers
    ).json()

    return redirect(res["data"]["authorization_url"])

# ---------------- VERIFY ----------------

@app.route("/verify/<int:order_id>")
@login_required
def verify_payment(order_id):
    reference = request.args.get("reference")

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}

    res = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers=headers
    ).json()

    if res["data"]["status"] == "success":
        order = Order.query.get(order_id)
        order.status = "paid"
        db.session.commit()

    return redirect("/dashboard")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", orders=orders)

# ---------------- DEALER ----------------

@app.route("/dealer")
@login_required
def dealer():
    if current_user.role != "dealer":
        return redirect("/")

    vehicles = Vehicle.query.filter_by(dealer_id=current_user.id).all()

    orders = Order.query.join(Vehicle).filter(
        Vehicle.dealer_id == current_user.id,
        Order.status == "paid"
    ).all()

    earnings = sum(o.dealer_earnings for o in orders)

    return render_template(
        "dealer_dashboard.html",
        vehicles=vehicles,
        orders=orders,
        earnings=earnings
    )

# ---------------- ADMIN ----------------

@app.route("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        return redirect("/")

    vehicles = Vehicle.query.all()
    orders = Order.query.all()

    revenue = db.session.query(func.sum(Order.commission)).scalar() or 0

    return render_template(
        "admin.html",
        vehicles=vehicles,
        orders=orders,
        revenue=revenue
    )

# ---------------- APPROVE ----------------

@app.route("/admin/approve/<int:id>")
@login_required
def approve(id):
    vehicle = Vehicle.query.get_or_404(id)
    vehicle.is_approved = True
    db.session.commit()
    return redirect("/admin")

# ---------------- DELETE ----------------

@app.route("/admin/delete/<int:id>")
@login_required
def delete(id):
    vehicle = Vehicle.query.get_or_404(id)
    db.session.delete(vehicle)
    db.session.commit()
    return redirect("/admin")

# ---------------- ADD VEHICLE (UPLOAD FIXED) ----------------

@app.route("/admin/add", methods=["POST"])
@login_required
def add_vehicle():
    file = request.files.get("image")
    image_url = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        file.save(filepath)

        # THIS is what makes it show on site
        image_url = f"/static/uploads/{filename}"

    vehicle = Vehicle(
        title=request.form["title"],
        price=int(request.form["price"]),
        year=int(request.form["year"]),
        mileage=int(request.form["mileage"]),
        description=request.form.get("description"),
        image_url=image_url,
        dealer_id=current_user.id,
        is_approved=True
    )

    db.session.add(vehicle)
    db.session.commit()

    return redirect("/admin")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
