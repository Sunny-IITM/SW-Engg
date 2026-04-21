from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import bcrypt, db
from middleware.role_required import role_required
from models import Customer, Employee, User

admin_users = Blueprint("admin_users", __name__)


def get_customer_profile(user):
    profile = user.customer_profile
    if profile is None:
        profile = Customer(user_id=user.id, name=user.name or "")
        db.session.add(profile)
        db.session.flush()
    return profile


def get_employee_profile(user):
    profile = user.employee_profile
    if profile is None:
        profile = Employee(user_id=user.id, name=user.name or "")
        db.session.add(profile)
        db.session.flush()
    return profile


def serialize_user(user):
    customer_profile = user.customer_profile
    employee_profile = user.employee_profile
    per_unit_wage = float(employee_profile.daily_wage or 0) if employee_profile else 0

    payload = {
        "id": user.id,
        "name": user.name or "",
        "email": user.email or "",
        "role": user.role or "customer",
        "is_active": bool(user.is_active),
        "created_at": user.created_at.strftime("%d/%m/%Y") if user.created_at else ""
    }

    if user.role == "customer":
        payload.update({
            "phone": customer_profile.phone_number if customer_profile and customer_profile.phone_number else "",
            "address": customer_profile.address if customer_profile and customer_profile.address else "",
            "department": "",
            "job_title": ""
        })
    elif user.role == "employee":
        payload.update({
            "phone": employee_profile.phone if employee_profile and employee_profile.phone else "",
            "address": employee_profile.address if employee_profile and employee_profile.address else "",
            "department": employee_profile.department if employee_profile and employee_profile.department else "",
            "job_title": employee_profile.job_title if employee_profile and employee_profile.job_title else (employee_profile.role if employee_profile and employee_profile.role else ""),
            "per_unit_wage": per_unit_wage,
            "daily_wage": per_unit_wage
        })
    else:
        payload.update({
            "phone": "",
            "address": "",
            "department": "",
            "job_title": ""
        })

    return payload


@admin_users.route('/users', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_users():
    role = (request.args.get('role') or '').strip().lower()
    query = User.query

    if role:
        query = query.filter_by(role=role)

    users = query.order_by(User.created_at.desc(), User.id.desc()).all()
    return jsonify([serialize_user(user) for user in users])


@admin_users.route('/users', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_user():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = (data.get('role') or '').strip().lower()

    if role not in {'customer', 'employee'}:
        return jsonify({'error': 'role must be customer or employee'}), 400

    if not name or not email or not password:
        return jsonify({'error': 'name, email, and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(
        name=name,
        email=email,
        password=bcrypt.generate_password_hash(password).decode('utf-8'),
        role=role,
        is_active=bool(data.get('is_active', True))
    )

    db.session.add(user)
    db.session.flush()

    if role == 'customer':
        profile = get_customer_profile(user)
        profile.name = name
        profile.phone_number = (data.get('phone') or '').strip()
        profile.address = (data.get('address') or '').strip()
    else:
        profile = get_employee_profile(user)
        profile.name = name
        profile.phone = (data.get('phone') or '').strip()
        profile.address = (data.get('address') or '').strip()
        profile.department = (data.get('department') or '').strip()
        profile.job_title = (data.get('job_title') or '').strip()
        profile.role = profile.job_title
        profile.daily_wage = float(data.get('per_unit_wage', data.get('daily_wage')) or 0)

    db.session.commit()
    return jsonify(serialize_user(user)), 201


@admin_users.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}

    if 'name' in data:
        user.name = (data.get('name') or '').strip()
    if 'email' in data:
        email = (data.get('email') or '').strip().lower()
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            return jsonify({'error': 'Email already exists'}), 400
        user.email = email
    if 'is_active' in data:
        user.is_active = bool(data.get('is_active'))
    if data.get('password'):
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    if user.role == 'customer':
        profile = get_customer_profile(user)
        profile.name = user.name or ''
        if 'phone' in data:
            profile.phone_number = (data.get('phone') or '').strip()
        if 'address' in data:
            profile.address = (data.get('address') or '').strip()
    elif user.role == 'employee':
        profile = get_employee_profile(user)
        profile.name = user.name or ''
        if 'phone' in data:
            profile.phone = (data.get('phone') or '').strip()
        if 'address' in data:
            profile.address = (data.get('address') or '').strip()
        if 'department' in data:
            profile.department = (data.get('department') or '').strip()
        if 'job_title' in data:
            profile.job_title = (data.get('job_title') or '').strip()
            profile.role = profile.job_title
        if 'per_unit_wage' in data or 'daily_wage' in data:
            profile.daily_wage = float(data.get('per_unit_wage', data.get('daily_wage')) or 0)

    db.session.commit()
    return jsonify(serialize_user(user))


@admin_users.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    current_user_id = int(get_jwt_identity())
    if user.id == current_user_id:
        return jsonify({'error': 'You cannot delete the current admin account'}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})
