import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    # DATABASE (Postgres on Render)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///local.db",
    ).replace("postgres://", "postgresql://")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # INIT EXTENSIONS
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # CREATE TABLES AT STARTUP
    with app.app_context():
        db.create_all()

    # ROUTES
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/search")
    def search():
        return render_template("search.html")

    @app.route("/favorites")
    def favorites():
        return render_template("favorites.html")

    @app.route("/reviews")
    def reviews():
        return render_template("reviews.html")

    @app.route("/settings")
    def settings():
        return render_template("settings.html")

    return app


app = create_app()


# LOCAL / FALLBACK RUNNER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
