import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static/uploads/cars")

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

from models import User, Car, CarImage, Favorite

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_first_request
def create_tables():
    db.create_all()


# ---------------- HOME ----------------

@app.route("/")
def home():
    page = request.args.get("page", 1, type=int)

    pagination = Car.query.order_by(Car.id.desc()).paginate(page=page, per_page=12)
    cars = pagination.items

    return render_template("home.html", cars=cars, pagination=pagination)


# ---------------- DETAIL ----------------

@app.route("/car/<int:car_id>")
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template("car_detail.html", car=car)


# ---------------- AUTH ----------------

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            email=request.form["email"]
        )
        user.set_password(request.form["password"])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and user.check_password(request.form["password"]):
            login_user(user)
            return redirect(url_for("home"))
        flash("Invalid login")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# ---------------- FAVORITES ----------------

@app.route("/favorite/<int:car_id>")
@login_required
def favorite(car_id):
    fav = Favorite.query.filter_by(user_id=current_user.id, car_id=car_id).first()
    if not fav:
        fav = Favorite(user_id=current_user.id, car_id=car_id)
        db.session.add(fav)
        db.session.commit()
    return redirect(request.referrer or url_for("home"))


# ---------------- ADMIN ----------------

@app.route("/admin", methods=["GET","POST"])
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for("home"))

    if request.method == "POST":
        car = Car(
            title=request.form["title"],
            price=request.form["price"],
            description=request.form["description"]
        )
        db.session.add(car)
        db.session.commit()

        files = request.files.getlist("images")
        for f in files:
            if f.filename:
                name = secure_filename(f.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], name)
                f.save(path)
                img = CarImage(car_id=car.id, filename=name)
                db.session.add(img)

        db.session.commit()
        return redirect(url_for("admin"))

    cars = Car.query.all()
    return render_template("admin.html", cars=cars)


if __name__ == "__main__":
    app.run(debug=True)
