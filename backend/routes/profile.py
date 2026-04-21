from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import bcrypt, db
from models import Customer, Employee, User

profile = Blueprint("profile", __name__)


def serialize_customer_profile(user, customer):
    return {
        "name": user.name or "",
        "email": user.email or "",
        "role": user.role or "customer",
        "phone": customer.phone_number or "",
        "address": customer.address or "",
        "city": customer.city or "",
        "state": customer.state or "",
        "postal_code": customer.postal_code or ""
    }


def serialize_employee_profile(user, employee):
    per_unit_wage = float(employee.daily_wage or 0)
    return {
        "name": user.name or "",
        "email": user.email or "",
        "role": user.role or "employee",
        "phone": employee.phone or "",
        "address": employee.address or "",
        "department": employee.department or "",
        "job_title": employee.job_title or employee.role or "",
        "per_unit_wage": per_unit_wage,
        "salary": per_unit_wage
    }


@profile.route("/me", methods=["GET"])
@jwt_required()
def get_my_profile():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role == "customer":
        customer = user.customer_profile
        if customer is None:
            customer = Customer(user_id=user.id, name=user.name or "")
            db.session.add(customer)
            db.session.commit()
        return jsonify(serialize_customer_profile(user, customer))

    if user.role == "employee":
        employee = user.employee_profile
        if employee is None:
            employee = Employee(user_id=user.id, name=user.name or "")
            db.session.add(employee)
            db.session.commit()
        return jsonify(serialize_employee_profile(user, employee))

    return jsonify({
        "name": user.name or "",
        "email": user.email or "",
        "role": user.role or ""
    })


@profile.route("/me", methods=["PUT"])
@jwt_required()
def update_my_profile():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if "name" in data:
        user.name = (data.get("name") or "").strip()
    if "email" in data and (data.get("email") or "").strip().lower() != (user.email or "").strip().lower():
        return jsonify({"error": "Email address cannot be changed from the profile page"}), 400

    if current_password or new_password:
        if not current_password or not new_password:
            return jsonify({"error": "Current password and new password are required"}), 400
        if not bcrypt.check_password_hash(user.password, current_password):
            return jsonify({"error": "Current password is incorrect"}), 400
        if len(new_password) < 6:
            return jsonify({"error": "New password must be at least 6 characters long"}), 400
        user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")

    if user.role == "customer":
        customer = user.customer_profile
        if customer is None:
            customer = Customer(user_id=user.id)
            db.session.add(customer)

        customer.name = user.name or customer.name or ""
        if "phone" in data:
            customer.phone_number = (data.get("phone") or "").strip()
        if "address" in data:
            customer.address = (data.get("address") or "").strip()
        if "city" in data:
            customer.city = (data.get("city") or "").strip()
        if "state" in data:
            customer.state = (data.get("state") or "").strip()
        if "postal_code" in data:
            customer.postal_code = (data.get("postal_code") or "").strip()

        db.session.commit()
        return jsonify(serialize_customer_profile(user, customer))

    if user.role == "employee":
        employee = user.employee_profile
        if employee is None:
            employee = Employee(user_id=user.id)
            db.session.add(employee)

        employee.name = user.name or employee.name or ""
        if "phone" in data:
            employee.phone = (data.get("phone") or "").strip()
        if "address" in data:
            employee.address = (data.get("address") or "").strip()

        db.session.commit()
        return jsonify(serialize_employee_profile(user, employee))

    db.session.commit()
    return jsonify({
        "name": user.name or "",
        "email": user.email or "",
        "role": user.role or ""
    })
