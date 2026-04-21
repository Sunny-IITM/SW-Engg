# Pytest Test Plan

This plan splits coverage into three layers:

- `backend API`: Flask route, validation, authorization, persistence, and business-rule tests
- `frontend logic`: route-guard, auth-session, API-client, and page-behavior tests
- `system / e2e`: user journeys that cross frontend, backend, database, and filesystem boundaries

The repository already has broad happy-path backend coverage. The highest-value next step is adding negative-path, authorization-edge, and cross-module regression tests.

## Confirmed Or High-Probability Issue Targets

These are the first issue-focused cases to automate because they are already confirmed in code review or are very likely defects.

1. Registration accepts `role="admin"` and allows privilege escalation.
2. Registration does not normalize email casing before duplicate checks.
3. Admin user update accepts blank email values.
4. Product creation allows negative prices.
5. Inventory adjustment resets `min_stock` to `0` when that field is omitted.
6. Inventory adjustment negative quantity validation should remain covered as a regression guard.
7. Order creation accepts negative shipping and can undercharge totals.
8. Single-order status update silently ignores invalid payment status values.
9. Payroll update silently normalizes invalid payroll statuses instead of rejecting them.
10. Bulk payroll update does not validate `paid_on` within the selected month.
11. Production entries endpoint does not validate month bounds.
12. Payroll endpoint does not validate month bounds.
13. Authentication registration can fail with server errors on malformed payloads instead of clean `400` responses.
14. Login lookup is case-sensitive, which can break normal user expectations.
15. Product update does not validate negative stock or negative price.
16. Raw inventory unit validation is inconsistent because allowed-unit constants are defined but not enforced.
17. Production logging likely allows duplicate same-day entries, which can double-count payroll.
18. Order flow does not document or validate duplicate line items for the same product.
19. Frontend bundle size is high enough to trigger Vite chunk warnings and should be tracked as a performance regression.
20. Test documentation in `backend/PYTEST_TEST_DOCUMENTATION.md` is stale and already diverges from the current codebase.

## Backend Pytest Coverage Matrix

### Authentication

- Register customer successfully.
- Reject duplicate email.
- Reject duplicate email with different case.
- Reject missing JSON body.
- Reject missing required fields one by one: `name`, `email`, `password`.
- Reject unsupported roles.
- Reject `admin` self-registration.
- Login success for customer.
- Login success for employee.
- Reject unknown email.
- Reject wrong password.
- Reject inactive user.
- Verify login payload shape for each role.

### Admin Users

- Admin can list all users.
- Admin can filter by `customer`.
- Admin can filter by `employee`.
- Non-admin cannot list users.
- Admin can create customer.
- Admin can create employee.
- Reject duplicate email on create.
- Reject invalid role on create.
- Reject blank required fields on create.
- Admin can update customer fields.
- Admin can update employee wage, department, and title.
- Reject duplicate email on update.
- Reject blank email on update.
- Reject deleting current admin account.
- Reject deleting nonexistent user.

### Profile

- Customer can fetch own profile.
- Employee can fetch own profile.
- Customer can update address fields.
- Employee can update phone/address.
- Reject self email change.
- Reject password change with wrong current password.
- Reject password change when new password is too short.
- Reject password change when one password field is missing.

### Products

- Public catalog loads.
- Product image endpoint serves valid files.
- Reject nonexistent product image.
- Admin can upload valid image types.
- Reject image upload without file.
- Reject unsupported image extension.
- Admin can create product.
- Reject missing required create fields.
- Reject blank category.
- Reject negative price.
- Reject negative stock.
- Reject negative wage per unit if business rules forbid it.
- Admin can update normal fields.
- Reject update for nonexistent product.
- Reject invalid numeric updates.
- Product history entry is created for create/update/delete.

### Inventory

- Admin can read current stock list.
- Inventory list preserves stored `min_stock`.
- Admin can adjust stock up.
- Admin can adjust stock down.
- Reject remove when stock is insufficient.
- Reject missing `product_id`.
- Reject invalid adjustment `type`.
- Reject no-op adjustment.
- Reject negative quantity.
- Preserve `min_stock` when omitted.
- Allow threshold-only update without stock change.
- History row is written for each stock change.

### Raw Inventory

- Admin can list raw materials.
- Admin can list raw inventory history.
- Admin can create raw material.
- Reject duplicate raw material name.
- Reject negative quantity.
- Reject negative reorder level.
- Reject negative cost.
- Reject missing unit.
- Reject unsupported unit if unit whitelist is enforced.
- Admin can update raw material.
- Admin can adjust raw stock positive and negative.
- Reject raw stock going below zero.
- Admin can delete raw material.

