from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_existing_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cars.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/cars'

# Make sure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# ---------- DATABASE MODELS ----------
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)  # float to handle decimals
    description = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(200), nullable=True)

# ---------- ROUTES ----------
@app.route('/')
def home():
    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template('home.html', cars=cars)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        title = request.form.get('title')
        brand = request.form.get('brand')
        price_raw = request.form.get('price', '0').replace(',', '')  # remove commas
        try:
            price = float(price_raw)
        except ValueError:
            flash("Invalid price format!", "danger")
            return redirect(url_for('admin'))

        description = request.form.get('description')

        # Handle image upload
        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename != '':
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)

        # Add car to DB
        new_car = Car(title=title, brand=brand, price=price, description=description, image_filename=image_filename)
        db.session.add(new_car)
        db.session.commit()
        flash("Vehicle published successfully!", "success")
        return redirect(url_for('admin'))

    cars = Car.query.order_by(Car.id.desc()).all()
    return render_template('admin.html', cars=cars)

# ---------- APP INIT ----------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ensures tables exist
    app.run(debug=True)
