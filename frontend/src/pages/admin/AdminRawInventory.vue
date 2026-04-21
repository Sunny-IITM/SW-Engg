<script setup>
import { computed, onMounted, reactive, ref } from "vue"
import {
  adjustRawMaterial,
  createRawMaterial,
  deleteRawMaterial,
  getRawInventory,
  updateRawMaterial
} from "../../services/api"
import { getAuthToken } from "../../services/auth"

const categoryTabs = ["All", "Clay", "Glaze", "Paint", "Packaging", "Other"]
const unitOptions = ["kg", "liters", "pieces", "bags"]

const materials = ref([])
const searchQuery = ref("")
const selectedCategory = ref("All")
const isLoading = ref(true)
const isSaving = ref(false)
const errorMessage = ref("")
const modalErrorMessage = ref("")
const showMaterialModal = ref(false)
const showAdjustModal = ref(false)
const editingMaterialId = ref(null)
const selectedMaterial = ref(null)

const materialForm = reactive({
  name: "",
  category: "Clay",
  unit: "kg",
  quantity: 0,
  reorder_level: 0,
  cost_per_unit: 0,
  supplier: ""
})

const adjustmentForm = reactive({
  adjustment: 0,
  reason: ""
})

function resetMaterialForm() {
  materialForm.name = ""
  materialForm.category = "Clay"
  materialForm.unit = "kg"
  materialForm.quantity = 0
  materialForm.reorder_level = 0
  materialForm.cost_per_unit = 0
  materialForm.supplier = ""
}

const filteredMaterials = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return materials.value.filter((item) => {
    const matchesQuery =
      !query ||
      item.name.toLowerCase().includes(query) ||
      item.supplier.toLowerCase().includes(query)

    const matchesCategory =
      selectedCategory.value === "All" || item.category === selectedCategory.value

    return matchesQuery && matchesCategory
  })
})

const summary = computed(() => {
  const totalMaterials = materials.value.length
  const totalValue = materials.value.reduce((sum, item) => sum + Number(item.inventory_value || 0), 0)
  const lowStockItems = materials.value.filter((item) => item.is_low_stock)
  return {
    totalMaterials,
    totalValue,
    lowStockItems
  }
})

function formatQuantity(item) {
  return `${Number(item.quantity || 0)} ${item.unit}`
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(Number(value || 0))
}

async function loadRawInventory() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to view raw inventory."
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    materials.value = await getRawInventory(token)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load raw inventory right now."
  } finally {
    isLoading.value = false
  }
}

function openAddMaterialModal() {
  editingMaterialId.value = null
  modalErrorMessage.value = ""
  resetMaterialForm()
  showMaterialModal.value = true
}

function openEditMaterialModal(material) {
  editingMaterialId.value = material.id
  modalErrorMessage.value = ""
  materialForm.name = material.name
  materialForm.category = material.category
  materialForm.unit = material.unit
  materialForm.quantity = material.quantity
  materialForm.reorder_level = material.reorder_level
  materialForm.cost_per_unit = material.cost_per_unit
  materialForm.supplier = material.supplier
  showMaterialModal.value = true
}

function openAdjustModal(material) {
  selectedMaterial.value = material
  adjustmentForm.adjustment = 0
  adjustmentForm.reason = ""
  modalErrorMessage.value = ""
  showAdjustModal.value = true
}

async function saveMaterial() {
  if (!materialForm.name.trim() || !materialForm.supplier.trim()) {
    modalErrorMessage.value = "Material name and supplier are required."
    return
  }

  const token = getAuthToken()
  if (!token) {
    modalErrorMessage.value = "Admin login is required to save raw materials."
    return
  }

  isSaving.value = true
  modalErrorMessage.value = ""

  const payload = {
    name: materialForm.name.trim(),
    category: materialForm.category,
    unit: materialForm.unit,
    quantity: Number(materialForm.quantity || 0),
    reorder_level: Number(materialForm.reorder_level || 0),
    cost_per_unit: Number(materialForm.cost_per_unit || 0),
    supplier: materialForm.supplier.trim()
  }

  try {
    if (editingMaterialId.value) {
      const updated = await updateRawMaterial(editingMaterialId.value, payload, token)
      materials.value = materials.value.map((item) => (item.id === updated.id ? updated : item))
    } else {
      const created = await createRawMaterial(payload, token)
      materials.value.unshift(created)
    }

    showMaterialModal.value = false
  } catch (error) {
    modalErrorMessage.value = error.message || "Unable to save raw material."
  } finally {
    isSaving.value = false
  }
}

