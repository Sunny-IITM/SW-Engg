from flask import Blueprint, request, jsonify
from extensions import db, bcrypt
from flask_jwt_extended import create_access_token
from models import Customer, User

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "customer").strip().lower()

    if not name or not email or not password:
        return jsonify({"message": "Name, email, and password are required"}), 400

    if role != "customer":
        return jsonify({"message": "Registration is only available for customer accounts"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(
        password
    ).decode("utf-8")

    user = User(
        name=name,
        email=email,
        password=hashed_password,
        role=role
    )

    db.session.add(user)
    db.session.flush()

    if role == "customer":
        db.session.add(Customer(
            user_id=user.id,
            name=user.name,
            phone_number=(data.get("phone") or "").strip(),
            address=(data.get("address") or "").strip()
        ))

    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"message": "This account has been disabled"}), 403

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    customer_profile = user.customer_profile
    employee_profile = user.employee_profile

    payload = {
        "token": token,
        "name": user.name,
        "role": user.role,
        "email": user.email
    }

    if user.role == "customer":
        payload.update({
            "phone": customer_profile.phone_number if customer_profile and customer_profile.phone_number else "",
            "address": customer_profile.address if customer_profile and customer_profile.address else "",
            "city": customer_profile.city if customer_profile and customer_profile.city else "",
            "state": customer_profile.state if customer_profile and customer_profile.state else "",
            "postal_code": customer_profile.postal_code if customer_profile and customer_profile.postal_code else ""
        })
    elif user.role == "employee":
        payload.update({
            "phone": employee_profile.phone if employee_profile and employee_profile.phone else "",
            "address": employee_profile.address if employee_profile and employee_profile.address else "",
            "department": employee_profile.department if employee_profile and employee_profile.department else "",
            "job_title": employee_profile.job_title if employee_profile and employee_profile.job_title else (employee_profile.role if employee_profile and employee_profile.role else "")
        })

    return jsonify(payload), 200
