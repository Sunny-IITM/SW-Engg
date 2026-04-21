from collections import defaultdict
from datetime import UTC, datetime, timedelta
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import jwt_required

from middleware.role_required import role_required
from models import Customer, Employee, InventoryHistory, InventorySetting, Order, Payment, Product

analytics = Blueprint("analytics", __name__)


def utc_today():
    return datetime.now(timezone.utc).date()


def format_currency(value):
    return round(float(value or 0), 2)


def iter_last_n_days(days):
    today = utc_today()
    return [today - timedelta(days=index) for index in range(days - 1, -1, -1)]


def iter_last_n_months(months):
    current = utc_today().replace(day=1)
    values = []
    for index in range(months - 1, -1, -1):
        month = current.month - index
        year = current.year
        while month <= 0:
            month += 12
            year -= 1
        values.append((year, month))
    return values


def build_analytics_snapshot():
    payments = Payment.query.order_by(Payment.payment_date.asc()).all()
    orders = Order.query.order_by(Order.order_date.asc()).all()
    products = Product.query.all()
    settings = {setting.product_id: int(setting.min_stock or 10) for setting in InventorySetting.query.all()}
    inventory_history = InventoryHistory.query.order_by(InventoryHistory.created_at.asc()).all()

    today = utc_today()
    month_start = today.replace(day=1)

    total_revenue = sum(float(payment.amount or 0) for payment in payments)
    today_revenue = sum(float(payment.amount or 0) for payment in payments if payment.payment_date == today)
    monthly_revenue = sum(float(payment.amount or 0) for payment in payments if payment.payment_date and payment.payment_date >= month_start)

    day_labels = []
    day_values = []
    payments_by_day = defaultdict(float)
    for payment in payments:
        if payment.payment_date:
            payments_by_day[payment.payment_date] += float(payment.amount or 0)

    for day in iter_last_n_days(7):
        day_labels.append(day.strftime('%d %b'))
        day_values.append(round(payments_by_day.get(day, 0), 2))

    monthly_labels = []
    monthly_values = []
    payments_by_month = defaultdict(float)
    for payment in payments:
        if payment.payment_date:
            payments_by_month[(payment.payment_date.year, payment.payment_date.month)] += float(payment.amount or 0)

    for year, month in iter_last_n_months(6):
        monthly_labels.append(datetime(year, month, 1).strftime('%b'))
        monthly_values.append(round(payments_by_month.get((year, month), 0), 2))

    low_stock_count = 0
    out_of_stock_count = 0
    inventory_value = 0
    low_stock_items = []
    for product in sorted(products, key=lambda item: (int(item.stock or 0), item.name or "")):
        stock = int(product.stock or 0)
        min_stock = settings.get(product.id, 10)
        inventory_value += float(product.price or 0) * stock
        if stock <= 0:
            out_of_stock_count += 1
        if stock <= min_stock:
            low_stock_count += 1
            low_stock_items.append({
                "name": product.name or "Product",
                "stock": stock,
                "min_stock": min_stock,
            })

    movement_map = {day: {'added': 0, 'sold': 0} for day in iter_last_n_days(7)}
    for entry in inventory_history:
        entry_day = entry.created_at.date()
        if entry_day in movement_map:
            if entry.change > 0:
                movement_map[entry_day]['added'] += int(entry.change)
            elif entry.change < 0:
                movement_map[entry_day]['sold'] += abs(int(entry.change))

    inventory_movement = {
        'labels': [day.strftime('%d %b') for day in iter_last_n_days(7)],
        'added': [movement_map[day]['added'] for day in iter_last_n_days(7)],
        'sold': [movement_map[day]['sold'] for day in iter_last_n_days(7)]
    }

    payment_methods = defaultdict(float)
    for payment in payments:
        payment_methods[payment.payment_method or 'Other'] += float(payment.amount or 0)

    pending_amount = sum(float(order.total_amount or 0) for order in orders if (order.status or '').lower() == 'pending')
    pending_orders = sum(1 for order in orders if (order.status or '').lower() == 'pending')
    completed_orders = sum(1 for order in orders if (order.status or '').lower() == 'completed')

    return {
        'sales': {
            'today_revenue': format_currency(today_revenue),
            'monthly_revenue': format_currency(monthly_revenue),
            'total_orders': len(orders),
            'total_revenue': format_currency(total_revenue),
            'daily_revenue': {
                'labels': day_labels,
                'values': day_values
            },
            'monthly_revenue_chart': {
                'labels': monthly_labels,
                'values': monthly_values
            }
        },
        'inventory': {
            'total_products': len(products),
            'low_stock': low_stock_count,
            'inventory_value': format_currency(inventory_value),
            'out_of_stock': out_of_stock_count,
            'low_stock_items': low_stock_items[:5],
            'stock_status': {
                'labels': ['In Stock', 'Low Stock', 'Out of Stock'],
                'values': [max(len(products) - low_stock_count, 0), low_stock_count - out_of_stock_count, out_of_stock_count]
            },
            'movement': inventory_movement
        },
        'payments': {
            'total_payments': format_currency(total_revenue),
            'pending_amount': format_currency(pending_amount),
            'completed_amount': format_currency(total_revenue),
            'transaction_count': len(payments),
            'method_breakdown': {
                'labels': list(payment_methods.keys()) or ['No Payments'],
                'values': [round(value, 2) for value in payment_methods.values()] or [0]
            },
            'trend': {
                'labels': day_labels,
                'values': day_values
            }
        },
        'overview': {
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'report_date': today.isoformat()
        }
    }


