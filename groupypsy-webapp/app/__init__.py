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











#from flask import Flask, session
#from .routes import main_bp
#
#def create_app():
#    """Application factory function."""
#    app = Flask(
#        __name__,
#        static_folder='../static',  # Adjust for relative path from `app/__init__.py`
#        template_folder='../templates'
#    )
#    # Other configurations remain unchanged
#    app.config['SECRET_KEY'] = 'your-secret-key'
#    app.config['UPLOAD_FOLDER'] = 'instance/uploads/'
#    app.config['PROCESSED_FOLDER'] = 'static/download/'
#    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file uploads to 16 MB
#
#    # Ensure SameSite=None for session cookies
#    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
#    app.config['SESSION_COOKIE_SECURE'] = True  # Requires HTTPS
#
#    # Register Blueprints
#    app.register_blueprint(main_bp)
#
#    # Cleanup session-specific files at the end of the request context
#    @app.teardown_appcontext
#    def cleanup_session_files(exception=None):
#        uploaded_files = session.pop('uploaded_files', [])
#        for file_path in uploaded_files:
#            if os.path.exists(file_path):
#                os.remove(file_path)
#                app.logger.info(f"Deleted: {file_path}")
#
#
#
 #   return app