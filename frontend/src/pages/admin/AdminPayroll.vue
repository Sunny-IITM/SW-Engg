<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue"
import { getPayrollRecords, updateBulkPayrollStatus, updatePayrollRecord } from "../../services/api"
import { getAuthToken } from "../../services/auth"

const monthOptions = [
  { label: "January", value: 1 },
  { label: "February", value: 2 },
  { label: "March", value: 3 },
  { label: "April", value: 4 },
  { label: "May", value: 5 },
  { label: "June", value: 6 },
  { label: "July", value: 7 },
  { label: "August", value: 8 },
  { label: "September", value: 9 },
  { label: "October", value: 10 },
  { label: "November", value: 11 },
  { label: "December", value: 12 }
]

const today = new Date()
const selectedMonth = ref(today.getMonth() + 1)
const selectedYear = ref(today.getFullYear())
const selectedAsOfDate = ref(today.toISOString().slice(0, 10))
const searchQuery = ref("")
const selectedStatus = ref("all")
const payrollRows = ref([])
const isLoading = ref(true)
const isSaving = ref(false)
const errorMessage = ref("")
const showDetailsModal = ref(false)
const selectedPayroll = ref(null)
const editor = reactive({
  bonus: 0,
  deductions: 0,
  paid_on: "",
  status: "pending"
})

const yearOptions = computed(() => {
  const currentYear = today.getFullYear()
  return Array.from({ length: 5 }, (_, index) => currentYear - 2 + index)
})

const selectedMonthMaxDate = computed(() => {
  const month = String(selectedMonth.value).padStart(2, "0")
  const lastDay = new Date(selectedYear.value, selectedMonth.value, 0).getDate()
  return `${selectedYear.value}-${month}-${String(lastDay).padStart(2, "0")}`
})

function clampAsOfDate(value) {
  if (!value) {
    return selectedMonthMaxDate.value
  }

  const minDate = `${selectedYear.value}-${String(selectedMonth.value).padStart(2, "0")}-01`
  if (value < minDate) {
    return minDate
  }
  if (value > selectedMonthMaxDate.value) {
    return selectedMonthMaxDate.value
  }
  return value
}

watch([selectedMonth, selectedYear], () => {
  selectedAsOfDate.value = clampAsOfDate(selectedAsOfDate.value)
})

function monthLabel(monthValue) {
  return monthOptions.find((option) => option.value === Number(monthValue))?.label || ""
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(Number(value || 0))
}

function formatStatus(status) {
  const normalized = (status || "").toLowerCase()
  return normalized ? normalized.charAt(0).toUpperCase() + normalized.slice(1) : "Pending"
}

async function loadPayroll() {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to view payroll."
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    payrollRows.value = await getPayrollRecords(selectedMonth.value, selectedYear.value, token, selectedAsOfDate.value)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load payroll right now."
  } finally {
    isLoading.value = false
  }
}

const filteredPayroll = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return payrollRows.value.filter((row) => {
    const matchesQuery =
      !query ||
      row.name.toLowerCase().includes(query) ||
      row.role.toLowerCase().includes(query) ||
      row.department.toLowerCase().includes(query) ||
      row.email.toLowerCase().includes(query)

    const matchesStatus = selectedStatus.value === "all" || row.status === selectedStatus.value
    return matchesQuery && matchesStatus
  })
})

const summaryCards = computed(() => {
  const totalWages = filteredPayroll.value.reduce((sum, row) => sum + Number(row.net_wages || 0), 0)
  const amountPaid = filteredPayroll.value.filter((row) => row.status === "paid").reduce((sum, row) => sum + Number(row.net_wages || 0), 0)
  const pendingAmount = filteredPayroll.value.filter((row) => row.status !== "paid").reduce((sum, row) => sum + Number(row.net_wages || 0), 0)

  return {
    totalWages,
    amountPaid,
    pendingAmount,
    employeeCount: filteredPayroll.value.length
  }
})

