import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "cars.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "supersecret"

db = SQLAlchemy(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------ MODELS ------------------

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)
    image = db.Column(db.String(200))

# ------------------ AUTO CREATE TABLES ------------------

@app.before_request
def create_tables():
    db.create_all()

# ------------------ ROUTES ------------------

@app.route("/")
def home():
    cars = Car.query.order_by(Car.id.desc()).limit(12).all()
    return render_template("home.html", cars=cars)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        title = request.form["title"]
        price = request.form["price"]
        description = request.form["description"]

        image_file = request.files.get("image")
        filename = None

        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)

        car = Car(
            title=title,
            price=price,
            description=description,
            image=filename,
        )

        db.session.add(car)
        db.session.commit()

        return redirect(url_for("admin"))

    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template("admin.html", cars=cars)

@app.route("/delete/<int:car_id>")
def delete(car_id):
    car = Car.query.get_or_404(car_id)

    if car.image:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], car.image))
        except:
            pass

    db.session.delete(car)
    db.session.commit()

    return redirect(url_for("admin"))

# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(debug=True)
