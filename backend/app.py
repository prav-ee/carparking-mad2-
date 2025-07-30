from flask import Flask
from flask_cors import CORS
from extensions import db, migrate, cache, mail
import os
from werkzeug.security import generate_password_hash
from config import Config
from celery_app import make_celery
from flask_jwt_extended import JWTManager
import logging
from flask_jwt_extended.exceptions import JWTExtendedException
from flask import jsonify

# Import models for migration
from models.user import User
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.vehicle import Vehicle

# Import blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.parking import parking_bp

# Flask app initialization
app = Flask(__name__)
app.config.from_object(Config)
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Change this to a secure value!
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
jwt = JWTManager(app)

# Enable CORS
CORS(app,
     origins=["http://10.253.145.9:8080", "http://localhost:8080", "http://localhost:8081", "http://localhost:8082", "http://192.168.1.8:8080"],
     supports_credentials=True)

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
mail.init_app(app)

# Cache
cache.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(parking_bp, url_prefix='/api/parking')

# Celery configuration
celery = make_celery(app)

logging.basicConfig(level=logging.DEBUG)

@app.errorhandler(JWTExtendedException)
def handle_jwt_errors(e):
    logging.error(f"JWT Error: {str(e)}")
    return jsonify({'error': 'JWT Error', 'message': str(e)}), 422

def create_admin_if_not_exists():
    admin_email = "superadmin@parkease.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User()
        admin.full_name = "Super Admin"
        admin.email = admin_email
        admin.phone = "1234567890"
        admin.password_hash = generate_password_hash("admin123")  # Change this password as needed
        admin.role = "admin"
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    return 'Vehicle Parking App Backend is running!'

if __name__ == '__main__':
    with app.app_context():
        create_admin_if_not_exists()
    app.run(debug=True)
