<script setup>
import { computed, onMounted, ref } from "vue"
import { getAdminDashboard } from "../../services/api"
import { getAuthToken } from "../../services/auth"

const isLoading = ref(true)
const errorMessage = ref("")
const dashboard = ref({
  stats: {
    products: 0,
    orders: 0,
    customers: 0,
    employees: 0
  },
  low_stock: [],
  recent_orders: []
})

const statCards = computed(() => [
  {
    key: "products",
    label: "Total Products",
    value: dashboard.value.stats.products,
    color: "blue",
    iconPaths: [
      "M12 3 4 7.5 12 12l8-4.5L12 3Z",
      "M4 7.5V16.5L12 21l8-4.5V7.5",
      "M12 12v9"
    ]
  },
  {
    key: "orders",
    label: "Total Orders",
    value: dashboard.value.stats.orders,
    color: "green",
    iconPaths: [
      "M3 5h2l2.2 10.2a1 1 0 0 0 1 .8h8.8a1 1 0 0 0 1-.8L21 8H7",
      "M9 19a1.5 1.5 0 1 1 0 .01",
      "M17 19a1.5 1.5 0 1 1 0 .01"
    ]
  },
  {
    key: "customers",
    label: "Customers",
    value: dashboard.value.stats.customers,
    color: "purple",
    iconPaths: [
      "M16 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z",
      "M8 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z",
      "M2.5 19a4.5 4.5 0 0 1 9 0",
      "M12.5 19a4.5 4.5 0 0 1 9 0"
    ]
  },
  {
    key: "employees",
    label: "Employees",
    value: dashboard.value.stats.employees,
    color: "orange",
    iconPaths: [
      "M12 12a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z",
      "M6 20a6 6 0 0 1 12 0",
      "M9 7h6",
      "M10 4h4v2h-4z"
    ]
  }
])

async function loadDashboard() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to view dashboard analytics."
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    dashboard.value = await getAdminDashboard(token)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load dashboard right now."
  } finally {
    isLoading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="dashboard-content">
    <div class="page-header">
      <div class="page-copy">
        <h1>Dashboard</h1>
        <p>Welcome back, Admin! Here's what's happening today.</p>
      </div>
    </div>

    <div v-if="errorMessage" class="notice error">
      {{ errorMessage }}
    </div>

    <div v-else-if="isLoading" class="notice">
      Loading dashboard from the backend...
    </div>

    <template v-else>
      <div class="stats">
        <div v-for="card in statCards" :key="card.key" class="card">
          <div class="icon" :class="card.color">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                v-for="(iconPath, index) in card.iconPaths"
                :key="`${card.key}-${index}`"
                :d="iconPath"
              />
            </svg>
          </div>
          <div class="content">
            <p>{{ card.label }}</p>
            <div class="value-row">
              <h2>{{ card.value }}</h2>
            </div>
          </div>
        </div>
      </div>

      <div class="grid">
        <div class="panel">
          <div class="panel-header">
            <h3>Low Stock Alert</h3>
            <router-link to="/admin/inventory">View All</router-link>
          </div>

          <div v-if="dashboard.low_stock.length === 0" class="empty-state">
            No low stock products right now.
          </div>

          <div v-for="product in dashboard.low_stock" :key="product.id" class="alert-item">
            <div>
              <strong>{{ product.name }}</strong>
              <p>Min stock: {{ product.min_stock }}</p>
            </div>
            <span class="danger">{{ product.stock }}</span>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h3>Recent Orders</h3>
            <router-link to="/admin/orders">View All</router-link>
          </div>

          <div v-if="dashboard.recent_orders.length === 0" class="empty-state">
            No recent orders available.
          </div>

          <div v-for="order in dashboard.recent_orders" :key="order.id" class="order">
            <div>
              <strong>#{{ order.order_number }}</strong>
              <p>{{ order.customer_name }}</p>
            </div>
            <div class="right">
              <strong>Rs {{ order.amount }}</strong>
              <span class="status" :class="order.status.toLowerCase()">{{ order.status }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="quick">
        <router-link to="/admin/products" class="action brown">
          <h3>Add Product</h3>
          <p>Manage catalog</p>
        </router-link>

        <router-link to="/admin/orders" class="action green">
          <h3>Process Orders</h3>
          <p>Update status</p>
        </router-link>

        <router-link to="/admin/employees" class="action orange">
          <h3>Manage Staff</h3>
          <p>Add employees</p>
        </router-link>

        <router-link to="/admin/customers" class="action purple">
          <h3>View Customers</h3>
          <p>Customer data</p>
        </router-link>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard-content {
  box-sizing: border-box;
  width: 100%;
  padding: 30px 50px;
  background: #f3ead8;
  min-height: 100vh;
}

.page-header {
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

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin: 25px 0;
}

.card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  padding: 18px 20px;
  border-radius: 14px;
  box-shadow: 0 6px 14px rgba(0,0,0,0.08);
}

.icon {
  flex: 0 0 52px;
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.icon svg {
  width: 26px;
  height: 26px;
  stroke: currentColor;
  stroke-width: 1.8;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.blue { background: #3b82f6; }
.green { background: #16a34a; }
.purple { background: #9333ea; }
.orange { background: #ea580c; }

.content p {
  font-size: 13px;
  color: #666;
  margin: 0;
}

.content {
  min-width: 0;
  flex: 1;
  text-align: center;
}

.value-row h2 {
  margin: 2px 0 0;
  font-size: 24px;
}

.value-row {
  display: flex;
  justify-content: center;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.panel {
  background: white;
  padding: 20px;
  border-radius: 12px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  gap: 16px;
}

.panel-header a {
  color: #8b4513;
  text-decoration: none;
  font-weight: 600;
}

.empty-state {
  padding: 12px;
  border-radius: 10px;
  background: #faf4ea;
  color: #7c6a58;
}

.alert-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #f5c6cb;
  border-radius: 10px;
  margin-bottom: 10px;
}

.danger {
  color: red;
  font-weight: bold;
}

.order {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 10px;
  margin-bottom: 10px;
  gap: 14px;
}

.status {
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.pending { background: #fde68a; }
.completed { background: #bbf7d0; }
.cancelled { background: #fecaca; }

.quick {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.action {
  display: block;
  padding: 20px;
  border-radius: 12px;
  color: white;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.action:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.12);
}

.action h3,
.action p {
  margin: 0;
}

.action p {
  margin-top: 6px;
}

.brown { background: #8b4513; }
.green { background: #0f9d58; }
.orange { background: #e65100; }
.purple { background: #7b1fa2; }

@media (max-width: 1200px) {
  .stats, .quick {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .dashboard-content {
    padding: 24px;
  }

  .grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .dashboard-content {
    padding: 20px;
  }

  .stats, .quick {
    grid-template-columns: 1fr;
  }
}
</style>
