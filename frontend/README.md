# Kulhad Shop Frontend

Vue 3 + Vite frontend for the Kulhad Shop platform.

## Requirements

- Node.js 18+
- npm

## Setup

```bash
npm install
```

## Run

Development:

```bash
npm run dev
```

Build:

```bash
npm run build
```

Preview:

```bash
npm run preview
```

Default local URL:

```text
http://localhost:5173
```

## Frontend Responsibilities

- public storefront
- cart and checkout
- customer account and order history
- admin dashboard modules
- employee dashboard modules
- route protection based on role

## Frontend Overview

The frontend is responsible for presenting three major user experiences in one application:

- customer-facing shopping and account flows
- admin-facing management dashboards
- employee-facing production and attendance flows

## Main Routes

### Public

| Route | Purpose |
| --- | --- |
| `/` | Home page |
| `/store` | Product listing |
| `/cart` | Cart page |
| `/checkout` | Checkout page |
| `/about` | About page |
| `/login` | Login page |
| `/signup` | Signup page |
| `/account` | Customer profile and order history |

### Admin

| Route | Purpose |
| --- | --- |
| `/admin` | Admin dashboard |
| `/admin/analytics` | Analytics dashboard |
| `/admin/inventory` | Product inventory management |
| `/admin/raw-inventory` | Raw inventory management |
| `/admin/orders` | Order management |
| `/admin/employees` | Employee management |
| `/admin/payroll` | Payroll management |
| `/admin/customers` | Customer management |
| `/admin/products` | Product management |
| `/admin/products/history` | Product history log |

### Employee

| Route | Purpose |
| --- | --- |
| `/employee` | Employee dashboard |
| `/employee/entries` | Production entries history |
| `/employee/profile` | Employee self profile |

## Important Integration Files

- Router: [src/router/index.js](./src/router/index.js)
- Shared API helpers: [src/services/api.js](./src/services/api.js)
- Production API helper: [src/services/ProductionLogService.js](./src/services/ProductionLogService.js)

## Important Frontend Areas

### Storefront

- product listing and filtering
- cart state
- checkout flow
- customer account and reorder flow

### Admin Pages

- dashboard overview cards and alerts
- analytics
- product management and product history
- inventory and raw inventory
- customers and employees
- orders with payment updates
- payroll management

### Employee Pages

- production dashboard
- attendance overview
- entries history
- self profile and password reset

## Backend Dependency

The frontend depends on the backend for:

- authentication
- product data
- inventory data
- checkout address data
- orders
- payroll
- profile updates
- employee production entries

Keep the backend running on `http://127.0.0.1:5000` while using the app locally.
The backend should be started from its own virtual environment inside `backend/.venv`.
If you want the employee image-detection flow to work, the backend virtual environment should use Python 3.10 to 3.12 so `inference-sdk` can be installed.

## Data Sources Used By The Frontend

- `/api/products` for store, product management, inventory-linked views, and employee product selection
- `/api/orders` for checkout, order history, admin orders, and payment status updates
- `/api/profile` for customer and employee self-profile data
- `/api/payroll` for payroll management
- `/api/production` for employee production logs, attendance, and entries
- `/api/inventory` for finished inventory and raw inventory operations

## Functional Areas

- Product Management with categories
- Inventory and stock adjustment
- Raw Inventory Management
- Checkout address save and previous-address suggestion
- Admin order filtering, payment status, and bulk confirmation
- Customer order history and reorder
- Employee production dashboard, attendance, and entries
- Employee and customer profile pages with password reset
- Admin payroll dashboard
