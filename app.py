import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from models import db, User, Vehicle, Order

# ================= INIT =================
app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= DATABASE FIX =================
database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ================= UPLOAD CONFIG =================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_app(app)

# ================= SAFE DB INIT =================
with app.app_context():
    try:
        db.create_all()
        print("✅ Database connected")
    except Exception as e:
        print("❌ DB ERROR:", e)


# ================= ROUTES =================

# HOME
@app.route("/")
def home():
    vehicles = Vehicle.query.filter(
        (Vehicle.is_approved == True) | (Vehicle.is_approved == None)
    ).all()
    return render_template("home.html", vehicles=vehicles)


# ADD VEHICLE
@app.route("/add", methods=["GET", "POST"])
def add_vehicle():
    if request.method == "POST":
        title = request.form.get("title")
        price = request.form.get("price")
        year = request.form.get("year")
        mileage = request.form.get("mileage")
        description = request.form.get("description")

        file = request.files.get("image")

        filename = None
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        vehicle = Vehicle(
            title=title,
            price=float(price),
            year=int(year),
            mileage=int(mileage),
            description=description,
            image_url=filename,
            dealer_id=1,  # TEMP (you’ll replace with auth later)
            is_approved=True
        )

        db.session.add(vehicle)
        db.session.commit()

        flash("Vehicle added successfully")
        return redirect(url_for("home"))

    return render_template("add_vehicle.html")


# ADMIN
@app.route("/admin")
def admin():
    vehicles = Vehicle.query.all()
    return render_template("admin.html", vehicles=vehicles)


# DELETE VEHICLE
@app.route("/delete/<int:id>")
def delete_vehicle(id):
    vehicle = Vehicle.query.get_or_404(id)
    db.session.delete(vehicle)
    db.session.commit()
    return redirect(url_for("admin"))


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
