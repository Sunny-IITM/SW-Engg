
from datetime import UTC, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from middleware.role_required import role_required
from models import Customer, Order, OrderItem, Payment, Product, User

orders = Blueprint("orders", __name__)


ORDER_STATUS_OPTIONS = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
CHECKOUT_PAYMENT_METHODS = {"Cash on Delivery", "UPI", "Credit / Debit Card"}
PAYMENT_STATUS_OPTIONS = {"pending", "paid", "failed", "refunded"}


def utc_now():
    return datetime.now(UTC)


def title_case(value, fallback=""):
    return (value or fallback).strip().title()


def get_or_create_customer_profile(user):
    customer = user.customer_profile
    if customer is None:
        customer = Customer(
            user_id=user.id,
            name=user.name or "",
            phone_number="",
            address="",
            city="",
            state="",
            postal_code=""
        )
        db.session.add(customer)
        db.session.flush()

    return customer


def serialize_checkout_profile(user, customer):
    return {
        "name": user.name or "",
        "email": user.email or "",
        "phone": customer.phone_number or "",
        "address": customer.address or "",
        "city": customer.city or "",
        "state": customer.state or "",
        "postal_code": customer.postal_code or "",
        "has_saved_address": bool(
            (customer.address or "").strip() or
            (customer.city or "").strip() or
            (customer.state or "").strip() or
            (customer.postal_code or "").strip()
        )
    }


def normalize_payment_method(value):
    payment_method = (value or "").strip()
    return payment_method if payment_method in CHECKOUT_PAYMENT_METHODS else "Cash on Delivery"


def normalize_payment_status(value, fallback="Pending"):
    normalized = (value or fallback).strip().lower()
    if normalized not in PAYMENT_STATUS_OPTIONS:
        normalized = fallback.strip().lower()
    return title_case(normalized, fallback)


def parse_payment_status(value):
    normalized = (value or "").strip().lower()
    if normalized not in PAYMENT_STATUS_OPTIONS:
        return None
    return title_case(normalized)


def serialize_order_record(order, customer, user, payment, items):
    payment_method = payment.payment_method if payment and payment.payment_method else "Unspecified"
    payment_status = normalize_payment_status(
        payment.status if payment and payment.status else (
            "Pending" if payment_method == "Cash on Delivery" else ("Paid" if payment else "Pending")
        )
    )

    return {
        "id": order.id,
        "order_number": f"ORD-{order.id:04d}",
        "status": title_case(order.status, "Pending"),
        "payment": payment_status,
        "name": customer.name if customer and customer.name else "Customer",
        "email": user.email if user and user.email else "",
        "phone": customer.phone_number if customer and customer.phone_number else "",
        "address": customer.address if customer and customer.address else "",
        "method": payment_method,
        "amount": round(float(order.total_amount or 0), 2),
        "date": order.order_date.strftime("%Y-%m-%d") if order.order_date else "",
        "items": items,
        "item_count": sum(item["quantity"] for item in items)
    }


@orders.route("/checkout-profile", methods=["GET"])
@jwt_required()
def get_checkout_profile():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role != "customer":
        return jsonify({"error": "Checkout profile is only available for customers"}), 403

    customer = get_or_create_customer_profile(user)
    db.session.commit()
    return jsonify(serialize_checkout_profile(user, customer))


@orders.route("/checkout-profile", methods=["PUT"])
@jwt_required()
def update_checkout_profile():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role != "customer":
        return jsonify({"error": "Checkout profile is only available for customers"}), 403

    data = request.get_json() or {}
    customer = get_or_create_customer_profile(user)

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

    customer.name = user.name or customer.name or ""

    db.session.commit()
    return jsonify(serialize_checkout_profile(user, customer))


