# API Documentation

## Base URL

```text
http://localhost:5000/api
```

## Local Setup Note

For backend development, create the Python virtual environment inside `backend/.venv` and install dependencies from `backend/requirements.txt`.

If you want the kulhad image-detection routes to work locally, use Python 3.10 to 3.12 in that backend virtual environment. Roboflow `inference-sdk` is not currently available for Python 3.13.

## Authentication

This backend uses JWT bearer tokens for protected endpoints.

```text
Authorization: Bearer <jwt_token>
```

## Implemented Route Groups

### Authentication

- `POST /api/auth/register`
- `POST /api/auth/login`

### Products

- `GET /api/products/`
- `GET /api/products/images/<filename>`
- `POST /api/products/upload-image`
- `GET /api/products/history`
- `POST /api/products/`
- `PUT /api/products/<product_id>`
- `DELETE /api/products/<product_id>`

### Inventory

- `GET /api/inventory/`
- `GET /api/inventory/history`
- `POST /api/inventory/adjust`

### Analytics

- `GET /api/analytics/dashboard`
- `GET /api/analytics/summary`

### Admin User Management

- `GET /api/admin/users`
- `POST /api/admin/users`
- `PUT /api/admin/users/<user_id>`
- `DELETE /api/admin/users/<user_id>`

### Admin Orders

- `GET /api/orders/admin`
- `PUT /api/orders/<order_id>/status`

## Request and Response Notes

### `POST /api/auth/register`

Request body:

```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password": "securePass123",
  "role": "customer",
  "phone": "9876543210",
  "address": "Chennai"
}
```

Success response:

```json
{
  "message": "User registered successfully"
}
```

### `POST /api/auth/login`

Request body:

```json
{
  "email": "jane@example.com",
  "password": "securePass123"
}
```

Success response:

```json
{
  "token": "jwt-token",
  "name": "Jane Smith",
  "role": "customer",
  "email": "jane@example.com",
  "phone": "9876543210",
  "address": "Chennai"
}
```

### `GET /api/products/`

Public endpoint. Returns all products.

Example response:

```json
[
  {
    "id": 1,
    "name": "Classic Kulhad",
    "price": 25.0,
    "stock": 50,
    "image": "classic.png"
  }
]
```

### `POST /api/products/upload-image`

Protected admin endpoint. Accepts `multipart/form-data` with an `image` file and returns:

```json
{
  "filename": "classic.png"
}
```

### `POST /api/inventory/adjust`

Protected admin endpoint used to increase or reduce stock and update the minimum stock threshold.

Request body:

```json
{
  "product_id": 1,
  "type": "add",
  "quantity": 25,
  "reason": "Weekly production batch",
  "min_stock": 10
}
```

Success response:

```json
{
  "message": "Inventory updated",
  "product": {
    "id": 1,
    "name": "Classic Kulhad",
    "category": "Kulhads",
    "stock": 75,
    "min_stock": 10,
    "price": 25.0
  }
}
```

### `GET /api/analytics/dashboard`

Protected admin endpoint for dashboard cards, low-stock alerts, and recent orders.

### `GET /api/analytics/summary`

Protected admin endpoint for sales, inventory, and payment analytics used by owner-facing reports.

### `GET /api/admin/users`

Protected admin endpoint. Optional query parameter:

```text
role=customer|employee|admin
```

### `GET /api/orders/admin`

Protected admin endpoint that returns order summaries with customer, payment, and item details.

### `PUT /api/orders/<order_id>/status`

Protected admin endpoint. Allowed statuses:

```text
pending, confirmed, shipped, delivered, cancelled
```

## Computer Vision and Production APIs

The backend exposes kulhad detection endpoints using the Roboflow Inference HTTP SDK.

### `POST /api/production/detect`

Alias: `POST /detect-kulhad`

Purpose: upload an image and detect the number of kulhads using the Roboflow hosted model `kulhad-detector/1`.

Request:

- Content type: `multipart/form-data`
- Form field: `image`

Environment requirement:

- Set `ROBOFLOW_API_KEY` in `backend/.env`
- Use a backend Python 3.10-3.12 virtual environment so `inference-sdk` is available

Expected response:

```json
{
  "success": true,
  "kulhad_count": 2,
  "detections": [
    {
      "x": 212,
      "y": 180,
      "width": 110,
      "height": 140,
      "confidence": 0.87,
      "class": "kulhad"
    }
  ]
}
```

Possible error responses:

```json
{
  "success": false,
  "error": "missing_file",
  "message": "Image file is required"
}
```

```json
{
  "success": false,
  "error": "configuration_error",
  "message": "ROBOFLOW_API_KEY is not configured"
}
```

### `POST /api/production/log`

Purpose: persist a production log entry after manual entry or image-based confirmation.

Request body:

```json
{
  "method": "image",
  "product_id": 1,
  "product": "Classic Kulhad",
  "quantity": 6,
  "confidence": 0.91,
  "date": "2026-04-05"
}
```

Example response:

```json
{
  "id": 14,
  "product_id": 1,
  "product_name": "Classic Kulhad",
  "date": "2026-04-05",
  "status": "Present",
  "type": "Image",
  "kulhad_quantity": 6,
  "cup_quantity": 0,
  "total_quantity": 6,
  "wage_per_kulhad": 4.5,
  "daily_wage": 27.0,
  "notes": "",
  "created_at": "2026-04-05 05:30 PM"
}
```

Notes:

- `method` can be `manual` or `image`
- the employee dashboard now supports both manual quantity entry and image-based detection before confirmation
- image detection only suggests the quantity; the final production entry is saved through `/api/production/log`

### `GET /api/production/entries`

Purpose: fetch the employee's production entries and leave-derived attendance rows for a selected month and year.

Query parameters:

```text
month=<1-12>&year=<positive-integer>
```

Example response:

```json
[
  {
    "id": 14,
    "product_id": 1,
    "product_name": "Classic Kulhad",
    "date": "2026-04-05",
    "status": "Present",
    "type": "Image",
    "kulhad_quantity": 6,
    "cup_quantity": 0,
    "total_quantity": 6,
    "wage_per_kulhad": 4.5,
    "daily_wage": 27.0,
    "notes": "",
    "created_at": "2026-04-05 05:30 PM"
  }
]
```

## Common Error Responses

Unauthorized:

```json
{
  "msg": "Missing Authorization Header"
}
```

Forbidden:

```json
{
  "message": "Access forbidden"
}
```

Validation example:

```json
{
  "error": "name is required"
}
```

## Known Gaps

- The `cart` blueprint exists but no cart routes are implemented yet.
- Customer checkout, order creation, cancellation, and notification endpoints are not implemented in the current Flask app.
