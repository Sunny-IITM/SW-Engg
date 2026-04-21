from datetime import UTC, datetime

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


def utc_today():
    return utc_now().date()

# =========================
# USER
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20), default="customer")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    customer_profile = db.relationship("Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    employee_profile = db.relationship("Employee", back_populates="user", uselist=False, cascade="all, delete-orphan")

# =========================
# EMPLOYEE
# =========================
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    name = db.Column(db.String(100))
    role = db.Column(db.String(50))
    phone = db.Column(db.String(30), default="")
    address = db.Column(db.String(255), default="")
    department = db.Column(db.String(100), default="")
    job_title = db.Column(db.String(100), default="")
    daily_wage = db.Column(db.Float)
    user = db.relationship("User", back_populates="employee_profile")


class PayrollRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    payroll_month = db.Column(db.Integer, nullable=False)
    payroll_year = db.Column(db.Integer, nullable=False)
    base_salary = db.Column(db.Float, default=0)
    bonus = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    working_days = db.Column(db.Integer, default=26)
    total_days = db.Column(db.Integer, default=26)
    status = db.Column(db.String(20), default="pending")
    paid_on = db.Column(db.Date, nullable=True)


class ProductionEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    product_name = db.Column(db.String(100), default="")
    entry_date = db.Column(db.Date, nullable=False, default=utc_today)
    status = db.Column(db.String(20), default="present")
    entry_type = db.Column(db.String(20), default="regular")
    kulhad_quantity = db.Column(db.Integer, default=0)
    cup_quantity = db.Column(db.Integer, default=0)
    total_quantity = db.Column(db.Integer, default=0)
    wage_per_kulhad = db.Column(db.Float, default=0)
    wage_amount = db.Column(db.Float, default=0)
    notes = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=utc_now)


# =========================
# INVENTORY
# =========================
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    raw_material_name = db.Column(db.String(100))
    quantity_available = db.Column(db.Float)
    unit = db.Column(db.String(50))
    category = db.Column(db.String(50), default="Clay")
    supplier_name = db.Column(db.String(120), default="")
    reorder_level = db.Column(db.Float, default=0)
    cost_per_unit = db.Column(db.Float, default=0)
    last_restocked = db.Column(db.Date, default=utc_today)


class RawMaterialHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=True)
    material_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), default="")
    quantity_change = db.Column(db.Float, default=0)
    previous_quantity = db.Column(db.Float, default=0)
    new_quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(50), default="")
    actor_name = db.Column(db.String(100), default="System")
    created_at = db.Column(db.DateTime, default=utc_now)


# =========================
# CUSTOMER
# =========================
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100), default="")
    state = db.Column(db.String(100), default="")
    postal_code = db.Column(db.String(20), default="")
    user = db.relationship("User", back_populates="customer_profile")


# =========================
# ORDER
# =========================
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    order_date = db.Column(db.Date, default=utc_today)
    status = db.Column(db.String(50))
    total_amount = db.Column(db.Float)


# =========================
# ORDER ITEMS
# =========================
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    subtotal = db.Column(db.Float)


# =========================
# PAYMENT
# =========================
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    payment_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Pending")


# =========================
# PRODUCT
# =========================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False, default="Kulhad")
    price = db.Column(db.Float, nullable=False)
    wage_per_kulhad = db.Column(db.Float, nullable=False, default=0)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255))


class InventorySetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), unique=True, nullable=False)
    min_stock = db.Column(db.Integer, default=10, nullable=False)


class InventoryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    change = db.Column(db.Integer, nullable=False)
    previous_stock = db.Column(db.Integer, nullable=False)
    new_stock = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), default="")
    entry_type = db.Column(db.String(50), default="manual")
    actor_name = db.Column(db.String(100), default="System")
    created_at = db.Column(db.DateTime, default=utc_now)


class ProductHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=True)
    product_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), default="")
    actor_name = db.Column(db.String(100), default="System")
    created_at = db.Column(db.DateTime, default=utc_now)
