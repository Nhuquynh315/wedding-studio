from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config

# Initialize extensions at module level
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app(config_name='default'):
    """
    Application factory function
    
    Args:
        config_name: Configuration name ('development', 'testing', 'production', 'default')
    
    Returns:
        Flask application instance
    """
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Import models so Flask-Migrate/SQLAlchemy can detect them
    from app import models  # noqa: F401

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes import auth_bp, wedding_bp, guests_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(wedding_bp)
    app.register_blueprint(guests_bp)
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/csrf.html'), 400

    return app
