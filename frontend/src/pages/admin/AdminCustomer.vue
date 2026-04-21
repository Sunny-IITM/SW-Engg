<script setup>
import { computed, onMounted, ref } from "vue"
import { createAdminUser, deleteAdminUser, getAdminUsers, updateAdminUser } from "../../services/api"
import { getAuthToken } from "../../services/auth"

const searchQuery = ref("")
const selectedStatus = ref("All Status")
const selectedSort = ref("Recent Activity")
const showCustomerModal = ref(false)
const selectedCustomerId = ref(null)
const showConfirmPassword = ref(false)
const isAddingCustomer = ref(false)
const changeCustomerPassword = ref(false)
const isLoading = ref(true)
const isSaving = ref(false)
const errorMessage = ref("")
const formErrorMessage = ref("")
const customers = ref([])
const customer = ref({
  name: "",
  email: "",
  phone: "",
  address: "",
  password: "",
  confirmPassword: ""
})

const stats = computed(() => ({
  total: customers.value.length,
  active: customers.value.filter((item) => item.active).length,
  disabled: customers.value.filter((item) => !item.active).length,
  revenue: customers.value.reduce((sum, item) => sum + Number(item.spent || 0), 0),
  avg: customers.value.length
    ? Math.round(customers.value.reduce((sum, item) => sum + Number(item.spent || 0), 0) / customers.value.length)
    : 0
}))

function resetCustomerForm() {
  formErrorMessage.value = ""
  customer.value = {
    name: "",
    email: "",
    phone: "",
    address: "",
    password: "",
    confirmPassword: ""
  }
}

function normalizeCustomer(item) {
  return {
    id: item.id,
    name: item.name || "",
    email: item.email || "",
    phone: item.phone || "",
    address: item.address || "",
    joined: item.created_at || "",
    lastOrder: "-",
    orders: 0,
    spent: 0,
    active: Boolean(item.is_active)
  }
}

async function loadCustomers() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to view customers."
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    const response = await getAdminUsers("customer", token)
    customers.value = response.map(normalizeCustomer)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load customers right now."
  } finally {
    isLoading.value = false
  }
}

function closeCustomerModal() {
  showCustomerModal.value = false
  selectedCustomerId.value = null
  showConfirmPassword.value = false
  isAddingCustomer.value = false
  changeCustomerPassword.value = false
  isSaving.value = false
  formErrorMessage.value = ""
}

function openAddCustomerModal() {
  isAddingCustomer.value = true
  resetCustomerForm()
  showConfirmPassword.value = false
  changeCustomerPassword.value = true
  formErrorMessage.value = ""
  showCustomerModal.value = true
}

function openCustomerModal(selected) {
  isAddingCustomer.value = false
  selectedCustomerId.value = selected.id
  customer.value = {
    name: selected.name,
    email: selected.email,
    phone: selected.phone,
    address: selected.address ?? "",
    password: "",
    confirmPassword: ""
  }
  showConfirmPassword.value = false
  changeCustomerPassword.value = false
  formErrorMessage.value = ""
  showCustomerModal.value = true
}

async function saveCustomerChanges() {
  const shouldUpdatePassword = isAddingCustomer.value || changeCustomerPassword.value

  if (
    !customer.value.name.trim() ||
    !customer.value.email.trim() ||
    !customer.value.phone.trim() ||
    (shouldUpdatePassword && !customer.value.password.trim()) ||
    (shouldUpdatePassword && !customer.value.confirmPassword.trim())
  ) {
    formErrorMessage.value = "Please fill in all required customer fields."
    return
  }

  if (shouldUpdatePassword && customer.value.password !== customer.value.confirmPassword) {
    formErrorMessage.value = "Passwords do not match."
    return
  }

  const token = getAuthToken()
  if (!token) {
    formErrorMessage.value = "Admin login is required to save customers."
    return
  }

  const payload = {
    name: customer.value.name.trim(),
    email: customer.value.email.trim(),
    phone: customer.value.phone.trim(),
    address: customer.value.address.trim(),
    role: "customer"
  }

  if (shouldUpdatePassword) {
    payload.password = customer.value.password
  }

  isSaving.value = true
  formErrorMessage.value = ""

  try {
    if (isAddingCustomer.value) {
      const created = await createAdminUser(payload, token)
      customers.value.unshift(normalizeCustomer(created))
    } else {
      const updated = await updateAdminUser(selectedCustomerId.value, payload, token)
      customers.value = customers.value.map((item) =>
        item.id === updated.id ? normalizeCustomer(updated) : item
      )
    }

    closeCustomerModal()
  } catch (error) {
    formErrorMessage.value = error.message || "Unable to save customer."
  } finally {
    isSaving.value = false
  }
}

