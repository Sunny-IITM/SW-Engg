from flask import Flask
from flask_cors import CORS
from sqlalchemy import text
from config import Config
from extensions import db, bcrypt, jwt
from routes.auth import auth
from routes.products import products
from routes.inventory import inventory
from routes.analytics import analytics
from routes.admin_users import admin_users
from routes.cart import cart
from routes.orders import orders
from routes.payroll import payroll
from routes.profile import profile
from routes.production import production
from routes.kulhad_detection import kulhad_detection
import os
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


LEGACY_USER_PROFILE_COLUMNS = ["phone", "address", "department", "job_title"]
_daily_report_scheduler_started = False


def rebuild_user_table_without_legacy_columns(cursor, legacy_user_columns):
    removable_columns = [column for column in LEGACY_USER_PROFILE_COLUMNS if column in legacy_user_columns]
    if not removable_columns:
        return legacy_user_columns

    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.execute("ALTER TABLE user RENAME TO user_legacy")
    cursor.execute(
        """
        CREATE TABLE user (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(120) UNIQUE,
            password VARCHAR(200),
            role VARCHAR(20),
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO user (id, name, email, password, role, is_active, created_at)
        SELECT id, name, email, password, role, is_active, created_at
        FROM user_legacy
        """
    )
    cursor.execute("DROP TABLE user_legacy")
    cursor.execute("PRAGMA foreign_keys=ON")
    return {"id", "name", "email", "password", "role", "is_active", "created_at"}



