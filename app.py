import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_jwt_extended import JWTManager
from config import Config

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
jwt = JWTManager()

def create_app(config_class=Config):
    # Create the Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Set secret key
    app.secret_key = os.environ.get("SESSION_SECRET", app.config['SECRET_KEY'])
    
    # Initialize extensions with the app
    db.init_app(app)
    jwt.init_app(app)
    
    # Import and register blueprints
    from routes.auth import auth_bp
    from routes.chatbot import chatbot_bp
    from routes.itinerary import itinerary_bp
    from routes.social import social_bp
    from routes.booking import booking_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(itinerary_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(booking_bp)
    
    # Import routes for the main app
    from routes import main_routes
    
    # Create a route for the home page
    @app.route('/')
    def index():
        return main_routes.index()
    
    # Create database tables if they don't exist
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        import models
        db.create_all()
        
    return app