async function toggleStatus(selected) {
  if (selected.active) {
    const shouldDisable = window.confirm(
      `Disable ${selected.name}? They will no longer have an active account status.`
    )

    if (!shouldDisable) {
      return
    }
  }

  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to update account status."
    return
  }

  errorMessage.value = ""

  try {
    const updated = await updateAdminUser(selected.id, { is_active: !selected.active }, token)
    customers.value = customers.value.map((item) =>
      item.id === updated.id ? normalizeCustomer(updated) : item
    )
  } catch (error) {
    errorMessage.value = error.message || "Unable to update customer status."
  }
}

async function deleteCustomer(selectedId) {
  const selectedCustomer = customers.value.find((item) => item.id === selectedId)
  const shouldDelete = window.confirm(
    `Delete ${selectedCustomer?.name || "this customer"}? This action cannot be undone.`
  )

  if (!shouldDelete) {
    return
  }

  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to delete customers."
    return
  }

  errorMessage.value = ""

  try {
    await deleteAdminUser(selectedId, token)
    customers.value = customers.value.filter((item) => item.id !== selectedId)

    if (selectedCustomerId.value === selectedId) {
      closeCustomerModal()
    }
  } catch (error) {
    errorMessage.value = error.message || "Unable to delete customer."
  }
}

function parseDate(value) {
  if (!value || value === "-") {
    return new Date(0)
  }

  const [day, month, year] = value.split("/")
  return new Date(`${year}-${month}-${day}`)
}

const filteredCustomers = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return [...customers.value]
    .filter((item) => {
      const matchesSearch =
        !query ||
        item.name.toLowerCase().includes(query) ||
        item.email.toLowerCase().includes(query) ||
        item.phone.toLowerCase().includes(query)

      const matchesStatus =
        selectedStatus.value === "All Status" ||
        (selectedStatus.value === "Active" && item.active) ||
        (selectedStatus.value === "Disabled" && !item.active)

      return matchesSearch && matchesStatus
    })
    .sort((left, right) => {
      if (selectedSort.value === "Highest Spending") {
        return right.spent - left.spent
      }

      if (selectedSort.value === "Most Orders") {
        return right.orders - left.orders
      }

      if (selectedSort.value === "Name (A-Z)") {
        return left.name.localeCompare(right.name)
      }

      return parseDate(right.joined) - parseDate(left.joined)
    })
})

onMounted(loadCustomers)
</script>

