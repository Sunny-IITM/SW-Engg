from calendar import monthrange
from datetime import UTC, date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from middleware.role_required import role_required
from models import Employee, ProductionEntry, Product, User

production = Blueprint("production", __name__)


ENTRY_STATUS_OPTIONS = {"all", "present", "leave"}
ENTRY_TYPE_OPTIONS = {"regular", "overtime", "manual", "image", "leave"}


def utc_now():
    return datetime.now(timezone.utc)


def validate_month_year(month, year):
    if month < 1 or month > 12:
        return jsonify({"error": "month must be between 1 and 12"}), 400
    if year < 1:
        return jsonify({"error": "year must be a positive integer"}), 400
    return None


def get_employee_for_current_user():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return None, None, (jsonify({"error": "User not found"}), 404)

    if user.role != "employee":
        return None, None, (jsonify({"error": "Only employees can access production entries"}), 403)

    employee = user.employee_profile
    if employee is None:
        employee = Employee(user_id=user.id, name=user.name or "")
        db.session.add(employee)
        db.session.flush()

    return user, employee, None


def get_product_for_entry(data):
    product_id = data.get("product_id")
    product_name = (data.get("product") or "").strip()

    product = None
    if product_id:
        product = db.session.get(Product, int(product_id))
    elif product_name:
        product = Product.query.filter(db.func.lower(Product.name) == product_name.lower()).first()

    return product


def serialize_entry(entry):
    return {
        "id": entry.id,
        "product_id": entry.product_id,
        "product_name": entry.product_name or "",
        "date": entry.entry_date.strftime("%Y-%m-%d") if entry.entry_date else "",
        "status": (entry.status or "present").title(),
        "type": (entry.entry_type or "regular").title(),
        "kulhad_quantity": int(entry.kulhad_quantity or 0),
        "cup_quantity": int(entry.cup_quantity or 0),
        "total_quantity": int(entry.total_quantity or 0),
        "wage_per_kulhad": round(float(entry.wage_per_kulhad or 0), 2),
        "daily_wage": round(float(entry.wage_amount or 0), 2),
        "notes": entry.notes or "",
        "created_at": entry.created_at.strftime("%Y-%m-%d %I:%M %p") if entry.created_at else ""
    }


def build_attendance_rows(employee_id, month, year):
    today = date.today()
    month_start = date(year, month, 1)
    if month_start > today.replace(day=1):
        return []

    last_day = monthrange(year, month)[1]
    end_day = last_day
    if month == today.month and year == today.year:
        end_day = today.day

    stored_entries = (
        ProductionEntry.query
        .filter_by(employee_id=employee_id)
        .filter(db.extract("month", ProductionEntry.entry_date) == month)
        .filter(db.extract("year", ProductionEntry.entry_date) == year)
        .order_by(ProductionEntry.entry_date.desc(), ProductionEntry.created_at.desc(), ProductionEntry.id.desc())
        .all()
    )

    rows = [serialize_entry(entry) for entry in stored_entries]
    existing_dates = {entry.entry_date for entry in stored_entries}

    synthetic_id = -1
    for day_number in range(end_day, 0, -1):
        entry_date = date(year, month, day_number)
        if entry_date in existing_dates:
            continue

        rows.append({
            "id": synthetic_id,
            "product_id": None,
            "product_name": "",
            "date": entry_date.strftime("%Y-%m-%d"),
            "status": "Leave",
            "type": "Leave",
            "kulhad_quantity": 0,
            "cup_quantity": 0,
            "total_quantity": 0,
            "wage_per_kulhad": 0,
            "daily_wage": 0,
            "notes": "",
            "created_at": ""
        })
        synthetic_id -= 1

    rows.sort(key=lambda item: (item["date"], item["created_at"], item["id"]), reverse=True)
    return rows


@production.route("/entries", methods=["GET"])
@jwt_required()
@role_required("employee")
def get_production_entries():
    _, employee, error_response = get_employee_for_current_user()
    if error_response:
        return error_response

    month = int(request.args.get("month") or utc_now().month)
    year = int(request.args.get("year") or utc_now().year)
    validation_error = validate_month_year(month, year)
    if validation_error:
        return validation_error

    return jsonify(build_attendance_rows(employee.id, month, year))


@production.route("/log", methods=["POST"])
@jwt_required()
@role_required("employee")
def log_production():
    _, employee, error_response = get_employee_for_current_user()
    if error_response:
        return error_response

    data = request.get_json() or {}
    raw_date = (data.get("date") or "").strip()
    try:
        entry_date = datetime.strptime(raw_date, "%Y-%m-%d").date() if raw_date else utc_now().date()
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    if entry_date > date.today():
        return jsonify({"error": "Future dates are not allowed for production entries"}), 400

    quantity = max(0, int(data.get("quantity") or data.get("kulhad_quantity") or 0))
    if quantity <= 0 and (data.get("status") or "present").strip().lower() != "leave":
        return jsonify({"error": "Quantity must be greater than zero"}), 400

    method = (data.get("method") or "manual").strip().lower()
    entry_type = (data.get("entry_type") or method or "regular").strip().lower()
    if entry_type not in ENTRY_TYPE_OPTIONS:
        entry_type = "regular"

    status = (data.get("status") or "present").strip().lower()
    if status not in ENTRY_STATUS_OPTIONS:
        status = "present"

    product = get_product_for_entry(data)
    if status != "leave" and product is None:
        return jsonify({"error": "Valid product is required"}), 400

    wage_per_kulhad = float(product.wage_per_kulhad or 0) if product else 0
    product_name = product.name if product else ""
    category = (product.category or "Kulhad").strip().lower() if product else "kulhad"
    kulhad_quantity = quantity if status != "leave" and "cup" not in category else 0
    cup_quantity = quantity if status != "leave" and "cup" in category else 0
    total_quantity = 0 if status == "leave" else quantity
    wage_amount = 0 if status == "leave" else round(quantity * wage_per_kulhad, 2)

    entry = ProductionEntry(
        employee_id=employee.id,
        product_id=product.id if product else None,
        product_name=product_name,
        entry_date=entry_date,
        status=status,
        entry_type="leave" if status == "leave" else entry_type,
        kulhad_quantity=kulhad_quantity,
        cup_quantity=cup_quantity,
        total_quantity=total_quantity,
        wage_per_kulhad=wage_per_kulhad,
        wage_amount=wage_amount,
        notes=(data.get("notes") or "").strip()
    )
    db.session.add(entry)

    db.session.commit()
    return jsonify(serialize_entry(entry)), 201
