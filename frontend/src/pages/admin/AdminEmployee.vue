<script setup>
import { computed, onMounted, ref } from "vue"
import { createAdminUser, deleteAdminUser, getAdminUsers, updateAdminUser } from "../../services/api"
import { getAuthToken } from "../../services/auth"

const searchQuery = ref("")
const selectedStatus = ref("All Status")
const selectedSort = ref("Recent Joiners")
const showEmployeeModal = ref(false)
const selectedEmployeeId = ref(null)
const showConfirmPassword = ref(false)
const isAddingEmployee = ref(false)
const changeEmployeePassword = ref(false)
const isLoading = ref(true)
const isSaving = ref(false)
const errorMessage = ref("")
const formErrorMessage = ref("")
const employees = ref([])
const employee = ref({
  name: "",
  email: "",
  phone: "",
  role: "",
  department: "",
  address: "",
  password: "",
  confirmPassword: ""
})

const stats = computed(() => ({
  total: employees.value.length,
  active: employees.value.filter((item) => item.status === "active").length,
  disabled: employees.value.filter((item) => item.status !== "active").length,
  production: employees.value.filter((item) => item.department === "Production").length,
  quality: employees.value.filter((item) => item.department === "Quality").length
}))

function resetEmployeeForm() {
  employee.value = {
    name: "",
    email: "",
    phone: "",
    role: "",
    department: "",
    address: "",
    password: "",
    confirmPassword: ""
  }
  formErrorMessage.value = ""
}

function normalizeEmployee(item) {
  return {
    id: item.id,
    name: item.name || "",
    role: item.job_title || "",
    department: item.department || "",
    email: item.email || "",
    phone: item.phone || "",
    address: item.address || "",
    joined: item.created_at || "",
    status: item.is_active ? "active" : "disabled"
  }
}

async function loadEmployees() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to view employees."
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    const response = await getAdminUsers("employee", token)
    employees.value = response.map(normalizeEmployee)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load employees right now."
  } finally {
    isLoading.value = false
  }
}

function closeEmployeeModal() {
  showEmployeeModal.value = false
  selectedEmployeeId.value = null
  isAddingEmployee.value = false
  showConfirmPassword.value = false
  changeEmployeePassword.value = false
  isSaving.value = false
  formErrorMessage.value = ""
}

function openAddEmployeeModal() {
  isAddingEmployee.value = true
  resetEmployeeForm()
  showConfirmPassword.value = false
  changeEmployeePassword.value = true
  showEmployeeModal.value = true
}

function openEmployeeModal(selected) {
  isAddingEmployee.value = false
  selectedEmployeeId.value = selected.id
  employee.value = {
    name: selected.name,
    email: selected.email,
    phone: selected.phone,
    role: selected.role,
    department: selected.department,
    address: selected.address ?? "",
    password: "",
    confirmPassword: ""
  }
  formErrorMessage.value = ""
  showConfirmPassword.value = false
  changeEmployeePassword.value = false
  showEmployeeModal.value = true
}

async function saveEmployeeChanges() {
  const shouldUpdatePassword = isAddingEmployee.value || changeEmployeePassword.value

  if (
    !employee.value.name.trim() ||
    !employee.value.email.trim() ||
    !employee.value.phone.trim() ||
    !employee.value.role.trim() ||
    !employee.value.department.trim() ||
    (shouldUpdatePassword && !employee.value.password.trim()) ||
    (shouldUpdatePassword && !employee.value.confirmPassword.trim())
  ) {
    formErrorMessage.value = "Please fill in all required employee fields."
    return
  }

  if (shouldUpdatePassword && employee.value.password !== employee.value.confirmPassword) {
    formErrorMessage.value = "Passwords do not match."
    return
  }

  const token = getAuthToken()
  if (!token) {
    formErrorMessage.value = "Admin login is required to save employees."
    return
  }

  const payload = {
    name: employee.value.name.trim(),
    email: employee.value.email.trim(),
    phone: employee.value.phone.trim(),
    job_title: employee.value.role.trim(),
    department: employee.value.department.trim(),
    address: employee.value.address.trim(),
    role: "employee"
  }

  if (shouldUpdatePassword) {
    payload.password = employee.value.password
  }

  isSaving.value = true
  formErrorMessage.value = ""

  try {
    if (isAddingEmployee.value) {
      const created = await createAdminUser(payload, token)
      employees.value.unshift(normalizeEmployee(created))
    } else {
      const updated = await updateAdminUser(selectedEmployeeId.value, payload, token)
      employees.value = employees.value.map((item) =>
        item.id === updated.id ? normalizeEmployee(updated) : item
      )
    }

    closeEmployeeModal()
  } catch (error) {
    formErrorMessage.value = error.message || "Unable to save employee."
  } finally {
    isSaving.value = false
  }
}

