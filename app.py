import os

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager
from models import User, Vehicle


# ---------------------------------------
# APP SETUP
# ---------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

db_url = os.environ.get("DATABASE_URL")

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///local.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ---------------------------------------
# INIT EXTENSIONS
# ---------------------------------------

db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


# ---------------------------------------
# HOME WITH PAGINATION
# ---------------------------------------

@app.route("/")
def home():

    page = request.args.get("page", 1, type=int)

    pagination = Vehicle.query.order_by(
        Vehicle.created_at.desc()
    ).paginate(page=page, per_page=12)

    return render_template(
        "home.html",
        vehicles=pagination.items,
        pagination=pagination,
    )


# ---------------------------------------
# LOGIN
# ---------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("admin"))

        flash("Invalid login")

    return render_template("login.html")


# ---------------------------------------
# LOGOUT
# ---------------------------------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# ---------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------

@app.route("/admin")
@login_required
def admin():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    vehicles = Vehicle.query.order_by(
        Vehicle.created_at.desc()
    ).all()

    return render_template("admin.html", vehicles=vehicles)


# ---------------------------------------
# ADD VEHICLE
# ---------------------------------------

@app.route("/admin/add", methods=["POST"])
@login_required
def add_vehicle():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    vehicle = Vehicle(
        title=request.form["title"],
        price=request.form["price"],
        year=request.form["year"],
        mileage=request.form["mileage"],
        image_url=request.form["image_url"],
    )

    db.session.add(vehicle)
    db.session.commit()

    return redirect(url_for("admin"))


# ---------------------------------------
# DELETE VEHICLE
# ---------------------------------------

@app.route("/admin/delete/<int:vehicle_id>")
@login_required
def delete_vehicle(vehicle_id):

    if not current_user.is_admin:
        return redirect(url_for("home"))

    vehicle = Vehicle.query.get_or_404(vehicle_id)

    db.session.delete(vehicle)
    db.session.commit()

    return redirect(url_for("admin"))


# ---------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
