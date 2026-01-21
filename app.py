from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "dev-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------- MODEL ----------------
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price_usd = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(300), nullable=False)

# ---------------- ADMIN ----------------
ADMIN_USER = "OGTomzkid"
ADMIN_PASS = "Ajetomiwa29"

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    cars = Car.query.all()
    return render_template("index.html", cars=cars)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    if request.method == "POST":
        file = request.files["image"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        car = Car(
            name=request.form["name"],
            price_usd=request.form["price_usd"],
            description=request.form["description"],
            image=filename
        )
        db.session.add(car)
        db.session.commit()
        return redirect("/admin")

    cars = Car.query.all()
    return render_template("admin.html", cars=cars)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if (
            request.form["username"] == ADMIN_USER
            and request.form["password"] == ADMIN_PASS
        ):
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Invalid login"

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- INIT ----------------
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