async function toggleEmployeeStatus(selected) {
  if (selected.status === "active") {
    const shouldDisable = window.confirm(
      `Disable ${selected.name}? They will no longer have an active account status.`
    )

    if (!shouldDisable) {
      return
    }
  }

  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to update employee status."
    return
  }

  errorMessage.value = ""

  try {
    const updated = await updateAdminUser(selected.id, { is_active: selected.status !== "active" }, token)
    employees.value = employees.value.map((item) =>
      item.id === updated.id ? normalizeEmployee(updated) : item
    )
  } catch (error) {
    errorMessage.value = error.message || "Unable to update employee status."
  }
}

async function deleteEmployee(selectedId) {
  const selectedEmployee = employees.value.find((item) => item.id === selectedId)
  const shouldDelete = window.confirm(
    `Delete ${selectedEmployee?.name || "this employee"}? This action cannot be undone.`
  )

  if (!shouldDelete) {
    return
  }

  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to delete employees."
    return
  }

  errorMessage.value = ""

  try {
    await deleteAdminUser(selectedId, token)
    employees.value = employees.value.filter((item) => item.id !== selectedId)

    if (selectedEmployeeId.value === selectedId) {
      closeEmployeeModal()
    }
  } catch (error) {
    errorMessage.value = error.message || "Unable to delete employee."
  }
}

function parseDate(value) {
  if (!value) {
    return new Date(0)
  }

  const [day, month, year] = value.split("/")
  return new Date(`${year}-${month}-${day}`)
}

const filteredEmployees = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return [...employees.value]
    .filter((item) => {
      const matchesSearch =
        !query ||
        item.name.toLowerCase().includes(query) ||
        item.email.toLowerCase().includes(query) ||
        item.phone.toLowerCase().includes(query) ||
        item.role.toLowerCase().includes(query) ||
        item.department.toLowerCase().includes(query)

      const matchesStatus =
        selectedStatus.value === "All Status" ||
        (selectedStatus.value === "Active" && item.status === "active") ||
        (selectedStatus.value === "Disabled" && item.status !== "active")

      return matchesSearch && matchesStatus
    })
    .sort((left, right) => {
      if (selectedSort.value === "Name (A-Z)") {
        return left.name.localeCompare(right.name)
      }

      if (selectedSort.value === "Department") {
        return left.department.localeCompare(right.department)
      }

      if (selectedSort.value === "Role") {
        return left.role.localeCompare(right.role)
      }

      return parseDate(right.joined) - parseDate(left.joined)
    })
})

onMounted(loadEmployees)
</script>