function openPayrollDetails(row) {
  selectedPayroll.value = row
  editor.bonus = Number(row.bonus || 0)
  editor.deductions = Number(row.deductions || 0)
  editor.paid_on = row.paid_on || selectedAsOfDate.value
  editor.status = row.status || "pending"
  showDetailsModal.value = true
}

function closePayrollDetails() {
  showDetailsModal.value = false
  selectedPayroll.value = null
}

async function savePayrollDetails() {
  if (!selectedPayroll.value) return

  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to update payroll."
    return
  }

  isSaving.value = true
  errorMessage.value = ""

  try {
    const updated = await updatePayrollRecord(selectedPayroll.value.id, {
      month: selectedMonth.value,
      year: selectedYear.value,
      bonus: editor.bonus,
      deductions: editor.deductions,
      paid_on: editor.paid_on,
      status: editor.status
    }, token)

    payrollRows.value = payrollRows.value.map((row) => (row.id === updated.id ? updated : row))
    selectedPayroll.value = updated
  } catch (error) {
    errorMessage.value = error.message || "Unable to update payroll."
  } finally {
    isSaving.value = false
  }
}

async function applyBulkStatus(nextStatus, currentStatuses) {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to update payroll."
    return
  }

  isSaving.value = true
  errorMessage.value = ""

  try {
    const response = await updateBulkPayrollStatus({
      month: selectedMonth.value,
      year: selectedYear.value,
      status: nextStatus,
      current_statuses: currentStatuses,
      paid_on: nextStatus === "paid" ? selectedAsOfDate.value : ""
    }, token)

    const updatedLookup = new Map(response.records.map((record) => [record.id, record]))
    payrollRows.value = payrollRows.value.map((row) => updatedLookup.has(row.id) ? { ...row, status: updatedLookup.get(row.id).status, paid_on: updatedLookup.get(row.id).paid_on } : row)
  } catch (error) {
    errorMessage.value = error.message || "Unable to update payroll status."
  } finally {
    isSaving.value = false
  }
}

async function updateSingleStatus(row, nextStatus) {
  const token = getAuthToken()
  if (!token) {
    errorMessage.value = "Admin login is required to update payroll."
    return
  }

  isSaving.value = true
  errorMessage.value = ""

  try {
    const updated = await updatePayrollRecord(row.id, {
      month: selectedMonth.value,
      year: selectedYear.value,
      paid_on: selectedAsOfDate.value,
      status: nextStatus
    }, token)

    payrollRows.value = payrollRows.value.map((item) => (item.id === updated.id ? updated : item))
  } catch (error) {
    errorMessage.value = error.message || "Unable to update payroll status."
  } finally {
    isSaving.value = false
  }
}

