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

    # 🔥 AUTO CREATE ADMIN IF NONE EXISTS
    if not User.query.filter_by(role="admin").first():

        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_password = os.environ.get("ADMIN_PASSWORD")

        if admin_email and admin_password:
            admin = User(
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                role="admin",
            )
            db.session.add(admin)
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


# ---------------- REGISTER DEALER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        user = User(
            email=request.form["email"],
            password_hash=generate_password_hash(
                request.form["password"]
            ),
            role="dealer",
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


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


# ---------------- DEALER DASHBOARD ----------------

@app.route("/dealer")
@login_required
def dealer_dashboard():

    if current_user.role != "dealer":
        return redirect("/")

    vehicles = Vehicle.query.filter_by(
        dealer_id=current_user.id
    ).all()

    return render_template(
        "dealer.html",
        vehicles=vehicles,
    )


@app.route("/dealer/add", methods=["POST"])
@login_required
def dealer_add():

    if current_user.role != "dealer":
        return redirect("/")

    file = request.files["image"]

    filename = secure_filename(file.filename)
    path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename,
    )

    file.save(path)

    v = Vehicle(
        title=request.form["title"],
        price=int(request.form["price"]),
        year=int(request.form["year"]),
        mileage=int(request.form["mileage"]),
        image_url=f"/static/uploads/{filename}",
        dealer_id=current_user.id,
        is_approved=False,
    )

    db.session.add(v)
    db.session.commit()

    return redirect("/dealer")


# ---------------- ADMIN PANEL ----------------

@app.route("/admin")
@login_required
def admin():

    if current_user.role != "admin":
        return redirect("/")

    pending = Vehicle.query.filter_by(
        is_approved=False
    ).all()

    dealers = User.query.filter_by(
        role="dealer"
    ).all()

    return render_template(
        "admin.html",
        vehicles=pending,
        dealers=dealers,
    )


@app.route("/admin/approve/<int:id>")
@login_required
def approve_vehicle(id):

    if current_user.role != "admin":
        return redirect("/")

    v = Vehicle.query.get_or_404(id)
    v.is_approved = True
    db.session.commit()

    return redirect("/admin")


@app.route("/admin/promote/<int:id>")
@login_required
def promote_dealer(id):

    if current_user.role != "admin":
        return redirect("/")

    user = User.query.get_or_404(id)
    user.role = "admin"
    db.session.commit()

    return redirect("/admin")
