<script setup>
import { computed, onMounted, ref } from "vue"
import { adjustInventory, getInventoryHistory, getInventoryProducts } from "../../services/api"
import { getAuthToken } from "../../services/auth"

const activeTab = ref("products")
const showStockModal = ref(false)
const selectedProduct = ref(null)
const type = ref("add")
const quantity = ref(0)
const reason = ref("")
const minStock = ref(0)
const searchQuery = ref("")
const selectedCategory = ref("All")
const selectedStock = ref("All")
const isLoading = ref(true)
const isSubmitting = ref(false)
const errorMessage = ref("")
const modalErrorMessage = ref("")
const products = ref([])
const history = ref([])

const categoryOptions = computed(() => {
  return ["All", ...new Set(products.value.map((product) => product.category))]
})

const filteredProducts = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return products.value.filter((product) => {
    const matchesSearch =
      query === "" ||
      product.name.toLowerCase().includes(query) ||
      product.category.toLowerCase().includes(query)

    const matchesCategory =
      selectedCategory.value === "All" || product.category === selectedCategory.value

    const isLowStock = product.stock < product.min_stock
    const matchesStock =
      selectedStock.value === "All" ||
      (selectedStock.value === "Low Stock" && isLowStock) ||
      (selectedStock.value === "Sufficient Stock" && !isLowStock)

    return matchesSearch && matchesCategory && matchesStock
  })
})

async function loadInventory() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to view inventory."
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    const [inventoryProducts, inventoryHistory] = await Promise.all([
      getInventoryProducts(token),
      getInventoryHistory(token)
    ])

    products.value = inventoryProducts
    history.value = inventoryHistory
  } catch (error) {
    errorMessage.value = error.message || "Unable to load inventory right now."
  } finally {
    isLoading.value = false
  }
}

function openStockModal(product) {
  selectedProduct.value = product
  showStockModal.value = true
  type.value = "add"
  quantity.value = 0
  reason.value = ""
  minStock.value = product.min_stock
  modalErrorMessage.value = ""
}

async function applyStock() {
  if (!selectedProduct.value) {
    return
  }

  const currentStock = Number(selectedProduct.value.stock || 0)
  const hasQuantityChange = Number(quantity.value) > 0
  const hasMinStockChange = selectedProduct.value && Number(minStock.value) !== Number(selectedProduct.value.min_stock)

  if (!hasQuantityChange && !hasMinStockChange) {
    modalErrorMessage.value = "Update quantity or minimum stock to save changes."
    return
  }

  if (type.value === "remove" && currentStock <= 0 && hasQuantityChange) {
    modalErrorMessage.value = "Stock is empty. Cannot remove stock."
    return
  }

  if (type.value === "remove" && Number(quantity.value) > currentStock) {
    modalErrorMessage.value = `Only ${currentStock} item(s) available in stock.`
    return
  }

  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to adjust inventory."
    return
  }

  isSubmitting.value = true
  modalErrorMessage.value = ""

  try {
    const response = await adjustInventory({
      product_id: selectedProduct.value.id,
      type: type.value,
      quantity: quantity.value,
      reason: reason.value,
      min_stock: minStock.value
    }, token)

    products.value = products.value.map((product) =>
      product.id === response.product.id ? response.product : product
    )

    await loadInventory()
    showStockModal.value = false
  } catch (error) {
    modalErrorMessage.value = error.message || "Unable to update inventory."
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadInventory)
</script>

