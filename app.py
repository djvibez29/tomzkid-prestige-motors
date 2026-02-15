import os
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
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


# ---------------- HOME (SEARCH + FILTER + PAGINATION) ----------------

@app.route("/")
def home():

    search = request.args.get("search", "")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    page = request.args.get("page", 1, type=int)

    query = Vehicle.query.filter_by(is_approved=True)

    if search:
        query = query.filter(
            or_(
                Vehicle.brand.ilike(f"%{search}%"),
                Vehicle.model.ilike(f"%{search}%"),
                Vehicle.title.ilike(f"%{search}%"),
            )
        )

    if min_price:
        query = query.filter(Vehicle.price >= int(min_price))

    if max_price:
        query = query.filter(Vehicle.price <= int(max_price))

    vehicles = query.order_by(
        Vehicle.created_at.desc()
    ).paginate(page=page, per_page=12)

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

            return redirect("/")

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

        # NEW GLOBAL MARKETPLACE FIELDS
        brand=request.form.get("brand"),
        model=request.form.get("model"),
        trim=request.form.get("trim"),

        price=int(request.form.get("price")),
        year=int(request.form.get("year")),
        mileage=int(request.form.get("mileage")),

        transmission=request.form.get("transmission"),
        drivetrain=request.form.get("drivetrain"),
        body_style=request.form.get("body_style"),

        engine_type=request.form.get("engine_type"),
        engine_layout=request.form.get("engine_layout"),

        interior_color=request.form.get("interior_color"),
        exterior_color=request.form.get("exterior_color"),

        # BACKWARD COMPATIBILITY
        title=request.form.get("title"),

        image_url=image_url,
        dealer_id=current_user.id,
        is_approved=True,
    )

    db.session.add(vehicle)
    db.session.commit()

    return redirect("/admin")


# ---------------- DEALER DASHBOARD ----------------

@app.route("/dealer")
@login_required
def dealer():

    if current_user.role != "dealer":
        return redirect("/")

    vehicles = Vehicle.query.filter_by(
        dealer_id=current_user.id
    ).order_by(
        Vehicle.created_at.desc()
    ).all()

    return render_template("dealer.html", vehicles=vehicles)


@app.route("/dealer/add", methods=["POST"])
@login_required
def dealer_add():

    if current_user.role != "dealer":
        return redirect("/")

    file = request.files.get("image")

    image_url = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        image_url = f"/static/uploads/{filename}"

    vehicle = Vehicle(

        brand=request.form.get("brand"),
        model=request.form.get("model"),
        trim=request.form.get("trim"),

        price=int(request.form.get("price")),
        year=int(request.form.get("year")),
        mileage=int(request.form.get("mileage")),

        transmission=request.form.get("transmission"),
        drivetrain=request.form.get("drivetrain"),
        body_style=request.form.get("body_style"),

        engine_type=request.form.get("engine_type"),
        engine_layout=request.form.get("engine_layout"),

        interior_color=request.form.get("interior_color"),
        exterior_color=request.form.get("exterior_color"),

        title=request.form.get("title"),

        image_url=image_url,
        dealer_id=current_user.id,
        is_approved=False,
    )

    db.session.add(vehicle)
    db.session.commit()

    return redirect("/dealer")


# ---------------- APPROVE VEHICLE ----------------

@app.route("/admin/approve/<int:id>")
@login_required
def approve_vehicle(id):

    if current_user.role != "admin":
        return redirect("/")

    vehicle = Vehicle.query.get_or_404(id)
    vehicle.is_approved = True

    db.session.commit()

    return redirect("/admin")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
