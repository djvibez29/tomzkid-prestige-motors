import os
from werkzeug.utils import secure_filename

from flask import (
    Flask,
    render_template,
    redirect,
    request,
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from extensions import db, login_manager
from models import User, Vehicle


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
        )
        db.session.add(admin)
        db.session.commit()
    else:
        if admin.role != "admin":
            admin.role = "admin"
            db.session.commit()


# ---------------- HOME ----------------

@app.route("/")
def home():

    vehicles = Vehicle.query.filter_by(
        is_approved=True
    ).order_by(
        Vehicle.created_at.desc()
    ).all()

    return render_template("home.html", vehicles=vehicles)


# ---------------- LOGIN ----------------

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

            if user.role == "dealer":
                return redirect("/dealer")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


# ---------------- ADMIN PANEL ----------------

@app.route("/admin")
@login_required
def admin():

    if current_user.role != "admin":
        return redirect("/")

    vehicles = Vehicle.query.order_by(
        Vehicle.created_at.desc()
    ).all()

    return render_template("admin.html", vehicles=vehicles)


# 🔥 FIXED ADMIN ADD ROUTE (THIS WAS MISSING)

@app.route("/admin/add", methods=["POST"])
@login_required
def admin_add():

    if current_user.role != "admin":
        return redirect("/")

    file = request.files.get("image")

    image_url = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        image_url = f"/static/uploads/{filename}"

    vehicle = Vehicle(
        title=request.form["title"],
        price=int(request.form["price"]),
        year=int(request.form["year"]),
        mileage=int(request.form["mileage"]),
        image_url=image_url,
        dealer_id=current_user.id,
        is_approved=True,  # Admin uploads auto-approved
    )

    db.session.add(vehicle)
    db.session.commit()

    return redirect("/admin")
