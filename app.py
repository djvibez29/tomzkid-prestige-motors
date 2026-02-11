import os

from flask import Flask, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user

from werkzeug.security import check_password_hash

from extensions import db, login_manager
from models import User, Vehicle


# --------------------------------
# APP CONFIG
# --------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

db_url = os.environ.get("DATABASE_URL")

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///local.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# --------------------------------
# INIT
# --------------------------------

db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


# --------------------------------
# HOME + SEARCH + FILTERS
# --------------------------------

@app.route("/")
def home():

    page = request.args.get("page", 1, type=int)

    query = Vehicle.query

    search = request.args.get("q")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    year = request.args.get("year")

    if search:
        query = query.filter(Vehicle.title.ilike(f"%{search}%"))

    if min_price:
        query = query.filter(Vehicle.price >= min_price)

    if max_price:
        query = query.filter(Vehicle.price <= max_price)

    if year:
        query = query.filter(Vehicle.year == year)

    pagination = query.order_by(
        Vehicle.created_at.desc()
    ).paginate(page=page, per_page=12)

    return render_template(
        "home.html",
        vehicles=pagination.items,
        pagination=pagination,
    )


# --------------------------------
# VEHICLE DETAIL
# --------------------------------

@app.route("/vehicle/<int:vehicle_id>")
def vehicle_detail(vehicle_id):

    vehicle = Vehicle.query.get_or_404(vehicle_id)

    return render_template(
        "vehicle_detail.html",
        vehicle=vehicle,
    )


# --------------------------------
# FAVORITE
# --------------------------------

@app.route("/favorite/<int:vehicle_id>")
@login_required
def favorite(vehicle_id):

    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if vehicle not in current_user.favorites:
        current_user.favorites.append(vehicle)
        db.session.commit()

    return redirect(request.referrer or "/")


@app.route("/favorites")
@login_required
def favorites():

    return render_template(
        "favorites.html",
        vehicles=current_user.favorites,
    )


# --------------------------------
# LOGIN / LOGOUT
# --------------------------------

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
            return redirect("/admin")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


# --------------------------------
# ADMIN
# --------------------------------

@app.route("/admin")
@login_required
def admin():

    if not current_user.is_admin:
        return redirect("/")

    vehicles = Vehicle.query.all()

    return render_template(
        "admin.html",
        vehicles=vehicles,
    )


@app.route("/admin/add", methods=["POST"])
@login_required
def add_vehicle():

    if not current_user.is_admin:
        return redirect("/")

    v = Vehicle(
        title=request.form["title"],
        price=request.form["price"],
        year=request.form["year"],
        mileage=request.form["mileage"],
        image_url=request.form["image_url"],
    )

    db.session.add(v)
    db.session.commit()

    return redirect("/admin")


@app.route("/admin/delete/<int:id>")
@login_required
def delete_vehicle(id):

    if not current_user.is_admin:
        return redirect("/")

    v = Vehicle.query.get_or_404(id)

    db.session.delete(v)
    db.session.commit()

    return redirect("/admin")
