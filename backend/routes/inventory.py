from datetime import UTC, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from extensions import db
from middleware.role_required import role_required
from models import Inventory, InventoryHistory, InventorySetting, Product, RawMaterialHistory, User

inventory = Blueprint("inventory", __name__)

RAW_MATERIAL_CATEGORIES = {"Clay", "Glaze", "Paint", "Packaging", "Other"}
RAW_MATERIAL_UNITS = {
    "Kilograms (kg)": "kg",
    "Liters (liters)": "liters",
    "Pieces (pieces)": "pieces",
    "Bags (bags)": "bags"
}


def utc_today():
    return datetime.now(timezone.utc).date()


def get_setting_for_product(product_id):
    setting = InventorySetting.query.filter_by(product_id=product_id).first()

    if setting:
        return setting

    setting = InventorySetting(product_id=product_id, min_stock=10)
    db.session.add(setting)
    db.session.flush()
    return setting


def serialize_raw_material(item):
    quantity = round(float(item.quantity_available or 0), 2)
    reorder_level = round(float(item.reorder_level or 0), 2)
    cost_per_unit = round(float(item.cost_per_unit or 0), 2)
    inventory_value = round(quantity * cost_per_unit, 2)

    return {
        "id": item.id,
        "name": item.raw_material_name or "",
        "category": item.category or "Other",
        "quantity": quantity,
        "unit": item.unit or "",
        "reorder_level": reorder_level,
        "cost_per_unit": cost_per_unit,
        "supplier": item.supplier_name or "",
        "last_restocked": item.last_restocked.strftime("%Y-%m-%d") if item.last_restocked else "",
        "inventory_value": inventory_value,
        "is_low_stock": quantity < reorder_level if reorder_level > 0 else False
    }


def serialize_raw_material_history_entry(entry):
    quantity_change = round(float(entry.quantity_change or 0), 2)
    previous_quantity = round(float(entry.previous_quantity or 0), 2)
    new_quantity = round(float(entry.new_quantity or 0), 2)

    return {
        "id": entry.id,
        "name": entry.material_name,
        "desc": entry.description or "Raw inventory updated",
        "change": quantity_change,
        "from": previous_quantity,
        "to": new_quantity,
        "unit": entry.unit or "",
        "date": entry.created_at.strftime("%Y-%m-%d %I:%M %p"),
        "by": entry.actor_name or "System",
        "type": entry.action or "update",
    }


def create_raw_material_history_entry(item, action, actor_name="System", description="", quantity_change=0, previous_quantity=0, new_quantity=0):
    history_entry = RawMaterialHistory(
        inventory_id=item.id,
        material_name=item.raw_material_name or "",
        action=action,
        description=description,
        quantity_change=quantity_change,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        unit=item.unit or "",
        actor_name=actor_name or "System",
    )
    db.session.add(history_entry)
    return history_entry


def normalize_raw_material_payload(data, require_name=True):
    name = (data.get("name") or data.get("raw_material_name") or "").strip()
    category = (data.get("category") or "Other").strip().title()
    unit = (data.get("unit") or "").strip()
    supplier = (data.get("supplier") or data.get("supplier_name") or "").strip()

    if require_name and not name:
        return None, (jsonify({"error": "Material name is required"}), 400)

    if category not in RAW_MATERIAL_CATEGORIES:
        category = "Other"

    if not unit:
        return None, (jsonify({"error": "Unit is required"}), 400)

    quantity = float(data.get("quantity") or data.get("initial_quantity") or 0)
    reorder_level = float(data.get("reorder_level") or 0)
    cost_per_unit = float(data.get("cost_per_unit") or 0)

    if quantity < 0 or reorder_level < 0 or cost_per_unit < 0:
        return None, (jsonify({"error": "Quantity, reminder level, and cost cannot be negative"}), 400)

    payload = {
        "name": name,
        "category": category,
        "unit": unit,
        "supplier": supplier,
        "quantity": quantity,
        "reorder_level": reorder_level,
        "cost_per_unit": cost_per_unit
    }
    return payload, None


