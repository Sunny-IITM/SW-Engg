<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { getAdminOrders, updateAdminOrderStatus, updateBulkAdminPaymentStatus } from "../../services/api"
import { getAuthToken } from "../../services/auth"

const orders = ref([])
const searchQuery = ref("")
const selectedTimeRange = ref("All Time")
const selectedPayment = ref("All Payments")
const selectedOrderStatus = ref("All Orders")
const selectedPaymentMethod = ref("All Methods")
const showOrderModal = ref(false)
const selectedOrder = ref(null)
const deliveryStatus = ref("Pending")
const paymentStatus = ref("Pending")
const bulkPaymentStatus = ref("Paid")
const selectedOrderIds = ref([])
const isLoading = ref(true)
const isSaving = ref(false)
const errorMessage = ref("")
let refreshTimer = null

function parseOrderDate(value) {
  if (!value) {
    return new Date(0)
  }

  return new Date(`${value}T00:00:00`)
}

async function loadOrders() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to view orders."
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    orders.value = await getAdminOrders(token)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load orders right now."
  } finally {
    isLoading.value = false
  }
}

async function refreshOrdersInBackground() {
  const token = getAuthToken()
  if (!token || showOrderModal.value || isSaving.value) {
    return
  }

  try {
    orders.value = await getAdminOrders(token)
  } catch {
    // Keep the last successful list visible during background refresh failures.
  }
}

const paymentMethodOptions = computed(() => {
  const uniqueMethods = new Set()
  orders.value.forEach((order) => {
    if (order.method) {
      uniqueMethods.add(order.method)
    }
  })

  return ["All Methods", ...Array.from(uniqueMethods).sort((a, b) => a.localeCompare(b))]
})

const filteredOrders = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const now = new Date()

  return orders.value.filter((order) => {
    const orderDate = parseOrderDate(order.date)
    const timeDiffDays = (now - orderDate) / (1000 * 60 * 60 * 24)

    const matchesSearch =
      query === "" ||
      order.order_number.toLowerCase().includes(query) ||
      order.name.toLowerCase().includes(query) ||
      order.method.toLowerCase().includes(query) ||
      order.payment.toLowerCase().includes(query) ||
      order.status.toLowerCase().includes(query)

    const matchesTime =
      selectedTimeRange.value === "All Time" ||
      (selectedTimeRange.value === "Today" && orderDate.toDateString() === now.toDateString()) ||
      (selectedTimeRange.value === "Last 7 Days" && timeDiffDays <= 7) ||
      (selectedTimeRange.value === "Last 30 Days" && timeDiffDays <= 30)

    const matchesPayment =
      selectedPayment.value === "All Payments" || order.payment === selectedPayment.value

    const matchesStatus =
      selectedOrderStatus.value === "All Orders" || order.status === selectedOrderStatus.value

    const matchesPaymentMethod =
      selectedPaymentMethod.value === "All Methods" || order.method === selectedPaymentMethod.value

    return matchesSearch && matchesTime && matchesPayment && matchesStatus && matchesPaymentMethod
  })
})

const selectedFilteredOrders = computed(() =>
  filteredOrders.value.filter((order) => selectedOrderIds.value.includes(order.id))
)

const stats = computed(() => ([
  { title: "Total Orders", value: filteredOrders.value.length, class: "dark" },
  { title: "Pending", value: filteredOrders.value.filter((o) => o.status === "Pending").length, class: "yellow" },
  { title: "Delivered", value: filteredOrders.value.filter((o) => o.status === "Delivered").length, class: "green" },
  { title: "Cancelled", value: filteredOrders.value.filter((o) => o.status === "Cancelled").length, class: "red" }
]))

function openOrderModal(order) {
  selectedOrder.value = { ...order }
  deliveryStatus.value = order.status
  paymentStatus.value = order.payment
  showOrderModal.value = true
}

async function applyOrderUpdates() {
  if (!selectedOrder.value) {
    return
  }

  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to update orders."
    return
  }

  isSaving.value = true
  errorMessage.value = ""

  try {
    const updated = await updateAdminOrderStatus(selectedOrder.value.id, {
      status: deliveryStatus.value,
      payment: paymentStatus.value
    }, token)
    orders.value = orders.value.map((item) =>
      item.id === updated.id ? { ...item, status: updated.status, payment: updated.payment } : item
    )
    selectedOrder.value = {
      ...selectedOrder.value,
      status: updated.status,
      payment: updated.payment
    }
    showOrderModal.value = false
  } catch (error) {
    errorMessage.value = error.message || "Unable to update order status."
  } finally {
    isSaving.value = false
  }
}

