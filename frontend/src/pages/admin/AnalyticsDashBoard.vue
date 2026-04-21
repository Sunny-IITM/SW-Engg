<script setup>
import { computed, onMounted, ref } from "vue"
import { getAnalyticsSummary } from "../../services/api"
import { getAuthToken } from "../../services/auth"
import SalesAnalytics from "./SalesAnalytics.vue"
import Inventory from "./Inventory.vue"
import Payments from "./Payments.vue"

const activeTab = ref("sales")
const isLoading = ref(true)
const errorMessage = ref("")
const summary = ref({
  sales: null,
  inventory: null,
  payments: null
})

const tabs = computed(() => ({
  sales: { component: SalesAnalytics, props: { data: summary.value.sales } },
  inventory: { component: Inventory, props: { data: summary.value.inventory } },
  payments: { component: Payments, props: { data: summary.value.payments } }
}))

async function loadAnalytics() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to view analytics."
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    summary.value = await getAnalyticsSummary(token)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load analytics right now."
  } finally {
    isLoading.value = false
  }
}

onMounted(loadAnalytics)
</script>

<template>
  <div class="analytics-dashboard">
    <div class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'sales' }" @click="activeTab = 'sales'">Sales</button>
      <button class="tab-btn" :class="{ active: activeTab === 'inventory' }" @click="activeTab = 'inventory'">Inventory</button>
      <button class="tab-btn" :class="{ active: activeTab === 'payments' }" @click="activeTab = 'payments'">Payments</button>
    </div>

    <div v-if="errorMessage" class="notice error">
      {{ errorMessage }}
    </div>

    <div v-else-if="isLoading" class="notice">
      Loading analytics from the backend...
    </div>

    <component
      v-else
      :is="tabs[activeTab].component"
      v-bind="tabs[activeTab].props"
    />
  </div>
</template>

<style scoped>
.analytics-dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tabs {
  display: flex;
  width: 100%;
  padding: 6px;
  background: #e9ecef;
  border-radius: 12px;
  box-shadow: inset 0 0 0 1px rgba(11, 15, 26, 0.04);
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  border-radius: 10px;
  font-weight: 500;
  cursor: pointer;
}

.tab-btn.active {
  background: white;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.notice {
  padding: 14px 16px;
  border-radius: 10px;
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fdba74;
}

.notice.error {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fca5a5;
}

@media (max-width: 576px) {
  .tabs {
    flex-direction: column;
  }
}
</style>
