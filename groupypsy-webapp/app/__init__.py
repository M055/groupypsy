from flask import Flask
import os

def create_app():
    app = Flask(
        __name__,
        static_folder='../static',  # Adjust for relative path from `app/__init__.py`
        template_folder='../templates')
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['UPLOAD_FOLDER'] = 'instance/uploads'
    app.config['PROCESSED_FOLDER'] = 'static/download'
    app.config['PLOT_FOLDER'] = 'static/plots'

    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PLOT_FOLDER'], exist_ok=True)

    # Import and register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