def ensure_profile_schema(app):
    legacy_user_columns = set()

    with app.app_context():
        connection = db.engine.raw_connection()
        try:
            cursor = connection.cursor()

            cursor.execute("PRAGMA table_info(user)")
            legacy_user_columns = {row[1] for row in cursor.fetchall()}
            if "is_active" not in legacy_user_columns:
                cursor.execute("ALTER TABLE user ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
                legacy_user_columns.add("is_active")

            schema_updates = {
                "customer": {
                    "user_id": "ALTER TABLE customer ADD COLUMN user_id INTEGER",
                    "city": "ALTER TABLE customer ADD COLUMN city VARCHAR(100) DEFAULT ''",
                    "state": "ALTER TABLE customer ADD COLUMN state VARCHAR(100) DEFAULT ''",
                    "postal_code": "ALTER TABLE customer ADD COLUMN postal_code VARCHAR(20) DEFAULT ''",
                },
                "employee": {
                    "user_id": "ALTER TABLE employee ADD COLUMN user_id INTEGER",
                    "phone": "ALTER TABLE employee ADD COLUMN phone VARCHAR(30) DEFAULT ''",
                    "address": "ALTER TABLE employee ADD COLUMN address VARCHAR(255) DEFAULT ''",
                    "department": "ALTER TABLE employee ADD COLUMN department VARCHAR(100) DEFAULT ''",
                    "job_title": "ALTER TABLE employee ADD COLUMN job_title VARCHAR(100) DEFAULT ''",
                },
                "payment": {
                    "status": "ALTER TABLE payment ADD COLUMN status VARCHAR(20) DEFAULT 'Pending'",
                },
                "inventory": {
                    "category": "ALTER TABLE inventory ADD COLUMN category VARCHAR(50) DEFAULT 'Clay'",
                    "supplier_name": "ALTER TABLE inventory ADD COLUMN supplier_name VARCHAR(120) DEFAULT ''",
                    "reorder_level": "ALTER TABLE inventory ADD COLUMN reorder_level FLOAT DEFAULT 0",
                    "cost_per_unit": "ALTER TABLE inventory ADD COLUMN cost_per_unit FLOAT DEFAULT 0",
                    "last_restocked": "ALTER TABLE inventory ADD COLUMN last_restocked DATE",
                },
                "product": {
                    "category": "ALTER TABLE product ADD COLUMN category VARCHAR(100) DEFAULT 'Kulhad'",
                    "wage_per_kulhad": "ALTER TABLE product ADD COLUMN wage_per_kulhad FLOAT DEFAULT 0",
                },
                "production_entry": {
                    "product_id": "ALTER TABLE production_entry ADD COLUMN product_id INTEGER",
                    "product_name": "ALTER TABLE production_entry ADD COLUMN product_name VARCHAR(100) DEFAULT ''",
                    "wage_per_kulhad": "ALTER TABLE production_entry ADD COLUMN wage_per_kulhad FLOAT DEFAULT 0",
                    "wage_amount": "ALTER TABLE production_entry ADD COLUMN wage_amount FLOAT DEFAULT 0",
                },
            }

            for table_name, required_columns in schema_updates.items():
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_columns = {row[1] for row in cursor.fetchall()}
                for column_name, statement in required_columns.items():
                    if column_name not in existing_columns:
                        cursor.execute(statement)

            connection.commit()
        finally:
            connection.close()

    with app.app_context():
        db.session.execute(text("UPDATE inventory SET category = 'Clay' WHERE category IS NULL OR TRIM(category) = ''"))
        db.session.execute(text("UPDATE inventory SET supplier_name = '' WHERE supplier_name IS NULL"))
        db.session.execute(text("UPDATE inventory SET reorder_level = 0 WHERE reorder_level IS NULL"))
        db.session.execute(text("UPDATE inventory SET cost_per_unit = 0 WHERE cost_per_unit IS NULL"))
        db.session.execute(text("UPDATE inventory SET last_restocked = DATE('now') WHERE last_restocked IS NULL OR TRIM(last_restocked) = ''"))
        db.session.execute(text("UPDATE product SET category = 'Kulhad' WHERE category IS NULL OR TRIM(category) = ''"))
        db.session.execute(text("UPDATE product SET wage_per_kulhad = 0 WHERE wage_per_kulhad IS NULL"))
        db.session.execute(text("UPDATE production_entry SET product_name = '' WHERE product_name IS NULL"))
        db.session.execute(text("UPDATE production_entry SET wage_per_kulhad = 0 WHERE wage_per_kulhad IS NULL"))
        db.session.execute(text("UPDATE production_entry SET wage_amount = COALESCE(total_quantity, 0) * COALESCE(wage_per_kulhad, 0) WHERE wage_amount IS NULL OR wage_amount = 0"))
        db.session.execute(
            text(
                """
                UPDATE payment
                SET status = CASE
                    WHEN payment_method = 'Cash on Delivery' THEN 'Pending'
                    ELSE 'Paid'
                END
                WHERE status IS NULL OR TRIM(status) = ''
                """
            )
        )
        db.session.commit()

    with app.app_context():
        from models import Customer, Employee, User

        legacy_profile_data = {}
        legacy_fields = [column for column in LEGACY_USER_PROFILE_COLUMNS if column in legacy_user_columns]
        if legacy_fields:
            select_list = ", ".join(["id"] + legacy_fields)
            rows = db.session.execute(text(f"SELECT {select_list} FROM user")).mappings().all()
            legacy_profile_data = {row["id"]: dict(row) for row in rows}

        customers_by_user = {item.user_id: item for item in Customer.query.filter(Customer.user_id.isnot(None)).all()}
        employees_by_user = {item.user_id: item for item in Employee.query.filter(Employee.user_id.isnot(None)).all()}

        changed = False
        for user in User.query.order_by(User.id.asc()).all():
            legacy_values = legacy_profile_data.get(user.id, {})

            if user.role == "customer":
                customer = customers_by_user.get(user.id)
                if customer is None:
                    customer = Customer(user_id=user.id)
                    db.session.add(customer)
                    customers_by_user[user.id] = customer
                    changed = True

                desired_name = user.name or ""
                desired_phone = legacy_values.get("phone") or customer.phone_number or ""
                desired_address = legacy_values.get("address") or customer.address or ""

                if customer.name != desired_name:
                    customer.name = desired_name
                    changed = True
                if (customer.phone_number or "") != desired_phone:
                    customer.phone_number = desired_phone
                    changed = True
                if (customer.address or "") != desired_address:
                    customer.address = desired_address
                    changed = True

            if user.role == "employee":
                employee = employees_by_user.get(user.id)
                if employee is None:
                    employee = Employee(user_id=user.id)
                    db.session.add(employee)
                    employees_by_user[user.id] = employee
                    changed = True

                desired_name = user.name or ""
                desired_phone = legacy_values.get("phone") or employee.phone or ""
                desired_address = legacy_values.get("address") or employee.address or ""
                desired_department = legacy_values.get("department") or employee.department or ""
                desired_job_title = legacy_values.get("job_title") or employee.job_title or employee.role or ""

                if employee.name != desired_name:
                    employee.name = desired_name
                    changed = True
                if (employee.phone or "") != desired_phone:
                    employee.phone = desired_phone
                    changed = True
                if (employee.address or "") != desired_address:
                    employee.address = desired_address
                    changed = True
                if (employee.department or "") != desired_department:
                    employee.department = desired_department
                    changed = True
                if (employee.job_title or "") != desired_job_title:
                    employee.job_title = desired_job_title
                    changed = True
                if (employee.role or "") != desired_job_title:
                    employee.role = desired_job_title
                    changed = True

        if changed:
            db.session.commit()

    with app.app_context():
        connection = db.engine.raw_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("PRAGMA table_info(user)")
            current_user_columns = {row[1] for row in cursor.fetchall()}
            rebuild_user_table_without_legacy_columns(cursor, current_user_columns)
            connection.commit()
        finally:
            connection.close()


def get_database_file_path(app):
    database_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not database_uri.startswith("sqlite:///"):
        return None

    relative_path = database_uri.replace("sqlite:///", "", 1)
    if os.path.isabs(relative_path):
        return relative_path

    return os.path.join(app.instance_path, relative_path)


def start_daily_report_scheduler(app):
    global _daily_report_scheduler_started

    if _daily_report_scheduler_started or app.config.get("TESTING"):
        return

    if not app.config.get("ENABLE_DAILY_REPORT_SCHEDULER", True):
        return

    if not app.config.get("GOOGLE_CHAT_WEBHOOK_URL"):
        app.logger.info("Daily report scheduler skipped because GOOGLE_CHAT_WEBHOOK_URL is not configured.")
        return

    timezone_name = app.config.get("DAILY_REPORT_TIMEZONE", "Asia/Kolkata")
    hour = int(app.config.get("DAILY_REPORT_HOUR", 20))
    minute = int(app.config.get("DAILY_REPORT_MINUTE", 20))

    def scheduler_loop():
        while True:
            now = datetime.now(ZoneInfo(timezone_name))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run = next_run + timedelta(days=1)

            sleep_seconds = max((next_run - now).total_seconds(), 1)
            time.sleep(sleep_seconds)

            with app.app_context():
                try:
                    from routes.analytics import send_google_chat_daily_report

                    result = send_google_chat_daily_report()
                    app.logger.info(result["message"])
                except Exception as error:
                    app.logger.exception("Daily report scheduler failed: %s", error)

    worker = threading.Thread(target=scheduler_loop, name="daily-report-scheduler", daemon=True)
    worker.start()
    _daily_report_scheduler_started = True
    app.logger.info("Daily report scheduler started for %02d:%02d %s.", hour, minute, timezone_name)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)

    app.register_blueprint(auth, url_prefix="/api/auth")
    app.register_blueprint(products, url_prefix="/api/products")
    app.register_blueprint(inventory, url_prefix="/api/inventory")
    app.register_blueprint(analytics, url_prefix="/api/analytics")
    app.register_blueprint(admin_users, url_prefix="/api/admin")
    app.register_blueprint(cart, url_prefix="/api/cart")
    app.register_blueprint(orders, url_prefix="/api/orders")
    app.register_blueprint(payroll, url_prefix="/api/payroll")
    app.register_blueprint(profile, url_prefix="/api/profile")
    app.register_blueprint(production, url_prefix="/api/production")
    app.register_blueprint(kulhad_detection)

    db_path = "database.db"

    with app.app_context():
        database_file_path = get_database_file_path(app) or db_path
        if not os.path.exists(database_file_path):
            print("Database not found. Creating new database...")
        else:
            print("Database already exists. Ensuring schema is up to date.")
        db.create_all()

    ensure_profile_schema(app)

    should_start_scheduler = not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if should_start_scheduler:
        start_daily_report_scheduler(app)

    @app.cli.command("send-daily-report")
    def send_daily_report_command():
        from routes.analytics import send_google_chat_daily_report

        result = send_google_chat_daily_report()
        print(result["message"])

    @app.cli.command("seed-db")
    def seed_db_command():
        from seed_data import seed_database

        summary = seed_database(app, reset=False)
        print(summary)

    @app.cli.command("reset-seed-db")
    def reset_seed_db_command():
        from seed_data import seed_database

        summary = seed_database(app, reset=True)
        print(summary)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