function downloadPayslip(row) {
  const lines = [
    "Kulhad Shop Monthly Wage Summary",
    `${monthLabel(row.month)} ${row.year}`,
    "",
    `Employee: ${row.name}`,
    `Role: ${row.role}`,
    `Department: ${row.department}`,
    `Submitted Days: ${row.submitted_days}`,
    `Total Quantity: ${row.total_quantity} units`,
    `Gross Wages: ${formatCurrency(row.gross_wages)}`,
    `Bonus: ${formatCurrency(row.bonus)}`,
    `Deductions: ${formatCurrency(row.deductions)}`,
    `Net Wages: ${formatCurrency(row.net_wages)}`,
    `Calculated Through: ${row.calculated_through}`,
    `Paid On: ${row.paid_on || "Not paid yet"}`
  ]

  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = `${row.name.replace(/\s+/g, "-").toLowerCase()}-${row.month}-${row.year}-wage-summary.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

onMounted(loadPayroll)
</script>

<template>
  <div class="payroll-page">
    <div class="page-header">
      <div class="page-copy">
        <h1>Monthly Wage View</h1>
        <p>Unified monthly wage totals for each employee based on daily work submissions.</p>
      </div>

      <div class="header-actions">
        <button class="header-btn process" :disabled="isSaving" @click="applyBulkStatus('processed', ['pending'])">Process All Pending</button>
        <button class="header-btn paid" :disabled="isSaving" @click="applyBulkStatus('paid', ['processed'])">Pay All Processed</button>
      </div>
    </div>

    <div v-if="errorMessage" class="notice error">{{ errorMessage }}</div>
    <div v-if="isLoading" class="notice">Loading monthly wages from the backend...</div>

    <template v-else>
      <div class="summary-grid">
        <article class="summary-card total"><p>Total Wages</p><h2>{{ formatCurrency(summaryCards.totalWages) }}</h2><span>T</span></article>
        <article class="summary-card paid"><p>Amount Paid</p><h2>{{ formatCurrency(summaryCards.amountPaid) }}</h2><span>P</span></article>
        <article class="summary-card pending"><p>Pending Amount</p><h2>{{ formatCurrency(summaryCards.pendingAmount) }}</h2><span>N</span></article>
        <article class="summary-card employees"><p>Total Employees</p><h2>{{ summaryCards.employeeCount }}</h2><span>E</span></article>
      </div>

      <section class="filter-card period-card">
        <label class="field"><span>Month</span><select v-model="selectedMonth" @change="loadPayroll"><option v-for="month in monthOptions" :key="month.value" :value="month.value">{{ month.label }}</option></select></label>
        <label class="field"><span>Year</span><select v-model="selectedYear" @change="loadPayroll"><option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option></select></label>
        <label class="field"><span>Calculate Through</span><input v-model="selectedAsOfDate" type="date" :max="selectedMonthMaxDate" @change="loadPayroll" /></label>
      </section>

      <section class="filter-card search-card">
        <input v-model="searchQuery" placeholder="Search employees..." />
        <div class="status-tabs">
          <button :class="['tab-btn', { active: selectedStatus === 'all' }]" @click="selectedStatus = 'all'">All</button>
          <button :class="['tab-btn', { active: selectedStatus === 'pending' }]" @click="selectedStatus = 'pending'">Pending</button>
          <button :class="['tab-btn', { active: selectedStatus === 'processed' }]" @click="selectedStatus = 'processed'">Processed</button>
          <button :class="['tab-btn', { active: selectedStatus === 'paid' }]" @click="selectedStatus = 'paid'">Paid</button>
        </div>
      </section>

      <div v-if="filteredPayroll.length === 0" class="empty-state">No monthly wage records found for this period.</div>

      <div v-else class="table-card">
        <table class="payroll-table">
          <thead>
            <tr>
              <th>Employee</th>
              <th>Role</th>
              <th>Submitted Days</th>
              <th>Total Quantity</th>
              <th>Gross Wages</th>
              <th>Bonus</th>
              <th>Deductions</th>
              <th>Net Wages</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredPayroll" :key="row.id">
              <td>{{ row.name }}</td>
              <td><span class="role-pill">{{ row.role || row.department || 'Employee' }}</span></td>
              <td>{{ row.submitted_days }}</td>
              <td>{{ row.total_quantity }}</td>
              <td>{{ formatCurrency(row.gross_wages) }}</td>
              <td class="positive">+{{ formatCurrency(row.bonus) }}</td>
              <td class="negative">-{{ formatCurrency(row.deductions) }}</td>
              <td class="net">{{ formatCurrency(row.net_wages) }}</td>
              <td><span :class="['status-pill', row.status]">{{ formatStatus(row.status) }}</span></td>
              <td>
                <div class="row-actions">
                  <button class="ghost-btn" @click="openPayrollDetails(row)">View</button>
                  <button v-if="row.status === 'pending'" class="mini-btn process" @click="updateSingleStatus(row, 'processed')">Process</button>
                  <button v-else-if="row.status === 'processed'" class="mini-btn paid" @click="updateSingleStatus(row, 'paid')">Mark Paid</button>
                  <button v-else class="ghost-btn" @click="downloadPayslip(row)">Slip</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-if="showDetailsModal && selectedPayroll" class="modal" @click="closePayrollDetails">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <div>
            <h2>Monthly Wage Details</h2>
            <p>{{ monthLabel(selectedPayroll.month) }} {{ selectedPayroll.year }}</p>
          </div>
          <span :class="['status-pill', editor.status]">{{ formatStatus(editor.status) }}</span>
        </div>

        <div class="detail-panel">
          <div class="detail-grid">
            <p><span>Name</span>{{ selectedPayroll.name }}</p>
            <p><span>Role</span>{{ selectedPayroll.role || 'Employee' }}</p>
            <p><span>Submitted Days</span>{{ selectedPayroll.submitted_days }}</p>
            <p><span>Total Quantity</span>{{ selectedPayroll.total_quantity }} units</p>
            <p><span>Gross Wages</span>{{ formatCurrency(selectedPayroll.gross_wages) }}</p>
            <p><span>Calculated Through</span>{{ selectedPayroll.calculated_through }}</p>
          </div>
        </div>

        <div class="detail-panel">
          <div class="editor-grid">
            <label class="field"><span>Bonus</span><input v-model="editor.bonus" type="number" step="0.01" /></label>
            <label class="field"><span>Deductions</span><input v-model="editor.deductions" type="number" step="0.01" /></label>
            <label class="field"><span>Requested Payout Date</span><input v-model="editor.paid_on" type="date" :max="selectedMonthMaxDate" /></label>
            <label class="field"><span>Status</span><select v-model="editor.status"><option value="pending">Pending</option><option value="processed">Processed</option><option value="paid">Paid</option></select></label>
          </div>
          <div class="breakdown-grid">
            <p><span>Net Wages</span>{{ formatCurrency(selectedPayroll.net_wages) }}</p>
            <p><span>Paid On</span>{{ selectedPayroll.paid_on || 'Not paid yet' }}</p>
          </div>
        </div>

        <div class="modal-actions">
          <button class="save-btn" :disabled="isSaving" @click="savePayrollDetails">{{ isSaving ? 'Saving...' : 'Save' }}</button>
          <button class="ghost-wide" @click="downloadPayslip(selectedPayroll)">Download Slip</button>
          <button class="ghost-wide" @click="closePayrollDetails">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.payroll-page { min-height: 100vh; padding: 24px 26px 40px; background: linear-gradient(180deg, #f7efe0 0%, #f2e7d5 100%); }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 20px; }
.page-copy h1 { margin: 0 0 6px; color: #8c4b13; font-size: 28px; }
.page-copy p { margin: 0; color: #6f6658; }
.header-actions { display: flex; gap: 12px; flex-wrap: wrap; }
.header-btn, .save-btn, .ghost-wide, .mini-btn, .ghost-btn { border: none; border-radius: 10px; font-weight: 700; cursor: pointer; }
.header-btn { padding: 12px 16px; color: white; }
.header-btn.process, .mini-btn.process { background: #2251e6; }
.header-btn.paid, .mini-btn.paid { background: #059669; }
.notice, .empty-state { padding: 14px 16px; border-radius: 14px; margin-bottom: 18px; }
.notice { background: #fff7ed; color: #9a3412; border: 1px solid #fdba74; }
.notice.error { background: #fef2f2; color: #b91c1c; border-color: #fca5a5; }
.empty-state { background: rgba(255, 255, 255, 0.8); color: #7c6a58; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; margin-bottom: 20px; }
.summary-card { position: relative; overflow: hidden; padding: 18px 20px; border-radius: 16px; color: white; box-shadow: 0 12px 26px rgba(88, 49, 18, 0.14); }
.summary-card p, .summary-card h2 { margin: 0; }
.summary-card p { font-size: 14px; opacity: 0.95; }
.summary-card h2 { margin-top: 8px; font-size: 22px; }
.summary-card span { position: absolute; right: 18px; top: 16px; font-size: 36px; opacity: 0.55; }
.summary-card.total { background: linear-gradient(135deg, #965116, #6a320d); }
.summary-card.paid { background: linear-gradient(135deg, #06c149, #05963b); }
.summary-card.pending { background: linear-gradient(135deg, #f5a300, #ff7f00); }
.summary-card.employees { background: linear-gradient(135deg, #2251e6, #1238b8); }
.filter-card, .table-card { border-radius: 18px; background: rgba(255, 255, 255, 0.9); box-shadow: 0 10px 22px rgba(113, 72, 24, 0.12); }
.filter-card { margin-bottom: 18px; padding: 20px; }
.period-card { display: flex; align-items: end; gap: 22px; flex-wrap: wrap; }
.field { display: grid; gap: 8px; }
.field span { font-size: 13px; font-weight: 700; color: #5d4633; }
.field input, .field select, .search-card input { padding: 12px 14px; border: 1px solid #d6c7b2; border-radius: 12px; background: white; font: inherit; }
.search-card { display: flex; justify-content: space-between; gap: 16px; align-items: center; }
.search-card input { flex: 1; }
.status-tabs { display: flex; gap: 10px; flex-wrap: wrap; }
.tab-btn { border: none; border-radius: 12px; padding: 10px 16px; background: #e5e7eb; color: #334155; cursor: pointer; }
.tab-btn.active { background: #8b4513; color: white; }
.table-card { overflow: hidden; }
.payroll-table { width: 100%; border-collapse: collapse; }
.payroll-table thead { background: #8b4513; color: white; }
.payroll-table th, .payroll-table td { padding: 16px 18px; text-align: left; border-bottom: 1px solid #eadfcb; }
.role-pill, .status-pill { display: inline-flex; align-items: center; padding: 6px 12px; border-radius: 999px; font-size: 12px; }
.role-pill { background: #efe2ff; color: #7a1be6; }
.status-pill.pending { background: #fff0b8; color: #946200; }
.status-pill.processed { background: #dbeafe; color: #1d4ed8; }
.status-pill.paid { background: #dcfce7; color: #15803d; }
.positive { color: #059669; font-weight: 700; }
.negative { color: #dc2626; font-weight: 700; }
.net { font-weight: 800; color: #111827; }
.row-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.mini-btn, .ghost-btn { padding: 8px 12px; }
.ghost-btn, .ghost-wide { background: #eef2f7; color: #374151; }
.modal { position: fixed; inset: 0; background: rgba(23, 16, 8, 0.48); display: flex; justify-content: center; align-items: center; padding: 20px; z-index: 1000; }
.modal-box { width: min(760px, 100%); max-height: calc(100vh - 40px); overflow-y: auto; border-radius: 18px; background: #fffdf9; padding: 20px; display: grid; gap: 16px; }
.modal-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.modal-header h2, .detail-panel h3 { margin: 0; }
.modal-header p { margin: 6px 0 0; color: #6b7280; }
.detail-panel { padding: 14px; border-radius: 14px; background: #f8fafc; }
.detail-grid, .editor-grid, .breakdown-grid { display: grid; gap: 14px; }
.detail-grid, .breakdown-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.detail-grid p, .breakdown-grid p { margin: 0; display: grid; gap: 4px; }
.detail-grid span, .breakdown-grid span { font-size: 12px; color: #6b7280; }
.editor-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap; }
.save-btn, .ghost-wide { padding: 12px 18px; }
.save-btn { background: #8b4513; color: white; }
@media (max-width: 1200px) { .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 900px) { .payroll-page { padding: 20px; } .page-header, .search-card, .period-card { flex-direction: column; align-items: stretch; } .editor-grid, .detail-grid, .breakdown-grid { grid-template-columns: 1fr; } .table-card { overflow-x: auto; } }
@media (max-width: 640px) { .summary-grid { grid-template-columns: 1fr; } }
</style>
