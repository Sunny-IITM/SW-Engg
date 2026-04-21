from app import create_app
from extensions import db, bcrypt
from models import User

ADMIN_NAME = "admin"
ADMIN_EMAIL = "admin@admin"
ADMIN_PASSWORD = "password123"

app = create_app()

with app.app_context():
    existing_user = User.query.filter_by(email=ADMIN_EMAIL).first()

    if existing_user:
        existing_user.name = ADMIN_NAME
        existing_user.role = "admin"
        existing_user.is_active = True
        existing_user.password = bcrypt.generate_password_hash(ADMIN_PASSWORD).decode("utf-8")
        db.session.commit()
        print("Updated existing admin user: admin / password123")
    else:
        admin_user = User(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password=bcrypt.generate_password_hash(ADMIN_PASSWORD).decode("utf-8"),
            role="admin",
            is_active=True,
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Created admin user: admin / password123")