@inventory.route("/", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_inventory():
    products = Product.query.order_by(Product.name.asc()).all()
    output = []

    for product in products:
        setting = get_setting_for_product(product.id)
        output.append({
            "id": product.id,
            "name": product.name,
            "category": product.category or "Kulhad",
            "stock": int(product.stock or 0),
            "min_stock": int(setting.min_stock or 10),
            "price": product.price
        })

    db.session.commit()
    return jsonify(output)


@inventory.route("/history", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_inventory_history():
    history_entries = (
        db.session.query(InventoryHistory, Product.name)
        .join(Product, Product.id == InventoryHistory.product_id)
        .order_by(InventoryHistory.created_at.desc())
        .limit(100)
        .all()
    )

    output = []
    for entry, product_name in history_entries:
        output.append({
            "id": entry.id,
            "name": product_name,
            "desc": entry.reason or "Manual stock adjustment",
            "change": entry.change,
            "from": entry.previous_stock,
            "to": entry.new_stock,
            "date": entry.created_at.strftime("%Y-%m-%d %I:%M %p"),
            "by": entry.actor_name or "System",
            "type": entry.entry_type or "manual"
        })

    return jsonify(output)


@inventory.route("/adjust", methods=["POST"])
@jwt_required()
@role_required("admin")
def adjust_inventory():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    product_id = data.get("product_id")
    adjustment_type = data.get("type")
    reason = (data.get("reason") or "").strip()
    raw_min_stock = data.get("min_stock")

    try:
        quantity = int(data.get("quantity") or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "quantity must be an integer"}), 400

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    if adjustment_type not in {"add", "remove"}:
        return jsonify({"error": "type must be add or remove"}), 400

    if quantity < 0:
        return jsonify({"error": "quantity cannot be negative"}), 400

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    previous_stock = int(product.stock or 0)

    if adjustment_type == "remove" and quantity > 0 and previous_stock <= 0:
        return jsonify({"error": "Stock is empty. Cannot remove stock."}), 400

    if adjustment_type == "remove" and quantity > previous_stock:
        return jsonify({"error": f"Only {previous_stock} item(s) available in stock."}), 400

    signed_change = quantity if adjustment_type == "add" else -quantity
    next_stock = max(0, previous_stock + signed_change)
    actual_change = next_stock - previous_stock

    setting = get_setting_for_product(product.id)
    previous_min_stock = int(setting.min_stock or 0)
    min_stock = previous_min_stock

    if raw_min_stock is not None:
        try:
            min_stock = int(raw_min_stock)
        except (TypeError, ValueError):
            return jsonify({"error": "min_stock must be an integer"}), 400
        if min_stock < 0:
            return jsonify({"error": "min_stock cannot be negative"}), 400

    if quantity <= 0 and min_stock == previous_min_stock:
        return jsonify({"error": "Update quantity or minimum stock to save changes"}), 400

    product.stock = next_stock
    setting.min_stock = min_stock

    user = db.session.get(User, int(get_jwt_identity()))
    actor_name = user.name if user else "Admin"

    threshold_only_update = actual_change == 0 and min_stock != previous_min_stock

    history_entry = InventoryHistory(
        product_id=product.id,
        change=actual_change,
        previous_stock=previous_stock,
        new_stock=next_stock,
        reason=reason or (
            "Minimum stock threshold updated"
            if threshold_only_update
            else "Manual stock adjustment"
        ),
        entry_type="threshold-update" if threshold_only_update else "manual",
        actor_name=actor_name
    )

    db.session.add(history_entry)
    db.session.commit()

    return jsonify({
        "message": "Inventory updated",
        "product": {
            "id": product.id,
            "name": product.name,
            "category": product.category or "Kulhad",
            "stock": product.stock,
            "min_stock": setting.min_stock,
            "price": product.price
        }
    })


@inventory.route("/raw", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_raw_inventory():
    items = (
        Inventory.query
        .filter(Inventory.raw_material_name.isnot(None))
        .order_by(Inventory.raw_material_name.asc(), Inventory.id.asc())
        .all()
    )

    output = [serialize_raw_material(item) for item in items]
    return jsonify(output)


@inventory.route("/raw/history", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_raw_inventory_history():
    history_entries = (
        RawMaterialHistory.query
        .order_by(RawMaterialHistory.created_at.desc())
        .limit(100)
        .all()
    )

    return jsonify([serialize_raw_material_history_entry(entry) for entry in history_entries])


@inventory.route("/raw", methods=["POST"])
@jwt_required()
@role_required("admin")
def create_raw_material():
    data = request.get_json() or {}
    payload, error_response = normalize_raw_material_payload(data)
    if error_response:
        return error_response

    existing = Inventory.query.filter(
        db.func.lower(Inventory.raw_material_name) == payload["name"].lower()
    ).first()
    if existing:
        return jsonify({"error": "A raw material with this name already exists"}), 400

    user = db.session.get(User, int(get_jwt_identity()))
    actor_name = user.name if user else "Admin"

    item = Inventory(
        raw_material_name=payload["name"],
        category=payload["category"],
        unit=payload["unit"],
        supplier_name=payload["supplier"],
        quantity_available=payload["quantity"],
        reorder_level=payload["reorder_level"],
        cost_per_unit=payload["cost_per_unit"],
        last_restocked=utc_today() if payload["quantity"] > 0 else None
    )
    db.session.add(item)
    db.session.flush()
    create_raw_material_history_entry(
        item,
        action="create",
        actor_name=actor_name,
        description=f"Created raw material {item.raw_material_name}",
        quantity_change=payload["quantity"],
        previous_quantity=0,
        new_quantity=payload["quantity"],
    )
    db.session.commit()
    return jsonify(serialize_raw_material(item)), 201


@inventory.route("/raw/<int:item_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_raw_material(item_id):
    item = db.session.get(Inventory, item_id)
    if not item:
        return jsonify({"error": "Raw material not found"}), 404

    data = request.get_json() or {}
    payload, error_response = normalize_raw_material_payload(data)
    if error_response:
        return error_response

    existing = Inventory.query.filter(
        db.func.lower(Inventory.raw_material_name) == payload["name"].lower(),
        Inventory.id != item.id
    ).first()
    if existing:
        return jsonify({"error": "A raw material with this name already exists"}), 400

    user = db.session.get(User, int(get_jwt_identity()))
    actor_name = user.name if user else "Admin"

    previous_name = item.raw_material_name or ""
    previous_category = item.category or "Other"
    previous_supplier = item.supplier_name or ""
    previous_reorder_level = float(item.reorder_level or 0)
    previous_cost_per_unit = float(item.cost_per_unit or 0)
    previous_unit = item.unit or ""

    item.raw_material_name = payload["name"]
    item.category = payload["category"]
    item.unit = payload["unit"]
    item.supplier_name = payload["supplier"]
    item.reorder_level = payload["reorder_level"]
    item.cost_per_unit = payload["cost_per_unit"]

    changes = []
    if previous_name != item.raw_material_name:
        changes.append(f"name {previous_name} -> {item.raw_material_name}")
    if previous_category != item.category:
        changes.append(f"category {previous_category} -> {item.category}")
    if previous_unit != item.unit:
        changes.append(f"unit {previous_unit} -> {item.unit}")
    if previous_supplier != item.supplier_name:
        changes.append(f"supplier {previous_supplier or 'Not set'} -> {item.supplier_name or 'Not set'}")
    if previous_reorder_level != float(item.reorder_level or 0):
        changes.append(f"reorder level {previous_reorder_level:g} -> {float(item.reorder_level or 0):g}")
    if previous_cost_per_unit != float(item.cost_per_unit or 0):
        changes.append(f"cost/unit {previous_cost_per_unit:g} -> {float(item.cost_per_unit or 0):g}")

    create_raw_material_history_entry(
        item,
        action="update",
        actor_name=actor_name,
        description="Updated raw material details" + (f": {', '.join(changes)}" if changes else ""),
        quantity_change=0,
        previous_quantity=float(item.quantity_available or 0),
        new_quantity=float(item.quantity_available or 0),
    )
    db.session.commit()
    return jsonify(serialize_raw_material(item))


@inventory.route("/raw/<int:item_id>/adjust", methods=["PUT"])
@jwt_required()
@role_required("admin")
def adjust_raw_material_stock(item_id):
    item = db.session.get(Inventory, item_id)
    if not item:
        return jsonify({"error": "Raw material not found"}), 404

    data = request.get_json() or {}
    adjustment = float(data.get("adjustment") or 0)
    reason = (data.get("reason") or "").strip()

    if adjustment == 0:
        return jsonify({"error": "Adjustment amount is required"}), 400

    previous_quantity = float(item.quantity_available or 0)
    next_quantity = previous_quantity + adjustment
    if next_quantity < 0:
        return jsonify({"error": "Stock cannot go below zero"}), 400

    user = db.session.get(User, int(get_jwt_identity()))
    actor_name = user.name if user else "Admin"

    item.quantity_available = next_quantity
    if adjustment > 0:
        item.last_restocked = utc_today()

    create_raw_material_history_entry(
        item,
        action="adjust",
        actor_name=actor_name,
        description=reason or "Adjusted raw material stock",
        quantity_change=adjustment,
        previous_quantity=previous_quantity,
        new_quantity=next_quantity,
    )
    db.session.commit()
    return jsonify({
        "message": reason or "Stock adjusted",
        "material": serialize_raw_material(item)
    })


@inventory.route("/raw/<int:item_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def delete_raw_material(item_id):
    item = db.session.get(Inventory, item_id)
    if not item:
        return jsonify({"error": "Raw material not found"}), 404

    user = db.session.get(User, int(get_jwt_identity()))
    actor_name = user.name if user else "Admin"
    create_raw_material_history_entry(
        item,
        action="delete",
        actor_name=actor_name,
        description=f"Deleted raw material {item.raw_material_name}",
        quantity_change=-float(item.quantity_available or 0),
        previous_quantity=float(item.quantity_available or 0),
        new_quantity=0,
    )
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Raw material deleted", "id": item_id})