<template>
  <div class="customers">
    <div class="page-header">
      <div class="page-copy">
        <h1>Customer Management</h1>
        <p>View and manage customer accounts</p>
      </div>
      <button class="add-btn" @click="openAddCustomerModal">+ Add Customer</button>
    </div>

    <div v-if="errorMessage" class="notice error">
      {{ errorMessage }}
    </div>

    <div v-if="isLoading" class="notice">
      Loading customers from the backend...
    </div>

    <template v-else>
      <div class="stats">
        <div class="stat brown"><h3>{{ stats.total }}</h3><p>Total</p></div>
        <div class="stat green"><h3>{{ stats.active }}</h3><p>Active</p></div>
        <div class="stat red"><h3>{{ stats.disabled }}</h3><p>Disabled</p></div>
        <div class="stat blue"><h3>Rs {{ stats.revenue }}</h3><p>Revenue</p></div>
        <div class="stat purple"><h3>Rs {{ stats.avg }}</h3><p>Avg Spent</p></div>
      </div>

      <div class="filters">
        <input v-model="searchQuery" placeholder="Search customers..." />
        <select v-model="selectedStatus">
          <option>All Status</option>
          <option>Active</option>
          <option>Disabled</option>
        </select>
        <select v-model="selectedSort">
          <option>Recent Activity</option>
          <option>Highest Spending</option>
          <option>Most Orders</option>
          <option>Name (A-Z)</option>
        </select>
      </div>

      <div v-if="filteredCustomers.length === 0" class="empty-state">
        No customer records found.
      </div>

      <div v-else class="list">
        <div class="row" v-for="c in filteredCustomers" :key="c.id">
          <div class="left">
            <div class="avatar">{{ c.name.charAt(0) }}</div>

            <div>
              <h3>{{ c.name }}</h3>
              <p>&#128231; {{ c.email }}</p>
              <p>&#128197; Joined: {{ c.joined || "-" }}</p>
              <p class="meta customer-summary">
                &#128722; {{ c.orders }} Orders &bull; &#8377; {{ c.spent }} Spent
              </p>
            </div>
          </div>

          <div class="center">
            <p>&#128222; {{ c.phone || "No phone" }}</p>
            <p>&#128205; {{ c.address || "No address" }}</p>
            <p>&#128339; Last order: {{ c.lastOrder }}</p>
          </div>

          <div class="right">
            <span :class="['status', c.active ? 'active' : 'disabled']">
              {{ c.active ? 'Active' : 'Disabled' }}
            </span>

            <div class="actions">
              <button class="icon" @click="openCustomerModal(c)">&#9998; Edit</button>
              <button
                class="icon"
                :class="c.active ? 'danger' : 'enable'"
                @click="toggleStatus(c)"
              >
                {{ c.active ? "Disable" : "Enable" }}
              </button>
              <button class="icon delete-btn" @click="deleteCustomer(c.id)">Delete</button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-if="showCustomerModal" class="modal" @click="closeCustomerModal">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <h2>{{ isAddingCustomer ? "Add New Customer" : "Edit Customer" }}</h2>
          <span @click="closeCustomerModal">&times;</span>
        </div>

        <div v-if="formErrorMessage" class="notice error compact-error">
          {{ formErrorMessage }}
        </div>

        <div class="form">
          <div class="field">
            <label>Full Name *</label>
            <input v-model="customer.name" />
          </div>

          <div class="row-fields">
            <div class="field">
              <label>Email *</label>
              <input v-model="customer.email" />
            </div>

            <div class="field">
              <label>Phone *</label>
              <input v-model="customer.phone" />
            </div>
          </div>

          <div class="field">
            <label>Address</label>
            <input v-model="customer.address" />
          </div>

          <div class="field">
            <label v-if="!isAddingCustomer" class="checkbox-row">
              <input v-model="changeCustomerPassword" type="checkbox" />
              <span>Change password</span>
            </label>
            <label>{{ isAddingCustomer ? "Password *" : "Password" }}</label>
            <input
              :value="customer.password"
              type="password"
              :readonly="!isAddingCustomer && !changeCustomerPassword"
              :disabled="!isAddingCustomer && !changeCustomerPassword"
              :placeholder="isAddingCustomer || changeCustomerPassword ? 'Enter password' : 'Password unchanged'"
              @input="customer.password = $event.target.value"
            />
          </div>

          <div v-if="isAddingCustomer || changeCustomerPassword" class="field">
            <label>Confirm Password *</label>
            <div class="password-field">
              <input
                v-model="customer.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
              />
              <button
                type="button"
                class="password-toggle"
                :aria-label="showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <svg v-if="!showConfirmPassword" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M1.5 12s3.8-6.5 10.5-6.5S22.5 12 22.5 12 18.7 18.5 12 18.5 1.5 12 1.5 12Z" />
                  <circle cx="12" cy="12" r="3.5" />
                </svg>
                <svg v-else viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M3 3l18 18" />
                  <path d="M10.6 5.7A11.5 11.5 0 0 1 12 5.5c6.7 0 10.5 6.5 10.5 6.5a18.9 18.9 0 0 1-4.1 4.8" />
                  <path d="M6.4 6.4A18.8 18.8 0 0 0 1.5 12S5.3 18.5 12 18.5c1.7 0 3.2-.4 4.5-1" />
                  <path d="M9.9 9.9A3 3 0 0 0 12 15a3 3 0 0 0 2.1-.9" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="cancel" @click="closeCustomerModal">Cancel</button>
          <button class="save" :disabled="isSaving" @click="saveCustomerChanges">
            {{ isSaving ? "Saving..." : isAddingCustomer ? "Add Customer" : "Save Changes" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.customers {
  display: flex;
  flex-direction: column;
  gap: 25px;
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

.compact-error {
  margin-bottom: 16px;
}

.empty-state {
  padding: 18px;
  border-radius: 12px;
  background: #f8f6f2;
  color: #7c6a58;
}

.add-btn {
  background: #8b4513;
  color: white;
  padding: 10px 16px;
  border-radius: 8px;
}

.page-copy h1 {
  margin: 0 0 6px;
}

.page-copy p {
  margin: 0;
  color: #666;
}

.stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 15px;
}

.stat {
  padding: 18px;
  border-radius: 12px;
  color: white;
  text-align: center;
}

.brown { background: #8b4513; }
.green { background: #22c55e; }
.red { background: #ef4444; }
.blue { background: #3b82f6; }
.purple { background: #a855f7; }

.filters {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 15px;
}

.filters input,
.filters select {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #ddd;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  align-items: center;
  gap: 18px;
  background: #f8f6f2;
  padding: 20px;
  border-radius: 14px;
  box-shadow: 0 6px 12px rgba(0,0,0,0.08);
}

.left {
  display: flex;
  gap: 15px;
  align-items: flex-start;
  min-width: 0;
}

.avatar {
  width: 45px;
  height: 45px;
  background: #8b4513;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status {
  margin: 5px 0;
  display: inline-block;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
}

.active { background: #22c55e; color: white; }
.disabled { background: #ef4444; color: white; }
.meta {
  font-size: 13px;
  color: #666;
}

.customer-summary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
  padding: 4px 0;
  font-weight: 500;
  color: #5f3817;
}

.center {
  color: #555;
  min-width: 0;
}

.center p {
  margin: 4px 0;
}

.right {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
  min-width: 0;
}

.actions {
  display: flex;
  gap: 10px;
}

.icon {
  padding: 8px 12px;
  border-radius: 8px;
  background: #eee;
}

.icon.danger {
  background: #fee2e2;
}

.icon.enable {
  background: #dcfce7;
  color: #166534;
}

.delete-btn {
  background: #fee2e2;
  color: #b91c1c;
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
  width: min(520px, 100%);
  background: white;
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  color: #8b4513;
}

.modal-header span {
  cursor: pointer;
  font-size: 24px;
  line-height: 1;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.row-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 600;
  color: #5f3817;
}

.checkbox-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.field input {
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.password-field {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
}

.password-toggle {
  width: 44px;
  height: 42px;
  border-radius: 8px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f1e6d6;
  color: #8b4513;
}

.password-toggle svg {
  width: 18px;
  height: 18px;
  stroke: currentColor;
  fill: none;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.modal-actions {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.cancel {
  background: #eee;
  padding: 10px 14px;
  border-radius: 8px;
}

.save {
  background: #8b4513;
  color: white;
  padding: 10px 14px;
  border-radius: 8px;
}

@media (max-width: 1200px) {
  .stats {
    grid-template-columns: repeat(3, 1fr);
  }

  .row {
    grid-template-columns: 1.5fr 1fr 1fr;
  }
}

@media (max-width: 900px) {
  .customers {
    padding: 24px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .filters,
  .row-fields {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .row {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .right {
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .customers {
    padding: 20px;
  }

  .stats {
    grid-template-columns: 1fr;
  }

  .left {
    align-items: flex-start;
  }

  .actions,
  .modal-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .password-field {
    grid-template-columns: 1fr;
  }
}
</style>




