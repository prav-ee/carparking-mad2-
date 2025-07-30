from app import app
from extensions import db
from models.user import User
from werkzeug.security import generate_password_hash

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

with app.app_context():
    db.create_all()
    print("All tables created!")

    # Check if admin exists
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        admin = User(
            full_name="Admin",
            email=ADMIN_EMAIL,
            phone="0000000000",
            role="admin",
            password_hash=generate_password_hash(ADMIN_PASSWORD)
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    else:
        print("Admin user already exists.") 