# Frontend and Backend Integration Guide

This document explains how the Kulhad Shop frontend and backend work together in the current application architecture.

## Stack

- Frontend: Vue 3, Vite, Vue Router, Chart.js
- Backend: Flask, Flask-JWT-Extended, Flask-Bcrypt, Flask-SQLAlchemy, Flask-CORS
- Database: SQLite

## Runtime Flow

### Frontend

- The frontend uses helper functions in [frontend/src/services/api.js](./frontend/src/services/api.js) for most API calls.
- Employee production logging uses [frontend/src/services/ProductionLogService.js](./frontend/src/services/ProductionLogService.js).
- Auth session data is stored client-side and used by router guards.
- Protected routes are defined in [frontend/src/router/index.js](./frontend/src/router/index.js).

### Backend

- The Flask app is created in [backend/app.py](./backend/app.py).
- API routes are registered under `/api/...`.
- The backend creates missing database tables and applies lightweight schema upgrades at startup.

## Integration Architecture

The project uses a straightforward split:

- Vue pages and components handle rendering, forms, route guards, and user interactions.
- Service files in the frontend translate those actions into HTTP requests.
- Flask blueprints handle validation, role checks, persistence, and response shaping.
- SQLite stores the data, while backend startup logic keeps older local databases compatible with newer features.

Most platform features in the repository follow the same pattern:

1. add or extend a backend model or route
2. expose a frontend service helper
3. connect a page or modal to that helper
4. refresh the related dashboard or list from backend data

## Base URLs

- Frontend dev server: `http://localhost:5173`
- Backend API server: `http://127.0.0.1:5000`
- Frontend API base: `/api`
- Backend route prefix: `/api/...`

In development, the frontend talks to the backend through the `/api` path, so the backend must be running when testing authenticated flows, checkout, orders, inventory, payroll, or employee entries.

For local setup, create and activate the Python virtual environment inside `backend/.venv`. Do not place the main Python virtual environment at the repository root if it is intended for backend work.
If you are testing kulhad image detection, use Python 3.10 to 3.12 in that backend virtual environment because Roboflow `inference-sdk` does not currently support Python 3.13.

## Authentication Integration

- Login is handled through `/api/auth/login`.
- The backend returns the JWT token and user role.
- The frontend uses that token in the `Authorization` header for protected requests.
- Route access is role-based:
  - `admin` routes under `/admin`
  - `employee` routes under `/employee`
  - customer pages like `/checkout` and `/account` require login

## Session And Role Behavior

- Admin users are redirected into the admin dashboard after login.
- Employee users are redirected into the employee dashboard after login.
- Customers are redirected into storefront flows and authenticated account pages.
- Protected frontend pages depend on both the token and the role returned by the backend.
- Most admin and employee APIs enforce role checks again on the server side, not just in the router.

## Major Integrated Features

### Product Management to Storefront

- Admins create and update products from Product Management.
- Storefront pages fetch products from `/api/products/`.
- Product images are built in the frontend with `buildProductImageUrl`.
- Product categories now come from backend product data rather than static frontend values.
- Employee production entry dropdowns now also reuse the same backend product list.

### Inventory and Raw Inventory

- Product inventory is handled through `/api/inventory`.
- Raw material inventory is handled through `/api/inventory/raw`.
- The raw inventory page supports:
  - add material
  - edit material
  - adjust stock
  - delete material
  - reminder-level alerts
- Inventory and raw inventory are now separate operational views for finished goods and production materials.

### Checkout and Customer Address

- Checkout saves customer address data through `/api/orders/checkout-profile`.
- The My Account page reads profile and order history from the backend.
- Saved addresses are suggested again on the checkout page as "use previous address".
- Address details are also surfaced again in the customer-facing account experience.

### Orders and Admin Order Dashboard

- Customers place orders through `/api/orders/`.
- Admin order management reads from `/api/orders/admin`.
- Admins can update order status, payment status, and bulk payment confirmation.
- Customer order history is linked to the backend and supports reorder.
- Admin order screens refresh more reliably from backend order data instead of depending on a one-time page load.

### Employee Dashboard and Entries

- Employees log production through `/api/production/log`.
- Employee entries are read from `/api/production/entries`.
- The employee dashboard graph and totals now use live backend production data.
- Employee production entry product selection now pulls from Product Management names.
- The employee dashboard now also supports capture or upload image detection through `/api/production/detect` and `/detect-kulhad`.
- Backend mapping converts the selected product to the correct production bucket using product category.
- Future-date entries are blocked.
- Attendance is derived from entries:
  - entry exists => Present
  - no entry => Leave
- The dashboard and the entries page both depend on the same production data source, which keeps attendance and totals consistent.

### Payroll

- Admin payroll data is served from `/api/payroll`.
- Payroll records are generated and updated per month and year.
- Admins can process and mark payments from the payroll dashboard.

### Profile Integration

- Customer and employee self-profile data is served from `/api/profile/me`.
- Email changes are blocked from the profile pages.
- Password reset is handled through the same profile update flow.

## Core Data Flows

### Product To Employee Entry Flow

1. Admin creates or updates a product in Product Management.
2. The product becomes available through `/api/products/`.
3. The employee dashboard loads that product list for entry selection.
4. The backend maps the selected product into the correct production bucket for attendance and totals.

### Checkout To Account Flow

1. Customer enters address details during checkout.
2. Frontend saves them through `/api/orders/checkout-profile`.
3. Saved address data appears later in My Account.
4. Checkout can suggest the previous address on the next visit.

### Production To Attendance Flow

1. Employee submits a production entry.
2. Backend stores it in production tables.
3. Employee dashboard and entries page reload from `/api/production/entries`.
4. Days with entries become `Present`; missing days for the selected month show as `Leave`.

### Order To Admin Flow

1. Customer places an order.
2. Order and payment data are stored on the backend.
3. Admin order dashboard fetches those records from backend order APIs.
4. Admin can update payment state, order state, and bulk payment processing.

## Startup Order

For local development:

1. Start the backend first from `backend/.venv`.
2. Start the frontend second.
3. Sign in using the appropriate role.
4. Test role-specific dashboards only after the backend is available.

## When a Backend Restart Is Required

Restart the backend after changes to:

- route registration
- database models
- schema upgrade logic
- new API validation
- new profile, payroll, order, or production behavior

This matters because the application relies on Flask route registration and startup schema initialization.

## Key Files

- App bootstrap: [backend/app.py](./backend/app.py)
- Models: [backend/models.py](./backend/models.py)
- Frontend API helpers: [frontend/src/services/api.js](./frontend/src/services/api.js)
- Production service: [frontend/src/services/ProductionLogService.js](./frontend/src/services/ProductionLogService.js)
- Router: [frontend/src/router/index.js](./frontend/src/router/index.js)

## Implementation Notes

- If a feature needs persistent data, prefer adding it through backend routes instead of local-only frontend state.
- After changing models or startup schema logic, restart the backend before testing.
- When a frontend page looks stale, check whether it is still using placeholder values instead of service-layer data.