<template>
  <div class="inventory">
    <div class="page-header">
      <div class="page-copy">
        <h1>Inventory Management</h1>
        <p>Manage product stock levels with live backend data.</p>
      </div>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: activeTab === 'products' }" @click="activeTab = 'products'">
        Products
      </button>
      <button class="tab" :class="{ active: activeTab === 'history' }" @click="activeTab = 'history'">
        Stock History
      </button>
    </div>

    <div v-if="errorMessage" class="notice error">
      {{ errorMessage }}
    </div>

    <div v-if="isLoading" class="notice">
      Loading inventory from the backend...
    </div>

    <template v-else>
      <div v-if="activeTab === 'products'">
        <div class="filters">
          <input v-model="searchQuery" placeholder="Search products..." />
          <select v-model="selectedCategory">
            <option v-for="category in categoryOptions" :key="category" :value="category">
              {{ category === "All" ? "All Categories" : category }}
            </option>
          </select>
          <select v-model="selectedStock">
            <option value="All">All Stock</option>
            <option value="Low Stock">Low Stock</option>
            <option value="Sufficient Stock">Sufficient Stock</option>
          </select>
        </div>

        <div class="grid">
          <div class="card" v-for="product in filteredProducts" :key="product.id">
            <div class="card-top">
              <h3>{{ product.name }}</h3>
              <span :class="product.stock <= 0 ? 'out' : product.stock < product.min_stock ? 'low' : 'ok'">
                {{ product.stock <= 0 ? "Out of Stock" : product.stock < product.min_stock ? "Low Stock" : "In Stock" }}
              </span>
            </div>

            <span class="category">{{ product.category }}</span>

            <div class="info">
              <p><span>Stock:</span> {{ product.stock }} units</p>
              <p><span>Min Stock:</span> {{ product.min_stock }} units</p>
              <p><span>Price:</span> Rs {{ product.price }}</p>
            </div>

            <div class="actions">
              <button class="adjust" @click="openStockModal(product)">Adjust</button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="panel">
        <div v-if="history.length === 0" class="empty-state">No stock history yet.</div>

        <div class="item" v-for="entry in history" :key="entry.id">
          <div class="left">
            <div :class="['history-icon', entry.change > 0 ? 'green' : 'red']">
              {{ entry.change > 0 ? "+" : "-" }}
            </div>

            <div class="content">
              <h3>{{ entry.name }}</h3>
              <p class="desc">{{ entry.desc }}</p>

              <div class="meta">
                {{ entry.date }} - By {{ entry.by }}
                <span class="badge">{{ entry.type }}</span>
              </div>
            </div>
          </div>

          <div class="right">
            <h3 :class="entry.change > 0 ? 'green-text' : 'red-text'">
              {{ entry.change > 0 ? "+" : "" }}{{ entry.change }} units
            </h3>
            <p class="range">{{ entry.from }} -> {{ entry.to }}</p>
          </div>
        </div>
      </div>
    </template>

    <div v-if="showStockModal" class="modal" @click="showStockModal = false">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <h3>Adjust Stock</h3>
          <button type="button" class="close-btn" @click="showStockModal = false">&times;</button>
        </div>

        <div v-if="selectedProduct" class="product-info">
          <strong>{{ selectedProduct.name }}</strong>
          <p>Current stock: {{ selectedProduct.stock }} units</p>
        </div>

        <div class="field-group">
          <span class="field-label">Adjustment Type</span>
          <div class="toggle">
            <button class="add" :class="{ active: type === 'add' }" @click="type = 'add'">
              Add Stock
            </button>
            <button class="remove" :class="{ active: type === 'remove' }" @click="type = 'remove'">
              Remove Stock
            </button>
          </div>
        </div>

        <div class="field-group">
          <span class="field-label">Quantity</span>
          <input v-model.number="quantity" type="number" min="0" placeholder="Leave 0 to only update minimum stock" />
        </div>

        <div class="field-group">
          <span class="field-label">Reason</span>
          <textarea v-model="reason" placeholder="Reason for adjustment"></textarea>
        </div>

        <div class="field-group">
          <span class="field-label">Minimum Stock</span>
          <input v-model.number="minStock" type="number" min="0" placeholder="Minimum stock threshold" />
          <small class="field-help">You can update this without changing the current stock quantity.</small>
        </div>

        <div v-if="modalErrorMessage" class="notice error modal-notice">
          {{ modalErrorMessage }}
        </div>

        <div class="modal-actions">
          <button class="submit" :disabled="isSubmitting" @click="applyStock">
            {{ isSubmitting ? "Saving..." : "Apply" }}
          </button>
          <button class="cancel" :disabled="isSubmitting" @click="showStockModal = false">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventory {
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

.modal-notice {
  margin-bottom: 0;
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
  border: none;
}

.tab.active {
  background: white;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.filters {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 15px;
  margin-bottom: 25px;
}

.filters input,
.filters select {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #ddd;
  background: white;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.card {
  background: white;
  padding: 22px;
  border-radius: 14px;
  box-shadow: 0 6px 14px rgba(0,0,0,0.08);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.low {
  background: #facc15;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
}

.ok {
  background: #22c55e;
  color: white;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
}

.out {
  background: #fee2e2;
  color: #b42318;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
}

.category {
  display: inline-block;
  background: #f1f1f1;
  padding: 4px 10px;
  border-radius: 8px;
  margin: 10px 0;
}

.info {
  margin: 10px 0;
}

.info span {
  color: #777;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.adjust {
  flex: 1;
  padding: 10px;
  border-radius: 10px;
  background: #f1f1f1;
}

.panel {
  background: #f8f6f2;
  padding: 20px;
  border-radius: 16px;
  box-shadow: 0 8px 18px rgba(0,0,0,0.08);
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

.history-icon {
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
}

.right {
  text-align: right;
}

.green-text {
  color: #16a34a;
}

.red-text {
  color: #dc2626;
}

.range {
  font-size: 12px;
  color: #777;
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
  width: min(420px, 100%);
  background: white;
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
  padding: 0;
}

.product-info {
  background: #f3ead8;
  border: 1px solid #e0c97f;
  padding: 12px;
  border-radius: 10px;
}

.product-info p {
  margin: 6px 0 0;
  color: #666;
}

.toggle {
  display: flex;
  gap: 10px;
}

.toggle button {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  background: #eee;
}

.toggle .add.active {
  background: #16a34a;
  color: white;
}

.toggle .remove.active {
  background: #dc2626;
  color: white;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: #5f3817;
}

.field-help {
  color: #7c6a58;
  font-size: 12px;
}

.modal-box input,
.modal-box textarea {
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.modal-box textarea {
  min-height: 90px;
  resize: vertical;
}

.modal-actions {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.submit {
  background: #8b4513;
  color: white;
  padding: 10px 14px;
  border-radius: 8px;
}

.cancel {
  background: #eee;
  padding: 10px 14px;
  border-radius: 8px;
}

@media (max-width: 1200px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .inventory {
    padding: 24px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .filters {
    grid-template-columns: 1fr;
  }

  .grid {
    grid-template-columns: 1fr;
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
  .inventory {
    padding: 20px;
  }

  .tabs {
    flex-wrap: wrap;
  }

  .card-top,
  .left {
    gap: 10px;
    align-items: flex-start;
    flex-direction: column;
  }

  .actions {
    flex-wrap: wrap;
  }
}
</style>
