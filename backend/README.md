# Kulhad Shop Backend

Flask backend for the Kulhad Shop platform.

## Requirements

- Python 3.10+
- pip

For kulhad image detection with Roboflow `inference-sdk`, use Python 3.10 to 3.12. The SDK is not currently available for Python 3.13, so the detection endpoint will stay unavailable on 3.13-only environments.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create the virtual environment inside the `backend/` folder. The intended backend environment path is `backend/.venv`, not a repository-level virtual environment.

If you want the `/detect-kulhad` and `/api/production/detect` endpoints to work locally, install dependencies in a Python 3.10-3.12 environment so `inference-sdk` can be resolved correctly.

You can place backend-only environment variables such as `ROBOFLOW_API_KEY` in `backend/.env`.

## Run

```bash
python app.py
```

Default local API URL:

```text
http://127.0.0.1:5000
```

## Dependencies

- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-Bcrypt
- Flask-Cors
- inference-sdk for Roboflow kulhad detection on Python 3.10-3.12
- python-dotenv for loading `backend/.env`

## Main Responsibilities

- JWT authentication
- user, customer, and employee profile management
- product and category storage
- inventory and raw inventory operations
- orders, payments, and checkout profile save
- payroll management
- employee production logging and attendance data
- lightweight schema upgrades for existing SQLite databases

## Backend Overview

The backend is more than a simple API layer. It currently handles:

- authentication and role protection
- normalization of customer and employee profile data
- admin management operations
- persistence of newer operational modules such as payroll and raw inventory
- migration support for older local SQLite database files

## Startup Behavior

When the backend starts, [app.py](./app.py):

- creates missing tables
- registers all `/api/...` blueprints
- applies schema updates for newer fields
- migrates legacy user profile fields into `customer` and `employee` tables

This startup behavior is important for local development because the repository has introduced newer columns and tables over time without a separate migration framework.

## Main Route Groups

| Prefix | Purpose |
| --- | --- |
| `/api/auth` | login and registration |
| `/api/products` | products, images, history |
| `/api/inventory` | product inventory and raw inventory |
| `/api/analytics` | admin analytics |
| `/api/admin` | admin employee and customer management |
| `/api/cart` | cart helpers |
| `/api/orders` | checkout profile, customer orders, admin orders |
| `/api/payroll` | payroll management |
| `/api/profile` | customer and employee self profile |
| `/api/production` | employee production entries and attendance |

## Route Group Details

### `/api/auth`

- user registration
- login
- JWT session generation

### `/api/products`

- public product listing
- admin product creation and update
- product image upload and serving
- product history tracking

### `/api/inventory`

- finished product inventory
- stock adjustment
- stock history
- raw inventory endpoints for raw materials

### `/api/orders`

- customer order creation
- checkout profile save/load
- customer order history
- admin order listing and status updates
- payment status update flows

### `/api/profile`

- customer self-profile load/update
- employee self-profile load/update
- password reset support
- email change blocking

### `/api/production`

- employee production entry logging
- attendance row generation from production data
- monthly employee entries retrieval

### `/api/payroll`

- monthly payroll generation
- payroll record updates
- processed and paid state transitions

## Key Files

- App bootstrap: [app.py](./app.py)
- Models: [models.py](./models.py)
- API details: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

## Database Notes

- SQLite is used by default.
- The app includes schema update logic for newer fields like:
  - product category
  - raw inventory details
  - customer address fields
  - payment status
  - employee profile fields
- Restart the backend after model or route changes so the schema/update logic runs.

## Data Model And API Coverage

- Product records support categories
- Inventory records support raw-material metadata like supplier, cost, and reminder level
- Customer records support detailed address data
- Payment records carry payment status
- Profile routes support customer and employee self-service updates
- Production routes power attendance and employee entry history
- Payroll routes support monthly payroll management
