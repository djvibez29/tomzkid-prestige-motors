import os
import csv
from werkzeug.utils import secure_filename

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from werkzeug.security import check_password_hash

from extensions import db, login_manager
from models import User, Vehicle


# ---------------------------------
# CONFIG
# ---------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

db_url = os.environ.get("DATABASE_URL")

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------------------------
# INIT
# ---------------------------------

db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


# ---------------------------------
# HOME + SEARCH
# ---------------------------------

@app.route("/")
def home():

    page = request.args.get("page", 1, type=int)

    query = Vehicle.query

    q = request.args.get("q")

    if q:
        query = query.filter(Vehicle.title.ilike(f"%{q}%"))

    pagination = query.order_by(
        Vehicle.created_at.desc()
    ).paginate(page=page, per_page=12)

    return render_template(
        "home.html",
        vehicles=pagination.items,
        pagination=pagination,
    )


# ---------------------------------
# VEHICLE PAGE
# ---------------------------------

@app.route("/vehicle/<int:vehicle_id>")
def vehicle_detail(vehicle_id):

    vehicle = Vehicle.query.get_or_404(vehicle_id)

    return render_template("vehicle_detail.html", vehicle=vehicle)


# ---------------------------------
# LOGIN
# ---------------------------------

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


# ---------------------------------
# ADMIN DASHBOARD
# ---------------------------------

@app.route("/admin")
@login_required
def admin():

    if not current_user.is_admin:
        return redirect("/")

    vehicles = Vehicle.query.order_by(
        Vehicle.created_at.desc()
    ).all()

    return render_template("admin.html", vehicles=vehicles)


# ---------------------------------
# IMAGE HELPER
# ---------------------------------

def allowed_file(filename):

    return "." in filename and (
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ---------------------------------
# ADD VEHICLE
# ---------------------------------

@app.route("/admin/add", methods=["POST"])
@login_required
def add_vehicle():

    if not current_user.is_admin:
        return redirect("/")

    image_url = None

    if "image" in request.files:

        file = request.files["image"]

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename,
            )

            file.save(path)

            image_url = f"/static/uploads/{filename}"

    v = Vehicle(
        title=request.form["title"],
        price=int(request.form["price"]),
        year=int(request.form["year"]),
        mileage=int(request.form["mileage"]),
        image_url=image_url,
    )

    db.session.add(v)
    db.session.commit()

    return redirect("/admin")


# ---------------------------------
# DELETE
# ---------------------------------

@app.route("/admin/delete/<int:id>")
@login_required
def delete_vehicle(id):

    if not current_user.is_admin:
        return redirect("/")

    v = Vehicle.query.get_or_404(id)

    db.session.delete(v)
    db.session.commit()

    return redirect("/admin")


# ---------------------------------
# CSV BULK UPLOAD
# ---------------------------------

@app.route("/admin/upload-csv", methods=["POST"])
@login_required
def upload_csv():

    if not current_user.is_admin:
        return redirect("/")

    file = request.files["csv"]

    stream = file.stream.read().decode("utf-8").splitlines()

    reader = csv.DictReader(stream)

    for row in reader:

        v = Vehicle(
            title=row["title"],
            price=int(row["price"]),
            year=int(row["year"]),
            mileage=int(row["mileage"]),
            image_url=row.get("image_url"),
        )

        db.session.add(v)

    db.session.commit()

    return redirect("/admin")
