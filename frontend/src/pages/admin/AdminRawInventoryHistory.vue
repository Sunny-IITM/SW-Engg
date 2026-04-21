<script setup>
import { onMounted, ref } from "vue"
import { getRawInventoryHistory } from "../../services/api"
import { getAuthToken } from "../../services/auth"

const isLoading = ref(true)
const errorMessage = ref("")
const history = ref([])

function formatQuantity(value, unit) {
  const amount = Number(value || 0)
  const normalized = Number.isInteger(amount) ? amount.toString() : amount.toFixed(2).replace(/\.?0+$/, "")
  return `${normalized} ${unit || ""}`.trim()
}

async function loadHistory() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to view raw inventory history."
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    history.value = await getRawInventoryHistory(token)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load raw inventory history right now."
  } finally {
    isLoading.value = false
  }
}

onMounted(loadHistory)
</script>

<template>
  <div class="history-page">
    <div class="page-header">
      <div class="page-copy">
        <h1>Raw Inventory Log History</h1>
        <p>Track raw material creation, adjustments, updates, and deletions.</p>
      </div>
    </div>

    <div class="tabs">
      <router-link to="/admin/raw-inventory" class="tab">
        Raw Inventory
      </router-link>
      <router-link to="/admin/raw-inventory/history" class="tab active">
        Log History
      </router-link>
    </div>

    <div v-if="errorMessage" class="notice error">
      {{ errorMessage }}
    </div>

    <div v-else-if="isLoading" class="notice">
      Loading raw inventory history from the backend...
    </div>

    <div v-else class="panel">
      <div v-if="history.length === 0" class="empty-state">No raw inventory log history yet.</div>

      <div v-for="h in history" :key="h.id" class="item">
        <div class="left">
          <div :class="['icon', h.type === 'create' ? 'green' : h.type === 'delete' ? 'red' : h.change > 0 ? 'green' : h.change < 0 ? 'red' : 'amber']">
            {{
              h.type === "create"
                ? "+"
                : h.type === "delete"
                  ? "-"
                  : h.change > 0
                    ? "+"
                    : h.change < 0
                      ? "-"
                      : "?"
            }}
          </div>

          <div class="content">
            <h3>{{ h.name }}</h3>
            <p class="desc">{{ h.desc }}</p>

            <div class="meta">
              {{ h.date }} - By {{ h.by }}
              <span class="badge">{{ h.type }}</span>
            </div>
          </div>
        </div>

        <div class="right">
          <h3 :class="h.type === 'create' || h.change > 0 ? 'green-text' : h.type === 'delete' || h.change < 0 ? 'red-text' : 'amber-text'">
            {{ h.change > 0 ? "+" : "" }}{{ formatQuantity(h.change, h.unit) }}
          </h3>
          <p class="range">
            {{ formatQuantity(h.from, h.unit) }} -> {{ formatQuantity(h.to, h.unit) }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-page {
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

.tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 20px;
  border-radius: 20px;
  background: #ddd;
  color: inherit;
  text-decoration: none;
}

.tab.active {
  background: white;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
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

.panel {
  background: #f8f6f2;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.08);
}

.empty-state {
  color: #777;
  text-align: center;
  padding: 20px;
}

.item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-radius: 12px;
  margin-bottom: 14px;
  background: #f1f1f1;
  transition: 0.2s;
}

.item:hover {
  transform: translateY(-2px);
}

.left {
  display: flex;
  align-items: center;
  gap: 15px;
  min-width: 0;
}

.icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
}

.green {
  background: #dcfce7;
  color: #16a34a;
}

.amber {
  background: #fef3c7;
  color: #d97706;
}

.red {
  background: #fee2e2;
  color: #dc2626;
}

.content h3 {
  margin-bottom: 3px;
}

.desc {
  font-size: 13px;
  color: #555;
}

.meta {
  font-size: 12px;
  color: #777;
  margin-top: 4px;
}

.badge {
  background: #e5e7eb;
  padding: 2px 8px;
  border-radius: 6px;
  margin-left: 6px;
  text-transform: capitalize;
}

.right {
  text-align: right;
}

.green-text {
  color: #16a34a;
}

.amber-text {
  color: #d97706;
}

.red-text {
  color: #dc2626;
}

.range {
  font-size: 12px;
  color: #777;
}

@media (max-width: 900px) {
  .history-page {
    padding: 24px;
  }

  .item {
    gap: 16px;
    align-items: flex-start;
    flex-direction: column;
  }

  .right {
    text-align: left;
  }
}

@media (max-width: 640px) {
  .history-page {
    padding: 20px;
  }

  .tabs {
    flex-wrap: wrap;
  }

  .left {
    align-items: flex-start;
  }
}
</style>
