import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, request, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db, login_manager
from models import User, Vehicle, Wishlist, Order

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
        admin.role = "admin"
        db.session.commit()


# 🏠 HOME WITH SEARCH + PAGINATION
@app.route("/")
def home():
    search = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)

    query = Vehicle.query.filter_by(is_approved=True)

    if search:
        query = query.filter(Vehicle.title.ilike(f"%{search}%"))

    vehicles = query.order_by(Vehicle.created_at.desc()).paginate(page=page, per_page=6)

    return render_template("home.html", vehicles=vehicles)


# 🚗 VEHICLE DETAIL
@app.route("/vehicle/<int:id>")
def vehicle_detail(id):
    vehicle = Vehicle.query.get_or_404(id)
    if not vehicle.is_approved:
        return redirect("/")

    return render_template("vehicle_detail.html", vehicle=vehicle)


# 🔐 LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()

        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)

            if user.role == "admin":
                return redirect("/admin")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


# 🛒 CHECKOUT
@app.route("/checkout/<int:vehicle_id>", methods=["GET", "POST"])
def checkout(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if request.method == "POST":
        order = Order(
            buyer_email=request.form["email"],
            vehicle_id=vehicle.id,
            amount=vehicle.price,
        )

        db.session.add(order)
        db.session.commit()

        return render_template("payment_success.html", vehicle=vehicle)

    return render_template("checkout.html", vehicle=vehicle)


# 🧠 ADMIN PANEL
@app.route("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        return redirect("/")

    vehicles = Vehicle.query.order_by(Vehicle.created_at.desc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()

    revenue = db.session.query(db.func.sum(Order.amount)).filter(Order.status == "paid").scalar() or 0

    return render_template(
        "admin.html",
        vehicles=vehicles,
        orders=orders,
        revenue=revenue,
    )


# ➕ ADD VEHICLE
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
        is_approved=True,
    )

    db.session.add(vehicle)
    db.session.commit()

    return redirect("/admin")


# ✅ MARK ORDER AS PAID (FOR TESTING PAYMENT)
@app.route("/admin/order/<int:id>/paid")
@login_required
def mark_order_paid(id):
    if current_user.role != "admin":
        return redirect("/")

    order = Order.query.get_or_404(id)
    order.status = "paid"
    db.session.commit()

    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)