### Orders

- Customer can fetch checkout profile.
- Non-customer cannot use checkout profile routes.
- Customer can save checkout profile.
- Customer can create order with COD.
- Customer can create order with online payment method.
- Reject order with empty items.
- Reject order with invalid product id.
- Reject quantity exceeding stock.
- Reject quantity `<= 0`.
- Reject incomplete delivery address.
- Reject negative shipping.
- Verify stock decreases after successful order.
- Verify payment row is created with correct method/status.
- Admin can list orders.
- Customer can fetch own order history only.
- Admin can update order status.
- Reject invalid order status.
- Reject invalid payment status.
- Bulk payment update works.
- Reject bulk payment update with empty order selection.

### Production

- Employee can fetch entries for current month.
- Employee can log manual production.
- Employee can log cup-category production and populate `cup_quantity`.
- Employee can log leave entry with zero quantity.
- Reject future date.
- Reject invalid date format.
- Reject invalid product.
- Reject non-employee access.
- Reject invalid month and year bounds.
- Reject duplicate same-day entry if duplicates are disallowed.
- Payroll totals reflect logged production.

### Payroll

- Admin can fetch payroll list.
- Employee can fetch own payroll.
- Admin can update bonus/deductions/status.
- Reject invalid payroll status.
- Reject invalid `paid_on` format.
- Reject `paid_on` outside payroll month.
- Bulk payroll status update works.
- Reject bulk status with no `current_statuses`.
- Reject bulk status invalid status.
- Reject bulk `paid_on` outside payroll month.
- Skip inactive employees in payroll list.
- Gross/net wages stay consistent with production totals.

### Analytics

- Dashboard summary returns core counts.
- Summary aggregates revenue correctly.
- Low-stock cards reflect inventory settings.
- Daily report requires webhook configuration.
- Daily report handles upstream delivery failure cleanly.

## Frontend Test Cases To Add

These should be driven by pytest only if you choose a Python browser stack such as `pytest-playwright`, `pytest-selenium`, or API-plus-DOM smoke tests. The app currently has no frontend test harness.

1. Router redirects unauthenticated users from `/checkout` to `/login`.
2. Router redirects unauthenticated users from `/account` to `/login`.
3. Router redirects non-admin users away from `/admin`.
4. Router redirects non-employee users away from `/employee`.
5. Logged-in admin visiting `/login` lands on admin dashboard.
6. Logged-in employee visiting `/signup` lands on employee dashboard.
7. Customer login stores token and role in local storage.
8. Corrupt auth session in local storage is cleared safely.
9. Store page renders product cards from `/api/products`.
10. Broken product image falls back gracefully.
11. Cart persists and reloads expected items.
12. Checkout pre-fills saved address from `/api/orders/checkout-profile`.
13. Checkout blocks submission when address is incomplete.
14. Checkout shows backend validation errors cleanly.
15. Profile page blocks email editing.
16. Employee entries page rejects future-date submission.
17. Admin product page preserves category and wage fields on edit.
18. Admin inventory page does not zero out `min_stock` when only stock is edited.
19. Admin orders page rejects invalid payment-state transitions.
20. Frontend build stays green and bundle-size warnings are tracked.

## End-To-End System Scenarios

1. Customer signup -> login -> add to cart -> checkout -> order history reflects purchase.
2. Admin creates product -> storefront shows new product -> customer buys it -> inventory decreases.
3. Admin updates stock -> analytics low-stock widget changes accordingly.
4. Employee logs production -> payroll gross wages update -> admin can process payroll.
5. Admin disables employee -> employee login is blocked -> payroll list excludes inactive employee.
6. Admin uploads product image -> storefront image URL resolves and renders.
7. Customer updates saved address -> checkout and account page show identical values.
8. Admin refunds payment -> order admin list and customer history both reflect updated payment status.

## Execution Recommendation

Use three pytest layers:

- `backend/tests/`: direct Flask test client coverage, fast and deterministic
- `tests/contracts/`: API contract tests that validate payload shape expected by the frontend
- `tests/e2e/`: browser-driven user journeys using a pytest plugin and a temporary test database

For this repository, the fastest path is:

1. Keep expanding Flask client tests for validation and authorization defects.
2. Add a frontend browser layer only after the backend contracts are stable.
3. Promote each confirmed bug into a regression test before fixing it.
