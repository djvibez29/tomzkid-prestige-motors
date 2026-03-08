import os
import requests
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import text, or_

from extensions import db, login_manager
from models import User, Vehicle, Order

# ---------------- APP CREATE ----------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")

# ---------------- DATABASE ----------------
db_url = os.environ.get("DATABASE_URL")
if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------------- UPLOADS ----------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- PAYSTACK ----------------
PAYSTACK_SECRET = os.environ.get("PAYSTACK_SECRET_KEY")

# ---------------- MARKETPLACE SETTINGS ----------------
COMMISSION_PERCENT = 10

# ---------------- INIT EXTENSIONS ----------------
db.init_app(app)
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- AUTO CREATE ADMIN + AUTO DB FIX ----------------
with app.app_context():
    db.create_all()

    # Add missing columns safely
    try:
        db.session.execute(text('ALTER TABLE "orders" ADD COLUMN commission INTEGER DEFAULT 0'))
        db.session.execute(text('ALTER TABLE "orders" ADD COLUMN dealer_earnings INTEGER DEFAULT 0'))
        db.session.commit()
    except:
        pass

    # Create admin if missing
    ADMIN_EMAIL = "tomzkidprestigegroups@gmail.com"
    ADMIN_PASSWORD = "OGTomzkid 29"
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        admin = User(email=ADMIN_EMAIL, password_hash=generate_password_hash(ADMIN_PASSWORD), role="admin")
        db.session.add(admin)
        db.session.commit()

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    brand = request.args.get("brand")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    year = request.args.get("year")
    sort = request.args.get("sort")

    query = Vehicle.query.filter(or_(Vehicle.is_approved == True, Vehicle.is_approved == None))
    if brand: query = query.filter(Vehicle.title.ilike(f"%{brand}%"))
    if min_price: query = query.filter(Vehicle.price >= int(min_price))
    if max_price: query = query.filter(Vehicle.price <= int(max_price))
    if year: query = query.filter(Vehicle.year == int(year))
    if sort == "price_low": query = query.order_by(Vehicle.price.asc())
    elif sort == "price_high": query = query.order_by(Vehicle.price.desc())
    elif sort == "newest": query = query.order_by(Vehicle.year.desc())

    vehicles = query.all()
    return render_template("home.html", vehicles=vehicles)

@app.route("/vehicle/<int:id>")
def vehicle_detail(id):
    vehicle = Vehicle.query.get_or_404(id)
    if vehicle.is_approved is False: return redirect("/")
    dealer = User.query.get(vehicle.dealer_id)
    return render_template("vehicle_detail.html", vehicle=vehicle, dealer=dealer)

# ---------------- AUTH ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)
            if user.role == "admin": return redirect("/admin")
            if user.role == "dealer": return redirect("/dealer")
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# ---------------- BUY VEHICLE ----------------
@app.route("/buy/<int:vehicle_id>")
@login_required
def buy(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    commission = int(vehicle.price * COMMISSION_PERCENT / 100)
    dealer_earnings = vehicle.price - commission

    order = Order(
        buyer_id=current_user.id,
        buyer_email=current_user.email,
        vehicle_id=vehicle.id,
        amount=vehicle.price,
        commission=commission,
        dealer_earnings=dealer_earnings,
        status="pending"
    )
    db.session.add(order)
    db.session.commit()

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}", "Content-Type": "application/json"}
    data = {"email": current_user.email, "amount": vehicle.price * 100,
            "callback_url": url_for("verify_payment", order_id=order.id, _external=True)}
    res = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers).json()
    return redirect(res["data"]["authorization_url"])

@app.route("/verify/<int:order_id>")
@login_required
def verify_payment(order_id):
    reference = request.args.get("reference")
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    res = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers).json()
    if res["data"]["status"] == "success":
        order = Order.query.get(order_id)
        order.status = "paid"
        db.session.commit()
        flash("Payment successful!", "success")
    return redirect("/dashboard")

# ---------------- DASHBOARDS ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    orders = Order.query.filter_by(buyer_email=current_user.email).all()
    return render_template("dashboard.html", orders=orders)

@app.route("/dealer")
@login_required
def dealer_dashboard():
    if current_user.role != "dealer": return redirect("/")
    vehicles = Vehicle.query.filter_by(dealer_id=current_user.id).all()
    orders = Order.query.join(Vehicle).filter(Vehicle.dealer_id == current_user.id, Order.status=="paid").all()
    earnings = sum(o.dealer_earnings for o in orders)
    return render_template("dealer_dashboard.html", vehicles=vehicles, orders=orders, earnings=earnings)

@app.route("/admin")
@login_required
def admin():
    if current_user.role != "admin": return redirect("/")
    vehicles = Vehicle.query.order_by(Vehicle.id.desc()).all()
    orders = Order.query.order_by(Order.id.desc()).all()
    revenue = db.session.query(db.func.sum(Order.commission)).filter(Order.status=="paid").scalar() or 0
    return render_template("admin.html", vehicles=vehicles, orders=orders, revenue=revenue)

# ---------------- ADMIN VEHICLE MANAGEMENT ----------------
@app.route("/admin/approve/<int:id>")
@login_required
def approve_vehicle(id):
    if current_user.role != "admin": return redirect("/")
    vehicle = Vehicle.query.get_or_404(id)
    vehicle.is_approved = True
    db.session.commit()
    flash("Vehicle approved")
    return redirect("/admin")

@app.route("/admin/delete/<int:id>")
@login_required
def delete_vehicle(id):
    if current_user.role != "admin": return redirect("/")
    vehicle = Vehicle.query.get_or_404(id)
    db.session.delete(vehicle)
    db.session.commit()
    flash("Vehicle deleted")
    return redirect("/admin")

@app.route("/admin/add", methods=["POST"])
@login_required
def admin_add():
    if current_user.role != "admin": return redirect("/")

    files = request.files.getlist("images")  # multiple image support
    image_urls = []

    for file in files:
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            image_urls.append(f"/static/uploads/{filename}")

    vehicle = Vehicle(
        title=request.form["title"],
        price=int(request.form["price"]),
        year=int(request.form["year"]),
        mileage=int(request.form.get("mileage", 0)),
        image_url=image_urls[0] if image_urls else None,
        images=",".join(image_urls) if image_urls else None,
        dealer_id=current_user.id,
        is_approved=True
    )

    db.session.add(vehicle)
    db.session.commit()
    return redirect("/admin")
