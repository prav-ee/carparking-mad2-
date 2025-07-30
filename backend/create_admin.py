from app import app, db
from models.user import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='superadmin@parkease.com').first()
        if admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin_user = User(
            full_name='Super Admin',
            email='superadmin@parkease.com',
            password_hash=generate_password_hash('SuperSecret123'),
            role='admin'
        )
        
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully!")
        print("Email: superadmin@parkease.com")
        print("Password: SuperSecret123")

if __name__ == '__main__':
    create_admin_user() 