async function applyAdjustment() {
  if (!selectedMaterial.value) {
    return
  }

  if (!Number(adjustmentForm.adjustment)) {
    modalErrorMessage.value = "Adjustment amount is required."
    return
  }

  const token = getAuthToken()
  if (!token) {
    modalErrorMessage.value = "Admin login is required to update stock."
    return
  }

  isSaving.value = true
  modalErrorMessage.value = ""

  try {
    const response = await adjustRawMaterial(selectedMaterial.value.id, {
      adjustment: Number(adjustmentForm.adjustment),
      reason: adjustmentForm.reason.trim()
    }, token)

    materials.value = materials.value.map((item) =>
      item.id === response.material.id ? response.material : item
    )
    showAdjustModal.value = false
  } catch (error) {
    modalErrorMessage.value = error.message || "Unable to adjust stock."
  } finally {
    isSaving.value = false
  }
}

async function removeMaterial(material) {
  const confirmed = window.confirm(`Delete ${material.name}? This action cannot be undone.`)
  if (!confirmed) {
    return
  }

  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to delete raw materials."
    return
  }

  errorMessage.value = ""

  try {
    await deleteRawMaterial(material.id, token)
    materials.value = materials.value.filter((item) => item.id !== material.id)
  } catch (error) {
    errorMessage.value = error.message || "Unable to delete raw material."
  }
}

onMounted(loadRawInventory)
</script>

