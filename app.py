import os

from flask import Flask, render_template, redirect, url_for, request
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager
from models import User, Vehicle


# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///local.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# -------------------------------------------------
# INIT EXTENSIONS
# -------------------------------------------------

db.init_app(app)
login_manager.init_app(app)


# -------------------------------------------------
# LOGIN LOADER  (FIXES YOUR CRASH)
# -------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------------------------------
# CREATE TABLES
# -------------------------------------------------

with app.app_context():
    db.create_all()


# -------------------------------------------------
# ROUTES
# -------------------------------------------------

@app.route("/")
def home():
    page = request.args.get("page", 1, type=int)

    pagination = Vehicle.query.paginate(
        page=page,
        per_page=12,
        error_out=False,
    )

    vehicles = pagination.items

    return render_template(
        "home.html",
        vehicles=vehicles,
        pagination=pagination,
    )


# -------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("home"))

    return render_template("login.html")


# -------------------------------------------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# -------------------------------------------------

@app.route("/admin")
@login_required
def admin():

    if not current_user.is_admin:
        return redirect(url_for("home"))

    vehicles = Vehicle.query.all()

    return render_template("admin.html", vehicles=vehicles)


# -------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
