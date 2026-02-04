from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

# ===== Config =====
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicles.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# ===== Models =====
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    vehicle_type = db.Column(db.String(50), nullable=False)
    drivetrain = db.Column(db.String(50), nullable=False)
    engine = db.Column(db.String(50), nullable=False)
    fuel = db.Column(db.String(50), nullable=False)
    images = db.relationship('VehicleImage', backref='vehicle', cascade='all, delete-orphan')

class VehicleImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))

# ===== Helpers =====
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===== Routes =====
@app.route('/')
def home():
    search = request.args.get('search', '')
    vehicle_type = request.args.get('type', '')
    query = Vehicle.query

    if search:
        query = query.filter(Vehicle.title.contains(search) | Vehicle.brand.contains(search))
    if vehicle_type:
        query = query.filter_by(vehicle_type=vehicle_type)

    vehicles = query.order_by(Vehicle.id.desc()).all()
    return render_template('home.html', vehicles=vehicles)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        try:
            title = request.form['title']
            brand = request.form['brand']
            price = float(request.form['price'])
            description = request.form.get('description', '')
            vehicle_type = request.form['vehicle_type']
            drivetrain = request.form['drivetrain']
            engine = request.form['engine']
            fuel = request.form['fuel']

            vehicle = Vehicle(
                title=title,
                brand=brand,
                price=price,
                description=description,
                vehicle_type=vehicle_type,
                drivetrain=drivetrain,
                engine=engine,
                fuel=fuel
            )
            db.session.add(vehicle)
            db.session.commit()

            files = request.files.getlist('images')
            for f in files:
                if f and allowed_file(f.filename):
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    db.session.add(VehicleImage(filename=filename, vehicle=vehicle))
            db.session.commit()
            flash('Vehicle added successfully!', 'success')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
            return redirect(url_for('admin'))

    vehicles = Vehicle.query.order_by(Vehicle.id.desc()).all()
    return render_template('admin.html', vehicles=vehicles)

# ===== Initialize DB =====
with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

if __name__ == '__main__':
    app.run(debug=True)
