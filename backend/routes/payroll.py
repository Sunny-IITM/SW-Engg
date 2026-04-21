from calendar import monthrange
from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from middleware.role_required import role_required
from models import Employee, PayrollRecord, ProductionEntry, User

payroll = Blueprint("payroll", __name__)


PAYROLL_STATUS_OPTIONS = {"pending", "processed", "paid"}


def normalize_status(value, fallback="pending"):
    status = (value or fallback).strip().lower()
    return status if status in PAYROLL_STATUS_OPTIONS else fallback


def validate_month_year(payroll_month, payroll_year):
    if payroll_month < 1 or payroll_month > 12:
        return jsonify({"error": "month must be between 1 and 12"}), 400
    if payroll_year < 1:
        return jsonify({"error": "year must be a positive integer"}), 400
    return None


def parse_status(value):
    status = (value or "").strip().lower()
    return status if status in PAYROLL_STATUS_OPTIONS else None


def parse_iso_date(raw_value):
    value = (raw_value or "").strip()
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_cutoff_date(payroll_month, payroll_year, requested_date=None):
    month_last_day = monthrange(payroll_year, payroll_month)[1]
    month_start = date(payroll_year, payroll_month, 1)
    month_end = date(payroll_year, payroll_month, month_last_day)
    effective_end = min(month_end, date.today())

    if requested_date is None:
        return effective_end

    if requested_date < month_start:
        return month_start

    return min(requested_date, effective_end)


def get_monthly_wage_totals(employee_id, payroll_month, payroll_year, requested_date=None):
    cutoff_date = get_cutoff_date(payroll_month, payroll_year, requested_date)
    totals = (
        db.session.query(
            db.func.coalesce(db.func.sum(ProductionEntry.total_quantity), 0),
            db.func.coalesce(db.func.sum(ProductionEntry.wage_amount), 0),
            db.func.coalesce(db.func.count(db.distinct(ProductionEntry.entry_date)), 0)
        )
        .filter(ProductionEntry.employee_id == employee_id)
        .filter(db.extract("month", ProductionEntry.entry_date) == payroll_month)
        .filter(db.extract("year", ProductionEntry.entry_date) == payroll_year)
        .filter(ProductionEntry.entry_date <= cutoff_date)
        .one()
    )
    return int(totals[0] or 0), round(float(totals[1] or 0), 2), int(totals[2] or 0), cutoff_date


def get_payroll_record(employee_id, payroll_month, payroll_year):
    return PayrollRecord.query.filter_by(
        employee_id=employee_id,
        payroll_month=payroll_month,
        payroll_year=payroll_year
    ).first()


def get_or_create_payroll_record(employee, payroll_month, payroll_year):
    record = get_payroll_record(employee.id, payroll_month, payroll_year)
    if record is None:
        record = PayrollRecord(
            employee_id=employee.id,
            payroll_month=payroll_month,
            payroll_year=payroll_year,
            base_salary=0,
            bonus=0,
            deductions=0,
            working_days=0,
            total_days=0,
            status="pending"
        )
        db.session.add(record)
        db.session.flush()

    return record


def serialize_payroll(employee, user, record, requested_date=None):
    total_quantity, gross_wages, submitted_days, cutoff_date = get_monthly_wage_totals(
        employee.id,
        int(record.payroll_month),
        int(record.payroll_year),
        requested_date,
    )
    bonus = round(float(record.bonus or 0), 2)
    deductions = round(float(record.deductions or 0), 2)
    net_wages = round(gross_wages + bonus - deductions, 2)

    return {
        "id": employee.id,
        "user_id": user.id if user else None,
        "name": employee.name or (user.name if user else "Employee"),
        "role": employee.job_title or employee.role or "",
        "department": employee.department or "",
        "email": user.email if user and user.email else "",
        "total_quantity": total_quantity,
        "gross_wages": gross_wages,
        "bonus": bonus,
        "deductions": deductions,
        "net_wages": net_wages,
        "submitted_days": submitted_days,
        "status": normalize_status(record.status),
        "paid_on": record.paid_on.isoformat() if record.paid_on else "",
        "calculated_through": cutoff_date.isoformat(),
        "month": int(record.payroll_month),
        "year": int(record.payroll_year)
    }


