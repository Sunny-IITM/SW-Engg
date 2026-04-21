from pathlib import Path
from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename
from models import Product, ProductHistory, User
from extensions import db
from middleware.role_required import role_required

products = Blueprint("products", __name__)
PRODUCT_IMAGE_DIR = Path(__file__).resolve().parent.parent / "static" / "product-images"
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def parse_non_negative_float(value, field_name):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, jsonify({"error": f"{field_name} must be a number"})

    if parsed < 0:
        return None, jsonify({"error": f"{field_name} cannot be negative"})

    return parsed, None


def parse_non_negative_int(value, field_name):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, jsonify({"error": f"{field_name} must be an integer"})

    if parsed < 0:
        return None, jsonify({"error": f"{field_name} cannot be negative"})

    return parsed, None


def get_actor_name():
    user_id = get_jwt_identity()

    try:
        user = db.session.get(User, int(user_id)) if user_id is not None else None
    except (TypeError, ValueError):
        user = None

    return user.name if user and user.name else "Admin"


def build_product_description(action, product_name, data=None):
    data = data or {}

    if action == "create":
        return f"Created product {product_name}"

    if action == "delete":
        return f"Deleted product {product_name}"

    changed_fields = []
    for field in ("name", "category", "price", "wage_per_kulhad", "stock", "image"):
        if field in data:
            changed_fields.append(field)

    if not changed_fields:
        return f"Updated product {product_name}"

    labels = {
        "name": "name",
        "category": "category",
        "price": "price",
        "wage_per_kulhad": "wage per kulhad",
        "stock": "stock",
        "image": "image"
    }
    field_text = ", ".join(labels[field] for field in changed_fields)
    return f"Updated {field_text} for {product_name}"


def log_product_history(action, product, data=None):
    history_entry = ProductHistory(
        product_id=product.id if product else None,
        product_name=product.name if product else "Unknown Product",
        action=action,
        description=build_product_description(action, product.name if product else "Unknown Product", data),
        actor_name=get_actor_name()
    )
    db.session.add(history_entry)


@products.route("/", methods=["GET"])
def get_products():
    product_list = Product.query.all()

    output = []
    for p in product_list:
        output.append({
            "id": p.id,
            "name": p.name,
            "category": p.category or "Kulhad",
            "price": p.price,
            "wage_per_kulhad": float(p.wage_per_kulhad or 0),
            "stock": p.stock,
            "image": p.image
        })

    return jsonify(output)


@products.route("/images/<path:filename>", methods=["GET"])
def get_product_image(filename):
    return send_from_directory(PRODUCT_IMAGE_DIR, filename)


@products.route("/upload-image", methods=["POST"])
@jwt_required()
@role_required("admin")
def upload_product_image():
    image_file = request.files.get("image")

    if not image_file or not image_file.filename:
        return jsonify({"error": "Image file is required"}), 400

    safe_name = secure_filename(image_file.filename)
    extension = Path(safe_name).suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "Only PNG, JPG, JPEG, and WEBP images are supported"}), 400

    PRODUCT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    image_path = PRODUCT_IMAGE_DIR / safe_name
    image_file.save(image_path)

    return jsonify({"filename": safe_name}), 201


@products.route("/history", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_product_history():
    history_entries = ProductHistory.query.order_by(ProductHistory.created_at.desc()).limit(100).all()

    output = []
    for entry in history_entries:
        output.append({
            "id": entry.id,
            "name": entry.product_name,
            "desc": entry.description or f"{entry.action.title()} product",
            "date": entry.created_at.strftime("%Y-%m-%d %I:%M %p"),
            "by": entry.actor_name or "Admin",
            "type": entry.action
        })

    return jsonify(output)


@products.route("/", methods=["POST"])
@jwt_required()
@role_required("admin")
def create_product():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    required_fields = ["name", "category", "price", "stock", "wage_per_kulhad"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    category = (data.get("category") or "").strip()
    if not category:
        return jsonify({"error": "category is required"}), 400

    price, error = parse_non_negative_float(data.get("price"), "price")
    if error:
        return error, 400

    stock, error = parse_non_negative_int(data.get("stock"), "stock")
    if error:
        return error, 400

    wage_per_kulhad, error = parse_non_negative_float(data.get("wage_per_kulhad"), "wage_per_kulhad")
    if error:
        return error, 400

    product = Product(
        name=data["name"],
        category=category,
        price=price,
        wage_per_kulhad=wage_per_kulhad,
        stock=stock,
        image=data.get("image", "")
    )

    db.session.add(product)
    db.session.flush()
    log_product_history("create", product, data)
    db.session.commit()

    return jsonify({"message": "Product created"}), 201


@products.route("/<int:product_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    if "name" in data:
        product.name = data["name"]
    if "category" in data:
        category = (data.get("category") or "").strip()
        if not category:
            return jsonify({"error": "category is required"}), 400
        product.category = category
    if "price" in data:
        price, error = parse_non_negative_float(data.get("price"), "price")
        if error:
            return error, 400
        product.price = price
    if "wage_per_kulhad" in data:
        wage_per_kulhad, error = parse_non_negative_float(data.get("wage_per_kulhad"), "wage_per_kulhad")
        if error:
            return error, 400
        product.wage_per_kulhad = wage_per_kulhad
    if "stock" in data:
        stock, error = parse_non_negative_int(data.get("stock"), "stock")
        if error:
            return error, 400
        product.stock = stock
    if "image" in data:
        product.image = data["image"]

    log_product_history("update", product, data)
    db.session.commit()
    return jsonify({"message": "Product updated"})


@products.route("/<int:product_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    log_product_history("delete", product)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"})