@orders.route("/", methods=["POST"])
@jwt_required()
def create_order():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role != "customer":
        return jsonify({"error": "Only customer accounts can place orders"}), 403

    data = request.get_json() or {}
    items = data.get("items") or []

    # Validate shipping cost if provided
    shipping = data.get("shipping")
    if shipping is not None and shipping < 0:
        return jsonify({"error": "Shipping cost cannot be negative"}), 400

    if not items:
        return jsonify({"error": "At least one item is required"}), 400

    customer = get_or_create_customer_profile(user)
    customer.name = user.name or customer.name or ""
    customer.phone_number = (data.get("phone") or customer.phone_number or "").strip()
    customer.address = (data.get("address") or customer.address or "").strip()
    customer.city = (data.get("city") or customer.city or "").strip()
    customer.state = (data.get("state") or customer.state or "").strip()
    customer.postal_code = (data.get("postal_code") or customer.postal_code or "").strip()

    if not customer.phone_number or not customer.address or not customer.city or not customer.state or not customer.postal_code:
        return jsonify({"error": "Complete delivery address is required"}), 400

    order = Order(
        customer_id=customer.id,
        order_date=utc_now(),
        status="pending",
        total_amount=0
    )

    db.session.add(order)
    db.session.flush()

    total_amount = 0.0
    created_items = []

    for raw_item in items:
        product_id = raw_item.get("id")
        quantity = int(raw_item.get("qty") or 0)

        if not product_id or quantity <= 0:
            db.session.rollback()
            return jsonify({"error": "Each order item must include a valid id and quantity"}), 400

        product = db.session.get(Product, product_id)
        if not product:
            db.session.rollback()
            return jsonify({"error": "One or more products could not be found"}), 404

        available_stock = int(product.stock or 0)
        if quantity > available_stock:
            db.session.rollback()
            return jsonify({"error": f"Only {available_stock} item(s) available for {product.name}"}), 400

        subtotal = round(float(product.price or 0) * quantity, 2)
        product.stock = available_stock - quantity
        total_amount += subtotal

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            subtotal=subtotal
        )
        db.session.add(order_item)

        created_items.append({
            "name": product.name,
            "quantity": quantity,
            "subtotal": subtotal
        })

    # Calculate shipping based on subtotal (backend-determined, not client-controlled)
    # Free shipping if subtotal >= 500, otherwise 50
    shipping_amount = 0 if total_amount >= 500 else 50

    order.total_amount = round(total_amount + shipping_amount, 2)

    payment_method = normalize_payment_method(data.get("payment_method"))
    payment = Payment(
        order_id=order.id,
        payment_date=utc_now(),
        amount=order.total_amount,
        payment_method=payment_method,
        status="Pending" if payment_method == "Cash on Delivery" else "Paid"
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({
        "message": "Order placed successfully",
        "id": order.id,
        "order_number": f"ORD-{order.id:04d}",
        "status": title_case(order.status),
        "payment": "Pending" if payment_method == "Cash on Delivery" else "Paid",
        "method": payment_method,
        "amount": round(float(order.total_amount or 0), 2),
        "items": created_items
    }), 201


@orders.route("/admin", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_admin_orders():
    customer_lookup = {customer.id: customer for customer in Customer.query.all()}
    payments_by_order = {}
    for payment in Payment.query.order_by(Payment.id.desc()).all():
        payments_by_order.setdefault(payment.order_id, payment)

    order_items = (
        db.session.query(OrderItem.order_id, OrderItem.quantity, OrderItem.subtotal, Product.name)
        .outerjoin(Product, Product.id == OrderItem.product_id)
        .all()
    )

    items_by_order = {}
    for order_id, quantity, subtotal, product_name in order_items:
        items_by_order.setdefault(order_id, []).append({
            "name": product_name or "Product",
            "quantity": int(quantity or 0),
            "subtotal": round(float(subtotal or 0), 2)
        })

    output = []
    orders_list = Order.query.order_by(Order.id.desc()).all()
    for order in orders_list:
        customer = customer_lookup.get(order.customer_id)
        user = db.session.get(User, customer.user_id) if customer and customer.user_id else None
        payment = payments_by_order.get(order.id)
        items = items_by_order.get(order.id, [])
        output.append(serialize_order_record(order, customer, user, payment, items))

    return jsonify(output)


@orders.route("/my-history", methods=["GET"])
@jwt_required()
def get_customer_order_history():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role != "customer":
        return jsonify({"error": "Order history is only available for customers"}), 403

    customer = get_or_create_customer_profile(user)
    payments_by_order = {}
    for payment in Payment.query.order_by(Payment.id.desc()).all():
        payments_by_order.setdefault(payment.order_id, payment)

    order_items = (
        db.session.query(
            OrderItem.order_id,
            OrderItem.product_id,
            OrderItem.quantity,
            OrderItem.subtotal,
            Product.name,
            Product.price,
            Product.stock,
            Product.image
        )
        .outerjoin(Product, Product.id == OrderItem.product_id)
        .filter(OrderItem.order_id.in_(
            db.session.query(Order.id).filter(Order.customer_id == customer.id)
        ))
        .all()
    )

    items_by_order = {}
    for order_id, product_id, quantity, subtotal, product_name, price, stock, image in order_items:
        items_by_order.setdefault(order_id, []).append({
            "id": product_id,
            "name": product_name or "Product",
            "quantity": int(quantity or 0),
            "subtotal": round(float(subtotal or 0), 2),
            "price": round(float(price or 0), 2),
            "stock": int(stock or 0),
            "image": image or ""
        })

    output = []
    orders_list = Order.query.filter_by(customer_id=customer.id).order_by(Order.id.desc()).all()
    for order in orders_list:
        payment = payments_by_order.get(order.id)
        items = items_by_order.get(order.id, [])
        output.append(serialize_order_record(order, customer, user, payment, items))

    return jsonify(output)


@orders.route("/<int:order_id>/status", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_admin_order_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    data = request.get_json() or {}
    status = (data.get("status") or "").strip().lower()
    if status not in ORDER_STATUS_OPTIONS:
        return jsonify({"error": "Invalid order status"}), 400

    payment = Payment.query.filter_by(order_id=order.id).order_by(Payment.id.desc()).first()
    existing_payment_status = (
        payment.status if payment and payment.status else (
            "Pending" if payment and payment.payment_method == "Cash on Delivery" else "Paid"
        )
    )
    payment_status = title_case(existing_payment_status, "Pending")
    if "payment" in data:
        payment_status = parse_payment_status(data.get("payment"))
        if payment_status is None:
            return jsonify({"error": "Invalid payment status"}), 400

    order.status = status
    if payment is None:
        payment = Payment(
            order_id=order.id,
            payment_date=utc_now(),
            amount=order.total_amount or 0,
            payment_method="Cash on Delivery",
            status=payment_status
        )
        db.session.add(payment)
    else:
        payment.status = payment_status
    db.session.commit()
    return jsonify({
        "message": "Order updated",
        "id": order.id,
        "status": title_case(order.status),
        "payment": payment_status
    })


@orders.route("/bulk-payment-status", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_bulk_payment_status():
    data = request.get_json() or {}
    raw_order_ids = data.get("order_ids") or []
    order_ids = []

    for raw_order_id in raw_order_ids:
        try:
            order_ids.append(int(raw_order_id))
        except (TypeError, ValueError):
            continue

    if not order_ids:
        return jsonify({"error": "Select at least one order"}), 400

    payment_status = parse_payment_status(data.get("payment"))
    if payment_status is None:
        return jsonify({"error": "Invalid payment status"}), 400

    updated_orders = []
    orders_list = Order.query.filter(Order.id.in_(order_ids)).all()
    for order in orders_list:
        payment = Payment.query.filter_by(order_id=order.id).order_by(Payment.id.desc()).first()
        if payment is None:
            payment = Payment(
                order_id=order.id,
                payment_date=utc_now(),
                amount=order.total_amount or 0,
                payment_method="Cash on Delivery",
                status=payment_status
            )
            db.session.add(payment)
        else:
            payment.status = payment_status

        updated_orders.append({
            "id": order.id,
            "payment": payment_status
        })

    db.session.commit()
    return jsonify({
        "message": f"Updated payment status for {len(updated_orders)} order(s)",
        "orders": updated_orders
    })