function toggleOrderSelection(orderId) {
  if (selectedOrderIds.value.includes(orderId)) {
    selectedOrderIds.value = selectedOrderIds.value.filter((id) => id !== orderId)
    return
  }

  selectedOrderIds.value = [...selectedOrderIds.value, orderId]
}

function toggleFilteredSelection() {
  const filteredIds = filteredOrders.value.map((order) => order.id)
  const areAllFilteredSelected =
    filteredIds.length > 0 && filteredIds.every((id) => selectedOrderIds.value.includes(id))

  if (areAllFilteredSelected) {
    selectedOrderIds.value = selectedOrderIds.value.filter((id) => !filteredIds.includes(id))
    return
  }

  selectedOrderIds.value = Array.from(new Set([...selectedOrderIds.value, ...filteredIds]))
}

async function applyBulkPaymentUpdate() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to update orders."
    return
  }

  if (selectedFilteredOrders.value.length === 0) {
    errorMessage.value = "Select at least one filtered order."
    return
  }

  isSaving.value = true
  errorMessage.value = ""

  try {
    const response = await updateBulkAdminPaymentStatus({
      order_ids: selectedFilteredOrders.value.map((order) => order.id),
      payment: bulkPaymentStatus.value
    }, token)

    const paymentMap = new Map(response.orders.map((order) => [order.id, order.payment]))
    orders.value = orders.value.map((order) =>
      paymentMap.has(order.id)
        ? { ...order, payment: paymentMap.get(order.id) }
        : order
    )
    selectedOrderIds.value = []
  } catch (error) {
    errorMessage.value = error.message || "Unable to update payment status."
  } finally {
    isSaving.value = false
  }
}

function startAutoRefresh() {
  refreshOrdersInBackground()
  refreshTimer = window.setInterval(refreshOrdersInBackground, 10000)
  window.addEventListener("focus", refreshOrdersInBackground)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
  window.removeEventListener("focus", refreshOrdersInBackground)
}

onMounted(() => {
  loadOrders()
  startAutoRefresh()
})

