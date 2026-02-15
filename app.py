import os
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from flask import Flask, render_template, redirect, request, url_for, flash

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager
from models import User, Vehicle, Wishlist


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
            plan="pro",
        )
        db.session.add(admin)
        db.session.commit()


# ---------------- HOME ----------------

@app.route("/")
def home():

    search = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)

    query = Vehicle.query.filter_by(is_approved=True)

    if search:
        query = query.filter(
            or_(
                Vehicle.brand.ilike(f"%{search}%"),
                Vehicle.model.ilike(f"%{search}%"),
            )
        )

    vehicles = query.order_by(
        Vehicle.created_at.desc()
    ).paginate(page=page, per_page=12)

    return render_template("home.html", vehicles=vehicles)


# ---------------- VEHICLE DETAIL ----------------

@app.route("/vehicle/<int:id>")
def vehicle_detail(id):

    vehicle = Vehicle.query.get_or_404(id)
    dealer = User.query.get(vehicle.dealer_id)

    return render_template("vehicle_detail.html", vehicle=vehicle, dealer=dealer)


# ---------------- WISHLIST ----------------

@app.route("/wishlist")
@login_required
def wishlist():

    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template("wishlist.html", items=items)


@app.route("/wishlist/add/<int:vehicle_id>")
@login_required
def add_to_wishlist(vehicle_id):

    item = Wishlist(user_id=current_user.id, vehicle_id=vehicle_id)
    db.session.add(item)
    db.session.commit()

    return redirect(request.referrer)


# ---------------- DEALER DASHBOARD ----------------

@app.route("/dealer")
@login_required
def dealer():

    if current_user.role != "dealer":
        return redirect("/")

    vehicles = Vehicle.query.filter_by(dealer_id=current_user.id).all()
    return render_template("dealer.html", vehicles=vehicles)


@app.route("/dealer/add", methods=["POST"])
@login_required
def dealer_add():

    if current_user.plan == "free":
        flash("Upgrade your plan to upload vehicles")
        return redirect("/dealer")

    file = request.files.get("image")

    image_url = None
    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        image_url = f"/static/uploads/{filename}"

    vehicle = Vehicle(
        brand=request.form.get("brand"),
        model=request.form.get("model"),
        price=request.form.get("price"),
        dealer_id=current_user.id,
        image_url=image_url,
        is_approved=False,
    )

    db.session.add(vehicle)
    db.session.commit()

    return redirect("/dealer")


# ---------------- ADMIN PANEL ----------------

@app.route("/admin")
@login_required
def admin():

    if current_user.role != "admin":
        return redirect("/")

    total_users = User.query.count()
    total_dealers = User.query.filter_by(role="dealer").count()
    total_vehicles = Vehicle.query.count()
    pending = Vehicle.query.filter_by(is_approved=False).count()

    vehicles = Vehicle.query.order_by(Vehicle.created_at.desc()).all()

    return render_template(
        "admin.html",
        vehicles=vehicles,
        total_users=total_users,
        total_dealers=total_dealers,
        total_vehicles=total_vehicles,
        pending=pending,
    )


# ---------------- SUBSCRIPTION ----------------

@app.route("/upgrade/<plan>")
@login_required
def upgrade(plan):

    current_user.plan = plan
    db.session.commit()

    flash(f"You are now on {plan} plan")

    return redirect("/dealer")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