<template>
  <div class="employees">
    <div class="page-header">
      <div class="page-copy">
        <h1>Employee Management</h1>
        <p>Manage employee accounts. Wages are calculated from product rates defined in Product Management.</p>
      </div>
      <button class="add-btn" @click="openAddEmployeeModal">+ Add Employee</button>
    </div>

    <div v-if="errorMessage" class="notice error">
      {{ errorMessage }}
    </div>

    <div v-if="isLoading" class="notice">
      Loading employees from the backend...
    </div>

    <template v-else>
      <div class="stats">
        <div class="stat brown"><h3>{{ stats.total }}</h3><p>Total</p></div>
        <div class="stat green"><h3>{{ stats.active }}</h3><p>Active</p></div>
        <div class="stat red"><h3>{{ stats.disabled }}</h3><p>Disabled</p></div>
        <div class="stat blue"><h3>{{ stats.production }}</h3><p>Production</p></div>
        <div class="stat purple"><h3>{{ stats.quality }}</h3><p>Quality</p></div>
      </div>

      <div class="filters">
        <input v-model="searchQuery" placeholder="Search employees..." />
        <select v-model="selectedStatus">
          <option>All Status</option>
          <option>Active</option>
          <option>Disabled</option>
        </select>
        <select v-model="selectedSort">
          <option>Recent Joiners</option>
          <option>Name (A-Z)</option>
          <option>Department</option>
          <option>Role</option>
        </select>
      </div>

      <div v-if="filteredEmployees.length === 0" class="empty-state">
        No employee records found.
      </div>

      <div v-else class="list">
        <div class="row" v-for="e in filteredEmployees" :key="e.id">
          <div class="left">
            <div class="avatar">{{ e.name.charAt(0) }}</div>

            <div>
              <h3>{{ e.name }}</h3>
              <p>&#128231; {{ e.email }}</p>
              <p>&#128197; Joined: {{ e.joined || "-" }}</p>
              <p class="meta">&#128188; {{ e.role }} &bull; &#127970; {{ e.department }}</p>
            </div>
          </div>

          <div class="center">
            <p>&#128222; {{ e.phone || "No phone" }}</p>
            <p>&#128205; {{ e.address || "No address" }}</p>
          </div>

          <div class="right">
            <span :class="['status', e.status === 'active' ? 'active' : 'disabled']">
              {{ e.status === 'active' ? 'Active' : 'Disabled' }}
            </span>

            <div class="actions">
              <button class="icon" @click="openEmployeeModal(e)">&#9998; Edit</button>
              <button
                class="icon"
                :class="e.status === 'active' ? 'danger' : 'enable'"
                @click="toggleEmployeeStatus(e)"
              >
                {{ e.status === "active" ? "Disable" : "Enable" }}
              </button>
              <button class="icon delete-btn" @click="deleteEmployee(e.id)">Delete</button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-if="showEmployeeModal" class="modal" @click="closeEmployeeModal">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <h2>{{ isAddingEmployee ? "Add New Employee" : "Edit Employee" }}</h2>
          <span @click="closeEmployeeModal">&times;</span>
        </div>

        <div v-if="formErrorMessage" class="notice error compact-error">
          {{ formErrorMessage }}
        </div>

        <div class="form">
          <div class="field">
            <label>Full Name *</label>
            <input v-model="employee.name" />
          </div>

          <div class="row-fields">
            <div class="field">
              <label>Email *</label>
              <input v-model="employee.email" />
            </div>

            <div class="field">
              <label>Phone *</label>
              <input v-model="employee.phone" />
            </div>
          </div>

          <div class="row-fields">
            <div class="field">
              <label>Role *</label>
              <input v-model="employee.role" />
            </div>

            <div class="field">
              <label>Department *</label>
              <select v-model="employee.department">
                <option disabled value="">Select Department</option>
                <option>Production</option>
                <option>Sales</option>
                <option>Management</option>
                <option>Quality</option>
                <option>Packaging</option>
                <option>Delivery</option>
              </select>
            </div>
          </div>

          <div class="field">
            <label>Address</label>
            <input v-model="employee.address" />
          </div>

          <div class="field">
            <label v-if="!isAddingEmployee" class="checkbox-row">
              <input v-model="changeEmployeePassword" type="checkbox" />
              <span>Change password</span>
            </label>
            <label>{{ isAddingEmployee ? "Password *" : "Password" }}</label>
            <input
              v-model="employee.password"
              type="password"
              :readonly="!isAddingEmployee && !changeEmployeePassword"
              :disabled="!isAddingEmployee && !changeEmployeePassword"
              :placeholder="isAddingEmployee || changeEmployeePassword ? 'Enter password' : 'Password unchanged'"
            />
          </div>

          <div v-if="isAddingEmployee || changeEmployeePassword" class="field">
            <label>Confirm Password *</label>
            <div class="password-field">
              <input
                v-model="employee.confirmPassword"
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
          <button class="cancel" @click="closeEmployeeModal">Cancel</button>
          <button class="save" :disabled="isSaving" @click="saveEmployeeChanges">
            {{ isSaving ? "Saving..." : isAddingEmployee ? "Add Employee" : "Save Changes" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.employees {
  display: flex;
  flex-direction: column;
  gap: 25px;
  padding: 30px 50px;
  background: #f3ead8;
  min-height: 100vh;
  box-sizing: border-box;
  width: 100%;
}
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.notice { padding: 14px 16px; border-radius: 10px; background: #fff7ed; color: #9a3412; border: 1px solid #fdba74; }
.notice.error { background: #fef2f2; color: #b91c1c; border-color: #fca5a5; }
.compact-error { margin: 0 0 4px; }
.empty-state { padding: 18px; border-radius: 12px; background: #f8f6f2; color: #7c6a58; }
.add-btn { background: #8b4513; color: white; padding: 10px 16px; border-radius: 8px; }
.page-copy h1 { margin: 0 0 6px; }
.page-copy p { margin: 0; color: #666; }
.stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; }
.stat { padding: 18px; border-radius: 12px; color: white; text-align: center; }
.brown { background: #8b4513; } .green { background: #22c55e; } .red { background: #ef4444; } .blue { background: #3b82f6; } .purple { background: #a855f7; }
.filters { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 15px; }
.filters input, .filters select { padding: 12px; border-radius: 10px; border: 1px solid #ddd; }
.list { display: flex; flex-direction: column; gap: 15px; }
.row { display: grid; grid-template-columns: 2fr 1.2fr 1fr; align-items: center; gap: 18px; background: #f8f6f2; padding: 20px; border-radius: 14px; box-shadow: 0 6px 12px rgba(0,0,0,0.08); }
.left { display: flex; gap: 15px; align-items: flex-start; min-width: 0; }
.avatar { width: 45px; height: 45px; background: #8b4513; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.status { margin: 5px 0; display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; }
.active { background: #22c55e; color: white; } .disabled { background: #ef4444; color: white; }
.meta { font-size: 13px; color: #666; }
.center { color: #555; min-width: 0; }
.center p { margin: 4px 0; }
.right { display: flex; flex-direction: column; gap: 10px; align-items: flex-end; min-width: 0; }
.actions { display: flex; gap: 10px; }
.icon { padding: 8px 12px; border-radius: 8px; background: #eee; }
.icon.danger { background: #fee2e2; }
.icon.enable { background: #dcfce7; color: #166534; }
.delete-btn { background: #fee2e2; color: #b91c1c; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; padding: 20px; z-index: 1000; }
.modal-box { width: min(520px, 100%); background: white; border-radius: 14px; padding: 20px; display: flex; flex-direction: column; gap: 18px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; }
.modal-header h2 { margin: 0; color: #8b4513; }
.modal-header span { cursor: pointer; font-size: 24px; line-height: 1; }
.form { display: flex; flex-direction: column; gap: 14px; }
.row-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 13px; font-weight: 600; color: #5f3817; }
.checkbox-row { display: inline-flex; align-items: center; gap: 8px; }
.field input, .field select { padding: 10px; border-radius: 8px; border: 1px solid #ddd; }
.password-field { display: grid; grid-template-columns: 1fr auto; gap: 10px; }
.password-toggle { width: 44px; height: 42px; border-radius: 8px; padding: 0; display: inline-flex; align-items: center; justify-content: center; background: #f1e6d6; color: #8b4513; }
.password-toggle svg { width: 18px; height: 18px; stroke: currentColor; fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.modal-actions { display: flex; justify-content: space-between; gap: 10px; }
.cancel { background: #eee; padding: 10px 14px; border-radius: 8px; }
.save { background: #8b4513; color: white; padding: 10px 14px; border-radius: 8px; }
@media (max-width: 1200px) { .stats { grid-template-columns: repeat(3, 1fr); } .row { grid-template-columns: 1.5fr 1fr 1fr; } }
@media (max-width: 900px) { .employees { padding: 24px; } .page-header { flex-direction: column; align-items: flex-start; } .filters, .row-fields { grid-template-columns: 1fr; } .stats { grid-template-columns: repeat(2, 1fr); } .row { grid-template-columns: 1fr; gap: 16px; } .right { align-items: flex-start; } }
@media (max-width: 640px) { .employees { padding: 20px; } .stats { grid-template-columns: 1fr; } .left { align-items: flex-start; } .actions, .modal-actions { width: 100%; flex-wrap: wrap; } .password-field { grid-template-columns: 1fr; } }
</style>