onBeforeUnmount(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="orders">
    <div class="page-header">
      <div class="page-copy">
        <h1>Order Management</h1>
        <p>Track and manage all customer orders</p>
      </div>
    </div>

    <div v-if="errorMessage" class="notice error">
      {{ errorMessage }}
    </div>

    <div v-if="isLoading" class="notice">
      Loading orders from the backend...
    </div>

    <template v-else>
      <div class="stats">
        <div v-for="s in stats" :key="s.title" :class="['stat-card', s.class]">
          <p>{{ s.title }}</p>
          <h2>{{ s.value }}</h2>
        </div>
      </div>

      <div class="filters">
        <input v-model="searchQuery" placeholder="Search orders, customers..." />
        <select v-model="selectedTimeRange">
          <option>All Time</option>
          <option>Today</option>
          <option>Last 7 Days</option>
          <option>Last 30 Days</option>
        </select>
        <select v-model="selectedPayment">
          <option>All Payments</option>
          <option>Paid</option>
          <option>Pending</option>
        </select>
        <select v-model="selectedOrderStatus">
          <option>All Orders</option>
          <option>Pending</option>
          <option>Delivered</option>
          <option>Cancelled</option>
        </select>
        <select v-model="selectedPaymentMethod">
          <option v-for="method in paymentMethodOptions" :key="method">{{ method }}</option>
        </select>
      </div>

      <div v-if="filteredOrders.length" class="bulk-bar">
        <label class="bulk-check">
          <input
            type="checkbox"
            :checked="filteredOrders.length > 0 && filteredOrders.every((order) => selectedOrderIds.includes(order.id))"
            @change="toggleFilteredSelection"
          />
          <span>Select Filtered</span>
        </label>

        <div class="bulk-actions">
          <select v-model="bulkPaymentStatus">
            <option>Paid</option>
            <option>Pending</option>
            <option>Failed</option>
            <option>Refunded</option>
          </select>
          <button type="button" class="bulk-btn" :disabled="isSaving || selectedFilteredOrders.length === 0" @click="applyBulkPaymentUpdate">
            {{ isSaving ? "Updating..." : `Update ${selectedFilteredOrders.length} Selected` }}
          </button>
        </div>
      </div>

      <div v-if="filteredOrders.length === 0" class="empty-state">
        No orders found.
      </div>

      <div v-else class="list">
        <div class="order-card" v-for="o in filteredOrders" :key="o.id">
          <div class="select-col">
            <input
              type="checkbox"
              :checked="selectedOrderIds.includes(o.id)"
              @change="toggleOrderSelection(o.id)"
            />
          </div>

          <div class="left">
            <div class="top">
              <h3>{{ o.order_number }}</h3>
              <div class="badge-group">
                <small>Delivery Status</small>
                <span class="badge status" :class="o.status.toLowerCase()">{{ o.status }}</span>
              </div>
              <div class="badge-group">
                <small>Payment Status</small>
                <span class="badge payment" :class="o.payment.toLowerCase()">{{ o.payment }}</span>
              </div>
            </div>

            <p class="user">{{ o.name }}</p>
            <p class="method">{{ o.method }}</p>
            <p class="amount">Rs {{ o.amount }}</p>
          </div>

          <div class="middle">
            <p>{{ o.date || "-" }}</p>
            <p>{{ o.item_count }} item(s)</p>
          </div>

          <div class="right">
            <button type="button" class="view" @click="openOrderModal(o)">View Details</button>
          </div>
        </div>
      </div>
    </template>

    <div v-if="showOrderModal && selectedOrder" class="modal" @click="showOrderModal = false">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <h2>Order Details</h2>
          <button type="button" class="close" @click="showOrderModal = false">&times;</button>
        </div>

        <div class="order-summary">
          <div>
            <h3>{{ selectedOrder.order_number }}</h3>
            <p>{{ selectedOrder.date || "-" }}</p>
          </div>

          <div class="badges">
            <div class="badge-group">
              <small>Delivery Status</small>
              <span class="badge status" :class="selectedOrder.status.toLowerCase()">
                {{ selectedOrder.status }}
              </span>
            </div>
            <div class="badge-group">
              <small>Payment Status</small>
              <span class="badge payment-badge" :class="selectedOrder.payment.toLowerCase()">
                {{ selectedOrder.payment }}
              </span>
            </div>
          </div>
        </div>

        <h4 class="section-title">Customer Information</h4>
        <div class="detail-card">
          <p><span>Name</span>{{ selectedOrder.name }}</p>
          <p><span>Email</span>{{ selectedOrder.email || "Not available" }}</p>
          <p><span>Phone</span>{{ selectedOrder.phone || "Not available" }}</p>
          <p><span>Delivery Address</span>{{ selectedOrder.address || "Not available" }}</p>
        </div>

        <h4 class="section-title">Order Items</h4>
        <div class="detail-card">
          <div v-if="selectedOrder.items.length === 0" class="empty-inline">No order items available.</div>
          <div class="item" v-for="item in selectedOrder.items" :key="`${selectedOrder.id}-${item.name}`">
            <div>
              <strong>{{ item.name }}</strong>
              <p>Quantity: {{ item.quantity }}</p>
            </div>
            <div class="item-right">
              Rs {{ item.subtotal }}
            </div>
          </div>
        </div>

        <div class="divider"></div>

        <div class="payment-row">
          <p>Payment Method:</p>
          <strong>{{ selectedOrder.method }}</strong>
        </div>

        <div class="total">
          <p>Total Amount:</p>
          <h2>Rs {{ selectedOrder.amount }}</h2>
        </div>

        <div class="divider"></div>

        <h4 class="section-title">Update Order Status</h4>

        <div class="status-row">
          <div>
            <label>Delivery Status</label>
            <select v-model="deliveryStatus">
              <option>Pending</option>
              <option>Delivered</option>
              <option>Cancelled</option>
            </select>
          </div>

          <div>
            <label>Payment Status</label>
            <select v-model="paymentStatus">
              <option>Pending</option>
              <option>Paid</option>
              <option>Failed</option>
              <option>Refunded</option>
            </select>
          </div>
        </div>

        <div class="actions">
          <button type="button" class="submit" :disabled="isSaving" @click="applyOrderUpdates">
            {{ isSaving ? "Saving..." : "Apply Changes" }}
          </button>
          <button type="button" class="cancel" @click="showOrderModal = false">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.orders {
  padding: 30px 50px;
  background: #f3ead8;
  min-height: 100vh;
  box-sizing: border-box;
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 25px;
}

.page-copy h1 {
  margin: 0 0 6px;
}

.page-copy p {
  margin: 0;
  color: #666;
}

.notice {
  padding: 14px 16px;
  border-radius: 10px;
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fdba74;
  margin-bottom: 20px;
}

.notice.error {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fca5a5;
}

.empty-state,
.empty-inline {
  padding: 14px;
  border-radius: 10px;
  background: #faf4ea;
  color: #7c6a58;
}

.stats {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  padding: 18px;
  border-radius: 14px;
  color: white;
  box-shadow: 0 6px 12px rgba(0,0,0,0.1);
}

.stat-card h2 {
  font-size: 24px;
}

.dark { background: linear-gradient(#4b5563, #374151); }
.yellow { background: linear-gradient(#f59e0b, #d97706); }
.blue { background: linear-gradient(#3b82f6, #2563eb); }
.purple { background: linear-gradient(#a855f7, #7e22ce); }
.green { background: linear-gradient(#22c55e, #16a34a); }
.red { background: linear-gradient(#ef4444, #dc2626); }

.filters {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.filters input,
.filters select,
.status-row input,
.bulk-actions select {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #ddd;
  background: white;
}

.bulk-bar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 18px;
  padding: 14px 16px;
  border-radius: 12px;
  background: #fff7ed;
  border: 1px solid #fdba74;
}

.bulk-check {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #7c2d12;
  font-weight: 600;
}

.bulk-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.bulk-btn {
  padding: 12px 16px;
  border: none;
  border-radius: 10px;
  background: #8b4513;
  color: white;
  font-weight: 700;
}

.bulk-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.order-card {
  background: #f8f6f2;
  padding: 20px;
  border-radius: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 6px 12px rgba(0,0,0,0.08);
}

.select-col {
  width: 32px;
  display: flex;
  justify-content: center;
}

.left {
  width: 35%;
}

.top {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}

.top h3 {
  margin: 0;
  font-size: 20px;
  line-height: 1.2;
}

.badge-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.badge-group small {
  font-size: 11px;
  color: #6b7280;
}

.badge {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
}

.status.pending { background: #f59e0b; color: white; }
.status.confirmed { background: #2563eb; color: white; }
.status.shipped { background: #7c3aed; color: white; }
.status.delivered { background: #16a34a; color: white; }
.status.cancelled { background: #dc2626; color: white; }

.payment.paid,
.payment-badge.paid { background: #22c55e; color: white; }
.payment.pending,
.payment-badge.pending { background: #f59e0b; color: white; }

.user,
.method {
  margin: 0;
  color: #555;
}

.user {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.method {
  margin-top: 4px;
  font-size: 14px;
}

.amount {
  margin: 10px 0 0;
  font-size: 15px;
  font-weight: 500;
  color: #8b4513;
}

.middle {
  width: 30%;
  color: #555;
}

.right {
  width: 25%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
}

.view {
  padding: 8px 12px;
  border-radius: 8px;
  background: white;
  border: 1px solid #ddd;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  z-index: 1000;
}

.modal-box {
  width: min(620px, 100%);
  max-height: calc(100vh - 40px);
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  color: #8b4513;
}

.close {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 24px;
  line-height: 1;
  padding: 0;
}

.order-summary {
  display: flex;
  justify-content: space-between;
  background: #f5efe6;
  border: 1px solid #e6c77c;
  padding: 14px;
  border-radius: 10px;
}

.order-summary h3,
.order-summary p {
  margin: 0;
}

.order-summary p {
  margin-top: 6px;
  color: #555;
}

.badges {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.section-title {
  margin: 0;
  font-size: 15px;
  color: #333;
}

.detail-card {
  background: #f7f7f7;
  padding: 14px;
  border-radius: 10px;
}

.detail-card p {
  margin: 6px 0;
}

.detail-card span {
  display: block;
  font-size: 12px;
  color: #777;
}

.item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.item-right {
  text-align: right;
}

.divider {
  height: 1px;
  background: #ddd;
}

.payment-row,
.total {
  display: flex;
  justify-content: space-between;
}

.total {
  align-items: center;
}

.total h2 {
  color: #8b4513;
  margin: 0;
}

.status-row {
  display: flex;
  gap: 12px;
}

.status-row div {
  flex: 1;
}

label {
  font-size: 13px;
  margin-bottom: 4px;
  display: block;
}

.modal-box select {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.cancel {
  background: #eee;
  padding: 10px 14px;
  border-radius: 8px;
}

.submit {
  background: #8b4513;
  color: white;
  padding: 10px 14px;
  border-radius: 8px;
  margin-right: 10px;
}

@media (max-width: 1200px) {
  .stats {
    grid-template-columns: repeat(3, 1fr);
  }

  .order-card {
    gap: 18px;
    align-items: flex-start;
    flex-direction: column;
  }

  .left,
  .middle,
  .right {
    width: 100%;
  }

  .right {
    align-items: flex-start;
  }
}

@media (max-width: 900px) {
  .orders {
    padding: 24px;
  }

  .filters {
    grid-template-columns: 1fr;
  }

  .bulk-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .bulk-actions {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 640px) {
  .orders {
    padding: 20px;
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .top,
  .order-summary,
  .item,
  .payment-row,
  .total,
  .status-row {
    gap: 12px;
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>

