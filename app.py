import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300MB


# ---------------- DB ----------------

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            name TEXT,
            price_usd INTEGER,
            miles INTEGER,
            description TEXT,
            image TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- HELPERS ----------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    conn = get_db()
    cars = conn.execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("home.html", cars=cars)


@app.route("/car/<int:car_id>")
def car_page(car_id):
    conn = get_db()
    car = conn.execute(
        "SELECT * FROM cars WHERE id=?",
        (car_id,)
    ).fetchone()
    conn.close()

    if not car:
        return redirect("/")

    images = car["image"].split(",")

    return render_template("car.html", car=car, images=images)


# ---------------- ADMIN ----------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        brand = request.form.get("brand")
        name = request.form.get("name")
        price_usd = request.form.get("price_usd")
        miles = request.form.get("miles")
        description = request.form.get("description")

        files = request.files.getlist("images")

        if not files or files[0].filename == "":
            return redirect("/admin")

        saved_files = []

        for file in files[:50]:

            if file and allowed_file(file.filename):

                filename = secure_filename(file.filename)

                save_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )

                counter = 1
                while os.path.exists(save_path):
                    name_only, ext = os.path.splitext(filename)
                    filename = f"{name_only}_{counter}{ext}"
                    save_path = os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        filename
                    )
                    counter += 1

                file.save(save_path)
                saved_files.append(filename)

        if not saved_files:
            return redirect("/admin")

        conn = get_db()

        conn.execute("""
            INSERT INTO cars
            (brand, name, price_usd, miles, description, image)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            brand,
            name,
            price_usd,
            miles,
            description,
            ",".join(saved_files)
        ))

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("admin.html")
