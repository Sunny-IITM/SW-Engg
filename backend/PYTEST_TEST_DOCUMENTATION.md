# Pytest Test Case Documentation

This document summarizes all pytest API tests in the backend project.

Test execution reference:
- Total tests: 38
- Passed: 37
- Failed: 1
- Test run date: 2026-04-03

## Bug Highlight

### test_update_product_stock_should_persist_new_stock_value
- Endpoint: `PUT /api/products/<product_id>`
- Input: `{"stock": 99}`
- Expected output: HTTP `200`, and the product's persisted stock in the database should become `99`
- Actual output: HTTP `200`, but the persisted stock remains `20`
- What bug this reveals: the product update endpoint accepts the request successfully but ignores the `stock` field during update
- Root cause visible in implementation: [`routes/products.py`](C:\Users\Arnav Mehta\Desktop\Code-Four\software-engineering-project\backend\routes\products.py#L163) updates `name`, `category`, `price`, and `image`, but never assigns `product.stock = data["stock"]`
- Real-world impact: an admin may believe stock was corrected in the system while inventory remains wrong, which can lead to overselling, stockout confusion, and inaccurate reporting

---

## Authentication API

### 1. test_register_user_success
- Test case name: `test_register_user_success`
- API endpoint being tested: `POST /api/auth/register`
- Input provided:
```json
{
  "name": "New Customer",
  "email": "newcustomer@example.com",
  "password": "secret123",
  "role": "customer",
  "phone": "7777777777",
  "address": "New Address"
}
```
- Expected output: HTTP `201` with `{"message": "User registered successfully"}`
- Actual output: Same as expected
- What the test is checking: a new customer can be registered successfully
- Why this test is important: user signup is the starting point for customer onboarding

### 2. test_login_success_returns_profile_details
- Test case name: `test_login_success_returns_profile_details`
- API endpoint being tested: `POST /api/auth/login`
- Input provided:
```json
{
  "email": "customer@example.com",
  "password": "customerpass"
}
```
- Expected output: HTTP `200` with customer profile details and a JWT token
- Actual output: login returns the seeded customer's profile fields plus a `token`
- What the test is checking: valid login should authenticate the user and return the correct profile data
- Why this test is important: login must both verify identity and provide the frontend with the information needed to start a session

## Admin And Profile API

### 3. test_get_admin_users_list
- Test case name: `test_get_admin_users_list`
- API endpoint being tested: `GET /api/admin/users?role=customer`
- Input provided: query parameter `role=customer`, admin bearer token
- Expected output: HTTP `200` and at least one customer user in the response list
- Actual output: list response with length `>= 1`
- What the test is checking: admin filtering by role works and returns customer accounts
- Why this test is important: admins need reliable filtered user lists for management tasks

### 4. test_create_admin_managed_user
- Test case name: `test_create_admin_managed_user`
- API endpoint being tested: `POST /api/admin/users`
- Input provided:
```json
{
  "name": "Worker Two",
  "email": "worker.two@example.com",
  "password": "workerpass",
  "role": "employee",
  "phone": "1234567890",
  "address": "Factory Road",
  "department": "Production",
  "job_title": "Painter",
  "daily_wage": 18000
}
```
- Expected output: HTTP `201` with created employee details including `daily_wage = 18000.0`
- Actual output: created employee response matches expected fields and wage value
- What the test is checking: admins can create employee accounts with job-related metadata
- Why this test is important: businesses often create staff accounts centrally rather than asking workers to self-register

### 5. test_update_admin_managed_user
- Test case name: `test_update_admin_managed_user`
- API endpoint being tested: `PUT /api/admin/users/2`
- Input provided:
```json
{
  "name": "Customer User Updated",
  "phone": "1111111111",
  "address": "Updated Street",
  "is_active": true
}
```
- Expected output: HTTP `200` with updated customer details and unchanged role `customer`
- Actual output: response contains updated fields and `role = "customer"`
- What the test is checking: admins can edit user account details without corrupting the user role
- Why this test is important: admin edits are common, and role stability prevents privilege mistakes

### 6. test_delete_admin_managed_user
- Test case name: `test_delete_admin_managed_user`
- API endpoint being tested: `DELETE /api/admin/users/3`
- Input provided: employee user ID `3`, admin bearer token
- Expected output: HTTP `200` with `{"message": "User deleted"}`
- Actual output: Same as expected
- What the test is checking: admins can remove managed users successfully
- Why this test is important: inactive or duplicate accounts must be removable to keep the system clean and secure

### 7. test_get_my_profile_for_customer
- Test case name: `test_get_my_profile_for_customer`
- API endpoint being tested: `GET /api/profile/me`
- Input provided: customer bearer token
- Expected output: HTTP `200` with customer profile fields including `city = "Jaipur"`
- Actual output: response includes the seeded customer profile and `city = "Jaipur"`
- What the test is checking: logged-in customers can retrieve their own profile accurately
- Why this test is important: profile pages, checkout autofill, and account verification depend on correct self-profile retrieval

### 8. test_update_my_profile_for_customer
- Test case name: `test_update_my_profile_for_customer`
- API endpoint being tested: `PUT /api/profile/me`
- Input provided:
```json
{
  "name": "Customer Prime",
  "phone": "2222222222",
  "address": "Prime Street",
  "city": "Jodhpur",
  "state": "Rajasthan",
  "postal_code": "342001",
  "current_password": "customerpass",
  "new_password": "newcustomerpass"
}
```
- Expected output: HTTP `200` with updated profile fields and unchanged email `customer@example.com`
- Actual output: response includes the updated profile values and the original email
- What the test is checking: customers can update profile details and password while keeping immutable identity fields intact
- Why this test is important: self-service account maintenance reduces admin workload and improves user experience

## Products API

### 9. test_get_products_returns_seeded_catalog
- Test case name: `test_get_products_returns_seeded_catalog`
- API endpoint being tested: `GET /api/products/`
- Input provided: none
- Expected output: HTTP `200` and at least `2` products
- Actual output: list response with length `>= 2`
- What the test is checking: the public catalog endpoint returns the seeded product list
- Why this test is important: customers cannot browse products if catalog retrieval fails

### 10. test_get_product_image_returns_static_file
- Test case name: `test_get_product_image_returns_static_file`
- API endpoint being tested: `GET /api/products/images/default.jpg`
- Input provided: filename `default.jpg`
- Expected output: HTTP `200`
- Actual output: HTTP `200` with an image content type
- What the test is checking: product image files are served correctly from static storage
- Why this test is important: broken image delivery hurts product presentation and user trust

### 11. test_upload_product_image_saves_file
- Test case name: `test_upload_product_image_saves_file`
- API endpoint being tested: `POST /api/products/upload-image`
- Input provided: multipart form upload with file `upload.jpg`, admin bearer token
- Expected output: HTTP `201` with `{"filename": "upload.jpg"}` and the file saved on disk
- Actual output: response returns `upload.jpg` and the file exists in the patched temp directory
- What the test is checking: admin image upload works end-to-end, including filesystem persistence
- Why this test is important: product management usually requires uploading catalog images from an admin panel

### 12. test_get_product_history_returns_entries
- Test case name: `test_get_product_history_returns_entries`
- API endpoint being tested: `GET /api/products/history`
- Input provided: admin bearer token
- Expected output: HTTP `200` and at least `1` history entry
- Actual output: list response with length `>= 1`
- What the test is checking: product change history is retrievable for admins
- Why this test is important: audit trails help teams track catalog edits and investigate mistakes

### 13. test_create_product_as_admin
- Test case name: `test_create_product_as_admin`
- API endpoint being tested: `POST /api/products/`
- Input provided:
```json
{
  "name": "Premium Mug",
  "category": "Cup",
  "price": 22.5,
  "stock": 12,
  "image": "premium.jpg"
}
```
- Expected output: HTTP `201` with `{"message": "Product created"}`
- Actual output: Same as expected
- What the test is checking: admins can add new products to the catalog
- Why this test is important: adding new sellable items is a core inventory and storefront operation

### 14. test_update_product_as_admin
- Test case name: `test_update_product_as_admin`
- API endpoint being tested: `PUT /api/products/1`
- Input provided:
```json
{
  "name": "Updated Kulhad",
  "category": "Kulhad",
  "price": 19.0,
  "image": "updated.jpg"
}
```
- Expected output: HTTP `200` with `{"message": "Product updated"}`
- Actual output: Same as expected
- What the test is checking: admins can update normal editable product fields
- Why this test is important: catalog details like price and image change frequently in real use

### 15. test_update_product_stock_should_persist_new_stock_value
- Test case name: `test_update_product_stock_should_persist_new_stock_value`
- API endpoint being tested: `PUT /api/products/1`
- Input provided:
```json
{
  "stock": 99
}
```
- Expected output: HTTP `200`, and database stock should update to `99`
- Actual output: HTTP `200`, but database stock remains `20`
- What the test is checking: sending only a stock update should persist the new stock quantity
- Why this test is important: stock correction is central to accurate inventory control and order acceptance
- Expected vs actual difference: **Mismatch**
- Bug revealed: the endpoint reports success without updating `stock`, so the API contract is misleading

### 16. test_delete_product_as_admin
- Test case name: `test_delete_product_as_admin`
- API endpoint being tested: `DELETE /api/products/2`
- Input provided: product ID `2`, admin bearer token
- Expected output: HTTP `200` with `{"message": "Product deleted"}`
- Actual output: Same as expected
- What the test is checking: admins can remove products from the catalog
- Why this test is important: discontinued or incorrect products must be removable to prevent bad orders

## Inventory API

### 17. test_get_inventory_returns_product_stock
- Test case name: `test_get_inventory_returns_product_stock`
- API endpoint being tested: `GET /api/inventory/`
- Input provided: admin bearer token
- Expected output: HTTP `200` and at least `2` stock items
- Actual output: list response with length `>= 2`
- What the test is checking: admin inventory view returns product stock records
- Why this test is important: stock monitoring is necessary for purchasing and fulfillment decisions

### 18. test_get_inventory_history_returns_seeded_changes
- Test case name: `test_get_inventory_history_returns_seeded_changes`
- API endpoint being tested: `GET /api/inventory/history`
- Input provided: admin bearer token
- Expected output: HTTP `200` and at least `1` inventory history entry
- Actual output: list response with length `>= 1`
- What the test is checking: inventory change logs are available
- Why this test is important: change history supports traceability and stock reconciliation

### 19. test_adjust_inventory_updates_stock_and_threshold
- Test case name: `test_adjust_inventory_updates_stock_and_threshold`
- API endpoint being tested: `POST /api/inventory/adjust`
- Input provided:
```json
{
  "product_id": 1,
  "type": "add",
  "quantity": 4,
  "reason": "Restock",
  "min_stock": 6
}
```
- Expected output: HTTP `200`, `{"message": "Inventory updated"}`, and product stock becomes `24`
- Actual output: response includes success message and `product.stock = 24`
- What the test is checking: stock adjustments increase quantity and apply a new low-stock threshold
- Why this test is important: restocking workflows must update both current stock and reorder settings

### 20. test_get_raw_inventory_returns_seeded_material
- Test case name: `test_get_raw_inventory_returns_seeded_material`
- API endpoint being tested: `GET /api/inventory/raw`
- Input provided: admin bearer token
- Expected output: HTTP `200` and at least `1` raw material item
- Actual output: list response with length `>= 1`
- What the test is checking: raw material inventory is retrievable
- Why this test is important: manufacturing depends on visibility into material availability

### 21. test_create_raw_material
- Test case name: `test_create_raw_material`
- API endpoint being tested: `POST /api/inventory/raw`
- Input provided:
```json
{
  "name": "Glaze Powder",
  "category": "Glaze",
  "quantity": 40,
  "unit": "kg",
  "reorder_level": 10,
  "cost_per_unit": 8.25,
  "supplier": "Glaze Depot"
}
```
- Expected output: HTTP `201` with created raw material details and `inventory_value = 330.0`
- Actual output: response matches expected values and calculates `inventory_value` correctly
- What the test is checking: raw material creation stores the item and computes total inventory value
- Why this test is important: procurement and costing rely on correct raw-material master data

### 22. test_update_raw_material
- Test case name: `test_update_raw_material`
- API endpoint being tested: `PUT /api/inventory/raw/1`
- Input provided:
```json
{
  "name": "Clay Mix Fine",
  "category": "Clay",
  "quantity": 100,
  "unit": "kg",
  "reorder_level": 30,
  "cost_per_unit": 5.5,
  "supplier": "Soil Suppliers"
}
```
- Expected output: HTTP `200` with updated material details and `supplier = "Soil Suppliers"`
- Actual output: response reflects the updated values and supplier
- What the test is checking: admins can update raw material master data correctly
- Why this test is important: supplier and cost updates affect purchasing and production planning

### 23. test_adjust_raw_material_stock
- Test case name: `test_adjust_raw_material_stock`
- API endpoint being tested: `PUT /api/inventory/raw/1/adjust`
- Input provided:
```json
{
  "adjustment": 15,
  "reason": "Fresh delivery"
}
```
- Expected output: HTTP `200`, `{"message": "Fresh delivery"}`, and material quantity becomes `115.0`
- Actual output: response includes the same message and `material.quantity = 115.0`
- What the test is checking: inbound stock adjustments for raw materials work correctly
- Why this test is important: receiving new supplies must increase available material accurately

### 24. test_delete_raw_material
- Test case name: `test_delete_raw_material`
- API endpoint being tested: `DELETE /api/inventory/raw/1`
- Input provided: raw material ID `1`, admin bearer token
- Expected output: HTTP `200` with `{"message": "Raw material deleted", "id": 1}`
- Actual output: Same as expected
- What the test is checking: raw materials can be deleted successfully
- Why this test is important: obsolete or duplicate material records must be removable

## Orders API

### 25. test_get_checkout_profile
- Test case name: `test_get_checkout_profile`
- API endpoint being tested: `GET /api/orders/checkout-profile`
- Input provided: customer bearer token
- Expected output: HTTP `200` with saved contact/address details and `has_saved_address = true`
- Actual output: response exactly matches the expected checkout profile
- What the test is checking: checkout can prefill a customer's saved profile information
- Why this test is important: prefilling checkout reduces friction and input errors during purchase

### 26. test_update_checkout_profile
- Test case name: `test_update_checkout_profile`
- API endpoint being tested: `PUT /api/orders/checkout-profile`
- Input provided:
```json
{
  "phone": "3333333333",
  "address": "Checkout Street",
  "city": "Udaipur",
  "state": "Rajasthan",
  "postal_code": "313001"
}
```
- Expected output: HTTP `200` with updated checkout profile and unchanged `name = "Customer User"`
- Actual output: response contains updated address fields, `has_saved_address = true`, and original name
- What the test is checking: customers can update checkout-specific saved address details
- Why this test is important: delivery accuracy depends on customers being able to correct shipping information easily

### 27. test_create_order_as_customer
- Test case name: `test_create_order_as_customer`
- API endpoint being tested: `POST /api/orders/`
- Input provided:
```json
{
  "items": [
    {
      "id": 1,
      "qty": 2
    }
  ],
  "phone": "9999999999",
  "address": "Main Street",
  "city": "Jaipur",
  "state": "Rajasthan",
  "postal_code": "302001",
  "payment_method": "Cash on Delivery",
  "shipping": 5
}
```
- Expected output: HTTP `201` with:
```json
{
  "message": "Order placed successfully",
  "status": "Pending",
  "payment": "Pending",
  "method": "Cash on Delivery",
  "amount": 26.0
}
```
and exactly `1` order item
- Actual output: response matches the expected summary and includes one item record
- What the test is checking: customers can place an order and the system calculates payment summary correctly
- Why this test is important: order creation is the main revenue-generating workflow

### 28. test_get_admin_orders
- Test case name: `test_get_admin_orders`
- API endpoint being tested: `GET /api/orders/admin`
- Input provided: admin bearer token
- Expected output: HTTP `200` and at least `1` order in the admin list
- Actual output: list response with length `>= 1`
- What the test is checking: admins can retrieve the order management list
- Why this test is important: operations teams need a complete order queue for fulfillment

### 29. test_get_customer_order_history
- Test case name: `test_get_customer_order_history`
- API endpoint being tested: `GET /api/orders/my-history`
- Input provided: customer bearer token
- Expected output: HTTP `200` and at least `1` order in the customer's history
- Actual output: list response with length `>= 1`
- What the test is checking: customers can view their own order history
- Why this test is important: order history supports tracking, repeat purchase decisions, and customer support

### 30. test_update_admin_order_status
- Test case name: `test_update_admin_order_status`
- API endpoint being tested: `PUT /api/orders/1/status`
- Input provided:
```json
{
  "status": "shipped",
  "payment": "paid"
}
```
- Expected output: HTTP `200` with:
```json
{
  "message": "Order updated",
  "id": 1,
  "status": "Shipped",
  "payment": "Paid"
}
```
- Actual output: Same as expected
- What the test is checking: admins can update fulfillment and payment status for an order
- Why this test is important: order lifecycle tracking is critical for logistics and customer communication

### 31. test_update_bulk_payment_status
- Test case name: `test_update_bulk_payment_status`
- API endpoint being tested: `PUT /api/orders/bulk-payment-status`
- Input provided:
```json
{
  "order_ids": [1],
  "payment": "refunded"
}
```
- Expected output: HTTP `200` with `{"message": "Updated payment status for 1 order(s)"}` and first order payment `Refunded`
- Actual output: response includes the success message and `orders[0].payment = "Refunded"`
- What the test is checking: admins can update payment status for multiple orders in one action
- Why this test is important: bulk operations save time during refunds, reconciliation, and payment correction

## Payroll, Production, And Analytics API

### 32. test_get_payroll_returns_employee_records
- Test case name: `test_get_payroll_returns_employee_records`
- API endpoint being tested: `GET /api/payroll/`
- Input provided: admin bearer token
- Expected output: HTTP `200` and at least `1` payroll record
- Actual output: list response with length `>= 1`
- What the test is checking: payroll listing returns employee payroll data
- Why this test is important: salary processing depends on retrieving current payroll records reliably

### 33. test_update_payroll_record
- Test case name: `test_update_payroll_record`
- API endpoint being tested: `PUT /api/payroll/1`
- Input provided:
```json
{
  "base_salary": 30000,
  "bonus": 1000,
  "deductions": 500,
  "working_days": 20,
  "total_days": 25,
  "status": "paid"
}
```
- Expected output: HTTP `200` with updated payroll values and `net_salary = 24500.0`
- Actual output: response matches the updated values and computes `net_salary = 24500.0`
- What the test is checking: payroll updates correctly calculate final salary after attendance, bonus, and deductions
- Why this test is important: payroll errors directly affect employees and financial records

### 34. test_update_bulk_payroll_status
- Test case name: `test_update_bulk_payroll_status`
- API endpoint being tested: `PUT /api/payroll/bulk-status`
- Input provided:
```json
{
  "status": "processed",
  "current_statuses": ["pending"],
  "month": 4,
  "year": 2026
}
```
- Expected output: HTTP `200` with `{"message": "Updated 1 payroll record(s)"}` and first returned record status `processed`
- Actual output: response includes the success message and `records[0].status = "processed"`
- What the test is checking: admins can bulk-transition payroll records by month/year and prior status
- Why this test is important: batch payroll processing is more practical than updating each employee manually

### 35. test_get_production_entries_for_employee
- Test case name: `test_get_production_entries_for_employee`
- API endpoint being tested: `GET /api/production/entries?month=4&year=2026`
- Input provided: query parameters `month=4`, `year=2026`, employee bearer token
- Expected output: HTTP `200` and at least `1` production entry
- Actual output: list response with length `>= 1`
- What the test is checking: an employee can retrieve production entries for the current month and year
- Why this test is important: workers and supervisors need visibility into production logs for performance tracking

### 36. test_log_production_entry_for_employee
- Test case name: `test_log_production_entry_for_employee`
- API endpoint being tested: `POST /api/production/log`
- Input provided:
```json
{
  "date": "2026-04-03",
  "product": "Kulhad",
  "quantity": 8,
  "method": "manual",
  "entry_type": "manual",
  "status": "present",
  "notes": "Manual logging"
}
```
- Expected output: HTTP `201` with:
```json
{
  "date": "2026-04-03",
  "status": "Present",
  "type": "Manual",
  "kulhad_quantity": 8,
  "cup_quantity": 0,
  "total_quantity": 8,
  "notes": "Manual logging"
}
```
- Actual output: Same as expected, including `total_quantity = 8`
- What the test is checking: an employee can manually log daily production output
- Why this test is important: production records are needed for payroll, reporting, and operational visibility

### 37. test_get_dashboard_summary
- Test case name: `test_get_dashboard_summary`
- API endpoint being tested: `GET /api/analytics/dashboard`
- Input provided: admin bearer token
- Expected output: HTTP `200` with dashboard stats:
```json
{
  "products": 2,
  "orders": 1,
  "customers": 1,
  "employees": 1
}
```
- Actual output: response contains `stats` equal to the expected values
- What the test is checking: dashboard summary aggregates key entity counts correctly
- Why this test is important: summary dashboards are often the first screen management sees and must be trustworthy

### 38. test_get_analytics_summary
- Test case name: `test_get_analytics_summary`
- API endpoint being tested: `GET /api/analytics/summary`
- Input provided: admin bearer token
- Expected output: HTTP `200`, with sales summary showing `total_orders = 1` and `total_revenue = 31.5`
- Actual output: response contains `sales.total_orders = 1` and `sales.total_revenue = 31.5`
- What the test is checking: analytics summary correctly aggregates order count and revenue
- Why this test is important: financial and business decisions depend on accurate sales reporting

## Overall Observations

- The test suite covers authentication, profile management, admin user management, catalog management, product images, inventory, raw materials, ordering, payroll, production logging, and analytics.
- Most tests focus on successful API flows and confirm both HTTP status codes and meaningful business data.
- The only confirmed behavior mismatch is the product stock update case, where the endpoint returns success without persisting the requested stock change.