@payroll.route("/", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_payroll():
    today = date.today()
    payroll_month = int(request.args.get("month") or today.month)
    payroll_year = int(request.args.get("year") or today.year)
    requested_date = parse_iso_date(request.args.get("as_of_date"))
    validation_error = validate_month_year(payroll_month, payroll_year)
    if validation_error:
        return validation_error

    employees = Employee.query.order_by(Employee.name.asc(), Employee.id.asc()).all()
    results = []

    for employee in employees:
        user = db.session.get(User, employee.user_id) if employee.user_id else None
        if user and not user.is_active:
            continue

        record = get_or_create_payroll_record(employee, payroll_month, payroll_year)
        results.append(serialize_payroll(employee, user, record, requested_date))

    db.session.commit()
    return jsonify(results)


@payroll.route("/me", methods=["GET"])
@jwt_required()
@role_required("employee")
def get_my_payroll():
    today = date.today()
    payroll_month = int(request.args.get("month") or today.month)
    payroll_year = int(request.args.get("year") or today.year)
    requested_date = parse_iso_date(request.args.get("as_of_date"))
    validation_error = validate_month_year(payroll_month, payroll_year)
    if validation_error:
        return validation_error

    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404

    employee = user.employee_profile
    if employee is None:
        return jsonify({"error": "Employee profile not found"}), 404

    record = get_or_create_payroll_record(employee, payroll_month, payroll_year)
    payload = serialize_payroll(employee, user, record, requested_date)
    db.session.commit()
    return jsonify(payload)


@payroll.route("/<int:employee_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_payroll_record(employee_id):
    employee = db.session.get(Employee, employee_id)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    data = request.get_json() or {}
    payroll_month = int(data.get("month") or date.today().month)
    payroll_year = int(data.get("year") or date.today().year)
    validation_error = validate_month_year(payroll_month, payroll_year)
    if validation_error:
        return validation_error
    requested_paid_on = parse_iso_date(data.get("paid_on"))
    if "paid_on" in data and requested_paid_on is None:
        return jsonify({"error": "Invalid paid_on date"}), 400

    record = get_or_create_payroll_record(employee, payroll_month, payroll_year)

    if "bonus" in data:
        record.bonus = float(data.get("bonus") or 0)
    if "deductions" in data:
        record.deductions = float(data.get("deductions") or 0)
    if "status" in data:
        parsed_status = parse_status(data.get("status"))
        if parsed_status is None:
            return jsonify({"error": "Invalid payroll status"}), 400
        record.status = parsed_status
        if record.status == "paid":
            record.paid_on = requested_paid_on or record.paid_on or date.today()
        elif record.status != "paid":
            record.paid_on = None
    elif requested_paid_on:
        record.paid_on = requested_paid_on

    if record.paid_on:
        month_start = date(payroll_year, payroll_month, 1)
        month_end = date(payroll_year, payroll_month, monthrange(payroll_year, payroll_month)[1])
        if record.paid_on < month_start or record.paid_on > month_end:
            return jsonify({"error": "paid_on must be within the selected payroll month"}), 400

    user = db.session.get(User, employee.user_id) if employee.user_id else None
    db.session.commit()
    return jsonify(serialize_payroll(employee, user, record))


@payroll.route("/bulk-status", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_bulk_payroll_status():
    data = request.get_json() or {}
    payroll_month = int(data.get("month") or date.today().month)
    payroll_year = int(data.get("year") or date.today().year)
    validation_error = validate_month_year(payroll_month, payroll_year)
    if validation_error:
        return validation_error
    next_status = parse_status(data.get("status"))
    requested_paid_on = parse_iso_date(data.get("paid_on"))

    if "paid_on" in data and requested_paid_on is None:
        return jsonify({"error": "Invalid paid_on date"}), 400

    if next_status is None:
        return jsonify({"error": "Invalid payroll status"}), 400

    if requested_paid_on:
        month_start = date(payroll_year, payroll_month, 1)
        month_end = date(payroll_year, payroll_month, monthrange(payroll_year, payroll_month)[1])
        if requested_paid_on < month_start or requested_paid_on > month_end:
            return jsonify({"error": "paid_on must be within the selected payroll month"}), 400

    allowed_current_statuses = []
    for value in (data.get("current_statuses") or []):
        parsed_status = parse_status(value)
        if parsed_status is None:
            return jsonify({"error": "Invalid current payroll status"}), 400
        allowed_current_statuses.append(parsed_status)
    if not allowed_current_statuses:
        return jsonify({"error": "At least one current status is required"}), 400

    updated = []
    employees = Employee.query.order_by(Employee.id.asc()).all()
    for employee in employees:
        user = db.session.get(User, employee.user_id) if employee.user_id else None
        if user and not user.is_active:
            continue

        record = get_or_create_payroll_record(employee, payroll_month, payroll_year)
        if normalize_status(record.status) not in allowed_current_statuses:
            continue

        record.status = next_status
        record.paid_on = requested_paid_on if next_status == "paid" else None
        updated.append({
            "id": employee.id,
            "status": next_status,
            "paid_on": record.paid_on.isoformat() if record.paid_on else ""
        })

    db.session.commit()
    return jsonify({
        "message": f"Updated {len(updated)} payroll record(s)",
        "records": updated
    })
