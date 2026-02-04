from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "YOUR_EXISTING_SECRET_KEY"

# SQLite DB path (persistent storage on Render)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "cars.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload folder
UPLOAD_FOLDER = os.path.join(basedir, "static/uploads/cars")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# ---------- Models ----------
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)  # float handles $ and decimals
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(200), nullable=True)

# ---------- Routes ----------
@app.route("/")
def home():
    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("home.html", cars=cars)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        title = request.form.get("title")
        brand = request.form.get("brand")
        price = float(request.form.get("price", 0))  # ✅ handle decimals
        description = request.form.get("description")
        image = request.files.get("image")

        image_filename = None
        if image:
            image_filename = image.filename
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

        new_car = Car(
            title=title,
            brand=brand,
            price=price,
            description=description,
            image_filename=image_filename
        )
        db.session.add(new_car)
        db.session.commit()
        flash("Car published successfully!", "success")
        return redirect(url_for("admin"))

    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("admin.html", cars=cars)

# ---------- Auto-create DB ----------
with app.app_context():
    db.create_all()  # 🔹 This ensures the 'car' table exists

if __name__ == "__main__":
    app.run(debug=True)