def build_daily_report_message(summary):
    sales = summary["sales"]
    inventory = summary["inventory"]
    payments = summary["payments"]
    overview = summary["overview"]

    low_stock_lines = [
        f"- {item['name']}: {item['stock']} left (min {item['min_stock']})"
        for item in inventory.get("low_stock_items", [])
    ] or ["- No urgent low-stock items today"]

    return "\n".join([
        f"Daily Overall Report - {overview['report_date']}",
        "",
        "Sales",
        f"- Today's revenue: INR {sales['today_revenue']:.2f}",
        f"- Monthly revenue: INR {sales['monthly_revenue']:.2f}",
        f"- Total orders: {sales['total_orders']}",
        f"- Pending orders: {overview['pending_orders']}",
        f"- Completed orders: {overview['completed_orders']}",
        "",
        "Inventory",
        f"- Total products: {inventory['total_products']}",
        f"- Low stock items: {inventory['low_stock']}",
        f"- Out of stock: {inventory['out_of_stock']}",
        f"- Inventory value: INR {inventory['inventory_value']:.2f}",
        "",
        "Payments",
        f"- Total payments received: INR {payments['total_payments']:.2f}",
        f"- Pending payment amount: INR {payments['pending_amount']:.2f}",
        f"- Transactions recorded: {payments['transaction_count']}",
        "",
        "Immediate Attention",
        *low_stock_lines
    ])


def send_google_chat_daily_report():
    webhook_url = (current_app.config.get("GOOGLE_CHAT_WEBHOOK_URL") or "").strip()
    if not webhook_url:
        raise ValueError("GOOGLE_CHAT_WEBHOOK_URL is not configured")

    summary = build_analytics_snapshot()
    message_text = build_daily_report_message(summary)
    payload = json.dumps({"text": message_text}).encode("utf-8")
    request = Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        method="POST"
    )

    try:
        with urlopen(request, timeout=15) as response:
            response_body = response.read().decode("utf-8") if response else ""
    except HTTPError as error:
        raise RuntimeError(f"Google Chat webhook returned HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError(f"Unable to reach Google Chat webhook: {error.reason}") from error

    return {
        "message": "Daily report sent successfully",
        "preview": message_text,
        "response": response_body,
    }


@analytics.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_dashboard_summary():
    product_count = Product.query.count()
    order_count = Order.query.count()
    customer_count = Customer.query.count()
    employee_count = Employee.query.count()

    settings = {setting.product_id: setting.min_stock for setting in InventorySetting.query.all()}
    products = Product.query.order_by(Product.stock.asc(), Product.name.asc()).all()

    low_stock = []
    for product in products:
        min_stock = int(settings.get(product.id, 10) or 10)
        stock = int(product.stock or 0)
        if stock <= min_stock:
            low_stock.append({
                'id': product.id,
                'name': product.name,
                'stock': stock,
                'min_stock': min_stock
            })

    customer_lookup = {customer.id: customer.name for customer in Customer.query.all()}
    recent_orders = []
    for order in Order.query.order_by(Order.id.desc()).limit(5).all():
        recent_orders.append({
            'id': order.id,
            'order_number': f'ORD-{order.id:04d}',
            'customer_name': customer_lookup.get(order.customer_id, 'Customer'),
            'amount': format_currency(order.total_amount),
            'status': (order.status or 'pending').title()
        })

    return jsonify({
        'stats': {
            'products': product_count,
            'orders': order_count,
            'customers': customer_count,
            'employees': employee_count
        },
        'low_stock': low_stock[:5],
        'recent_orders': recent_orders
    })


@analytics.route('/summary', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_analytics_summary():
    return jsonify(build_analytics_snapshot())


@analytics.route('/daily-report/send', methods=['POST'])
@jwt_required()
@role_required('admin')
def send_daily_report():
    try:
        result = send_google_chat_daily_report()
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 502

    return jsonify(result)