<template>
  <div class="raw-page">
    <div class="page-header">
      <div class="page-copy">
        <h1>Raw Inventory Management</h1>
        <p>Track and manage raw materials for pottery production</p>
      </div>
      <button class="add-btn" @click="openAddMaterialModal">+ Add Material</button>
    </div>

    <div class="tabs">
      <router-link to="/admin/raw-inventory" class="tab active">
        Raw Inventory
      </router-link>
      <router-link to="/admin/raw-inventory/history" class="tab">
        Log History
      </router-link>
    </div>

    <div v-if="errorMessage" class="notice error">
      {{ errorMessage }}
    </div>

    <div v-if="isLoading" class="notice">
      Loading raw inventory from the backend...
    </div>

    <template v-else>
      <div class="stats-grid">
        <article class="summary-card total">
          <p>Total Materials</p>
          <h2>{{ summary.totalMaterials }}</h2>
          <span>Box</span>
        </article>

        <article class="summary-card value">
          <p>Total Inventory Value</p>
          <h2>{{ formatCurrency(summary.totalValue) }}</h2>
          <span>Val</span>
        </article>

        <article class="summary-card low">
          <p>Low Stock Items</p>
          <h2>{{ summary.lowStockItems.length }}</h2>
          <span>Low</span>
        </article>
      </div>

      <section v-if="summary.lowStockItems.length" class="alert-card">
        <h3>Low Stock Alert - Reminder Required</h3>
        <div class="alert-grid">
          <article v-for="item in summary.lowStockItems" :key="item.id" class="alert-item">
            <div>
              <strong>{{ item.name }}</strong>
              <p>Supplier: {{ item.supplier || "Not set" }}</p>
            </div>
            <div class="alert-meta">
              <strong>{{ formatQuantity(item) }}</strong>
              <small>Min: {{ item.reorder_level }} {{ item.unit }}</small>
            </div>
          </article>
        </div>
      </section>

      <section class="filter-card">
        <input v-model="searchQuery" placeholder="Search materials or suppliers..." />
        <div class="tabs">
          <button
            v-for="tab in categoryTabs"
            :key="tab"
            :class="['tab-btn', { active: selectedCategory === tab }]"
            @click="selectedCategory = tab"
          >
            {{ tab }}
          </button>
        </div>
      </section>

      <div v-if="filteredMaterials.length === 0" class="empty-state">
        No raw materials found.
      </div>

      <div v-else class="table-card">
        <table class="materials-table">
          <thead>
            <tr>
              <th>Material Name</th>
              <th>Category</th>
              <th>Quantity</th>
              <th>Reminder Level</th>
              <th>Cost/Unit</th>
              <th>Supplier</th>
              <th>Last Restocked</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="material in filteredMaterials" :key="material.id">
              <td>{{ material.name }}</td>
              <td><span class="category-pill">{{ material.category }}</span></td>
              <td :class="{ lowtext: material.is_low_stock }">{{ formatQuantity(material) }}</td>
              <td>{{ material.reorder_level }} {{ material.unit }}</td>
              <td>{{ formatCurrency(material.cost_per_unit) }}</td>
              <td>{{ material.supplier || "-" }}</td>
              <td>{{ material.last_restocked || "-" }}</td>
              <td>
                <div class="row-actions">
                  <button class="icon-btn add" @click="openAdjustModal(material)">Adjust</button>
                  <button class="icon-btn edit" @click="openEditMaterialModal(material)">Edit</button>
                  <button class="icon-btn delete" @click="removeMaterial(material)">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-if="showMaterialModal" class="modal" @click="showMaterialModal = false">
      <div class="modal-box wide" @click.stop>
        <div class="modal-header">
          <h2>{{ editingMaterialId ? "Edit Material" : "Add New Raw Material" }}</h2>
          <button type="button" class="close-btn" @click="showMaterialModal = false">&times;</button>
        </div>

        <div class="form-grid">
          <label class="field field-full">
            <span>Material Name *</span>
            <input v-model="materialForm.name" placeholder="e.g., Red Clay" />
          </label>

          <label class="field">
            <span>Category</span>
            <select v-model="materialForm.category">
              <option v-for="tab in categoryTabs.filter((item) => item !== 'All')" :key="tab" :value="tab">
                {{ tab }}
              </option>
            </select>
          </label>

          <label class="field">
            <span>Unit</span>
            <select v-model="materialForm.unit">
              <option v-for="unit in unitOptions" :key="unit" :value="unit">
                {{ unit }}
              </option>
            </select>
          </label>

          <label v-if="!editingMaterialId" class="field">
            <span>Initial Quantity</span>
            <input v-model.number="materialForm.quantity" type="number" min="0" />
          </label>

          <label class="field">
            <span>Reminder Level</span>
            <input v-model.number="materialForm.reorder_level" type="number" min="0" />
          </label>

          <label class="field">
            <span>Cost per Unit (Rs)</span>
            <input v-model.number="materialForm.cost_per_unit" type="number" min="0" step="0.01" />
          </label>

          <label class="field field-full">
            <span>Supplier Name *</span>
            <input v-model="materialForm.supplier" placeholder="e.g., Rajasthan Clay Suppliers" />
          </label>
        </div>

        <div v-if="modalErrorMessage" class="notice error modal-notice">
          {{ modalErrorMessage }}
        </div>

        <div class="modal-actions">
          <button class="submit" :disabled="isSaving" @click="saveMaterial">
            {{ isSaving ? "Saving..." : editingMaterialId ? "Update Material" : "Add Material" }}
          </button>
          <button class="cancel" :disabled="isSaving" @click="showMaterialModal = false">Cancel</button>
        </div>
      </div>
    </div>

    <div v-if="showAdjustModal && selectedMaterial" class="modal" @click="showAdjustModal = false">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <h2>Adjust Stock</h2>
          <button type="button" class="close-btn" @click="showAdjustModal = false">&times;</button>
        </div>

        <div class="info-box">
          <strong>{{ selectedMaterial.name }}</strong>
          <p>Current Stock: {{ formatQuantity(selectedMaterial) }}</p>
        </div>

        <label class="field">
          <span>Adjustment Amount (use negative for reduction)</span>
          <input v-model.number="adjustmentForm.adjustment" type="number" />
        </label>

        <label class="field">
          <span>Reason (Optional)</span>
          <textarea v-model="adjustmentForm.reason" placeholder="e.g., New stock received from supplier"></textarea>
        </label>

        <div v-if="modalErrorMessage" class="notice error modal-notice">
          {{ modalErrorMessage }}
        </div>

        <div class="modal-actions">
          <button class="apply-btn" :disabled="isSaving" @click="applyAdjustment">
            {{ isSaving ? "Saving..." : "Apply Adjustment" }}
          </button>
          <button class="cancel" :disabled="isSaving" @click="showAdjustModal = false">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.raw-page {
  min-height: 100vh;
  padding: 24px 26px 40px;
  background: linear-gradient(180deg, #f7efe0 0%, #f2e7d5 100%);
}

.page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-copy h1 {
  margin: 0 0 6px;
  color: #8c4b13;
}

.page-copy p {
  margin: 0;
  color: #6f6658;
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

.add-btn,
.submit,
.apply-btn,
.cancel,
.tab-btn,
.icon-btn {
  border: none;
  border-radius: 10px;
  cursor: pointer;
}

.add-btn {
  padding: 12px 16px;
  background: #8b4513;
  color: white;
  font-weight: 700;
}

.notice,
.empty-state {
  padding: 14px 16px;
  border-radius: 14px;
  margin-bottom: 18px;
}

.notice {
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fdba74;
}

.notice.error {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fca5a5;
}

.modal-notice {
  margin-bottom: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 20px;
}

.summary-card {
  position: relative;
  overflow: hidden;
  padding: 18px 20px;
  border-radius: 16px;
  color: white;
  box-shadow: 0 12px 26px rgba(88, 49, 18, 0.14);
}

.summary-card p,
.summary-card h2 {
  margin: 0;
}

.summary-card h2 {
  margin-top: 8px;
  font-size: 22px;
}

.summary-card span {
  position: absolute;
  right: 18px;
  top: 16px;
  font-size: 28px;
  opacity: 0.5;
}

.summary-card.total {
  background: linear-gradient(135deg, #276ef1, #1d4ed8);
}

.summary-card.value {
  background: linear-gradient(135deg, #d07b00, #b16400);
}

.summary-card.low {
  background: linear-gradient(135deg, #e11d48, #b91c1c);
}

.alert-card,
.filter-card,
.table-card {
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 22px rgba(113, 72, 24, 0.12);
}

.alert-card {
  margin-bottom: 18px;
  padding: 18px 20px;
  border: 1px solid #fca5a5;
  background: #fff5f5;
}

.alert-card h3 {
  margin: 0 0 16px;
  color: #991b1b;
}

.alert-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.alert-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid #fca5a5;
  background: white;
}

.alert-item p,
.alert-meta small {
  margin: 4px 0 0;
  color: #6b7280;
}

.alert-meta {
  text-align: right;
  color: #dc2626;
}

.filter-card {
  margin-bottom: 18px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.filter-card input,
.field input,
.field select,
.field textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 1px solid #d6c7b2;
  border-radius: 12px;
  background: white;
  font: inherit;
}

.filter-card input {
  flex: 1;
}

.tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 10px 16px;
  background: #e5e7eb;
  color: #334155;
}

.tab-btn.active {
  background: #8b4513;
  color: white;
}

.table-card {
  overflow: hidden;
}

.materials-table {
  width: 100%;
  border-collapse: collapse;
}

.materials-table thead {
  background: #8b4513;
  color: white;
}

.materials-table th,
.materials-table td {
  padding: 16px 18px;
  text-align: left;
  border-bottom: 1px solid #eadfcb;
}

.materials-table tbody tr:hover {
  background: #fff8ee;
}

.category-pill {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
}

.lowtext {
  color: #dc2626;
  font-weight: 700;
}

.row-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.icon-btn {
  padding: 8px 10px;
  background: #eef2f7;
  color: #374151;
}

.icon-btn.add {
  color: #15803d;
}

.icon-btn.edit {
  color: #1d4ed8;
}

.icon-btn.delete {
  color: #dc2626;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(23, 16, 8, 0.48);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  z-index: 1000;
}

.modal-box {
  width: min(420px, 100%);
  border-radius: 18px;
  background: #fffdf9;
  padding: 20px;
  display: grid;
  gap: 16px;
}

.modal-box.wide {
  width: min(700px, 100%);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.modal-header h2 {
  margin: 0;
  color: #8b4513;
}

.close-btn {
  border: none;
  background: transparent;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  font-size: 13px;
  font-weight: 700;
  color: #5d4633;
}

.field-full {
  grid-column: 1 / -1;
}

.field textarea {
  min-height: 96px;
  resize: vertical;
}

.info-box {
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
}

.info-box p {
  margin: 6px 0 0;
  color: #6b7280;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.submit {
  padding: 12px 18px;
  background: #8b4513;
  color: white;
  font-weight: 700;
}

.apply-btn {
  padding: 12px 18px;
  background: #059669;
  color: white;
  font-weight: 700;
}

.cancel {
  padding: 12px 18px;
  background: #eef2f7;
  color: #374151;
}

@media (max-width: 1100px) {
  .stats-grid,
  .alert-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .raw-page {
    padding: 20px;
  }

  .page-header,
  .filter-card {
    flex-direction: column;
    align-items: stretch;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .table-card {
    overflow-x: auto;
  }
}

@media (max-width: 640px) {
  .tabs {
    flex-wrap: wrap;
  }
}
</style>
