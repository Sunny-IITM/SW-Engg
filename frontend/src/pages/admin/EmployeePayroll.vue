<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { getMyPayrollRecord } from "../../services/api"
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
const payroll = ref(null)
const isLoading = ref(true)
const errorMessage = ref("")

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
    errorMessage.value = "Employee login is required to view payroll."
    isLoading.value = false
    return
  }

  isLoading.value = true
  errorMessage.value = ""

  try {
    payroll.value = await getMyPayrollRecord(selectedMonth.value, selectedYear.value, token, selectedAsOfDate.value)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load payroll right now."
  } finally {
    isLoading.value = false
  }
}

function downloadPayslip() {
  if (!payroll.value) {
    return
  }

  const row = payroll.value
  const lines = [
    "Kulhad Shop Employee Payslip",
    `${monthLabel(row.month)} ${row.year}`,
    "",
    `Employee: ${row.name}`,
    `Role: ${row.role || "Employee"}`,
    `Department: ${row.department || "Not set"}`,
    `Submitted Days: ${row.submitted_days}`,
    `Total Quantity: ${row.total_quantity} units`,
    `Gross Wages: ${formatCurrency(row.gross_wages)}`,
    `Bonus: ${formatCurrency(row.bonus)}`,
    `Deductions: ${formatCurrency(row.deductions)}`,
    `Net Wages: ${formatCurrency(row.net_wages)}`,
    `Status: ${formatStatus(row.status)}`,
    `Calculated Through: ${row.calculated_through}`,
    `Paid On: ${row.paid_on || "Not paid yet"}`
  ]

  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = `${row.name.replace(/\s+/g, "-").toLowerCase()}-${row.month}-${row.year}-payslip.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

onMounted(loadPayroll)
</script>

<template>
  <section class="employee-payroll-page">
    <div class="hero">
      <div>
        <p class="eyebrow">Employee Payroll</p>
        <h1>My Payslip</h1>
        <p class="subcopy">Review your current and past monthly payslips, then download the one you need.</p>
      </div>

      <button class="download-btn" :disabled="!payroll" @click="downloadPayslip">
        Download Payslip
      </button>
    </div>

    <section class="filter-card">
      <label class="field">
        <span>Month</span>
        <select v-model="selectedMonth" @change="loadPayroll">
          <option v-for="month in monthOptions" :key="month.value" :value="month.value">{{ month.label }}</option>
        </select>
      </label>

      <label class="field">
        <span>Year</span>
        <select v-model="selectedYear" @change="loadPayroll">
          <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
        </select>
      </label>

      <label class="field">
        <span>Calculate Through</span>
        <input v-model="selectedAsOfDate" type="date" :max="selectedMonthMaxDate" @change="loadPayroll" />
      </label>
    </section>

    <div v-if="errorMessage" class="notice error">{{ errorMessage }}</div>
    <div v-else-if="isLoading" class="notice">Loading your payslip...</div>

    <div v-else-if="payroll" class="payroll-layout">
      <article class="summary-card spotlight">
        <p>Net Wages</p>
        <h2>{{ formatCurrency(payroll.net_wages) }}</h2>
        <span>{{ monthLabel(payroll.month) }} {{ payroll.year }}</span>
      </article>

      <div class="summary-grid">
        <article class="summary-card plain">
          <p>Gross Wages</p>
          <h3>{{ formatCurrency(payroll.gross_wages) }}</h3>
        </article>

        <article class="summary-card plain">
          <p>Submitted Days</p>
          <h3>{{ payroll.submitted_days }}</h3>
        </article>

        <article class="summary-card plain">
          <p>Total Quantity</p>
          <h3>{{ payroll.total_quantity }} units</h3>
        </article>

        <article class="summary-card plain">
          <p>Status</p>
          <h3><span :class="['status-pill', payroll.status]">{{ formatStatus(payroll.status) }}</span></h3>
        </article>
      </div>

      <article class="detail-card">
        <div class="section-header">
          <div>
            <h2>Payslip Details</h2>
            <p>{{ monthLabel(payroll.month) }} {{ payroll.year }}</p>
          </div>
        </div>

        <div class="detail-grid">
          <p><span>Name</span>{{ payroll.name }}</p>
          <p><span>Role</span>{{ payroll.role || "Employee" }}</p>
          <p><span>Department</span>{{ payroll.department || "Not set" }}</p>
          <p><span>Calculated Through</span>{{ payroll.calculated_through }}</p>
          <p><span>Bonus</span>{{ formatCurrency(payroll.bonus) }}</p>
          <p><span>Deductions</span>{{ formatCurrency(payroll.deductions) }}</p>
          <p><span>Paid On</span>{{ payroll.paid_on || "Not paid yet" }}</p>
          <p><span>Email</span>{{ payroll.email || "Not set" }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.employee-payroll-page {
  min-height: 100vh;
  padding: 30px;
  background: #f3ead8;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #9a3412;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0;
  color: #4a2910;
}

.subcopy {
  margin: 10px 0 0;
  color: #6f604e;
  max-width: 680px;
}

.download-btn {
  padding: 12px 18px;
  border: none;
  border-radius: 12px;
  background: #8b4513;
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.download-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.filter-card,
.detail-card,
.summary-card.plain {
  border-radius: 18px;
  background: white;
  box-shadow: 0 10px 22px rgba(113, 72, 24, 0.12);
}

.filter-card {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  align-items: end;
  padding: 18px;
  margin-bottom: 20px;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  font-size: 13px;
  font-weight: 700;
  color: #5f3817;
}

.field input,
.field select {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 1px solid #ddd5c6;
  border-radius: 10px;
  background: white;
  font: inherit;
}

.notice {
  padding: 14px 16px;
  border-radius: 10px;
  margin-bottom: 18px;
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fdba74;
}

.notice.error {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fca5a5;
}

.payroll-layout {
  display: grid;
  gap: 20px;
}

.spotlight {
  padding: 24px;
  color: white;
  background: linear-gradient(135deg, #965116, #6a320d);
}

.spotlight p,
.spotlight h2,
.spotlight span {
  margin: 0;
}

.spotlight h2 {
  margin-top: 10px;
  font-size: 32px;
}

.spotlight span {
  display: inline-block;
  margin-top: 8px;
  opacity: 0.85;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.summary-card.plain {
  padding: 20px;
}

.summary-card.plain p,
.summary-card.plain h3 {
  margin: 0;
}

.summary-card.plain p {
  color: #7a6049;
}

.summary-card.plain h3 {
  margin-top: 8px;
  color: #4a2910;
}

.detail-card {
  padding: 24px;
}

.section-header h2 {
  margin: 0;
  color: #4a2910;
}

.section-header p {
  margin: 6px 0 0;
  color: #6f604e;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.detail-grid p {
  margin: 0;
  display: grid;
  gap: 4px;
  color: #5f3817;
}

.detail-grid span {
  font-size: 12px;
  color: #9a3412;
  font-weight: 700;
  text-transform: uppercase;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
}

.status-pill.pending {
  background: #fff0b8;
  color: #946200;
}

.status-pill.processed {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-pill.paid {
  background: #dcfce7;
  color: #15803d;
}

@media (max-width: 1100px) {
  .summary-grid,
  .filter-card,
  .detail-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .employee-payroll-page {
    padding: 20px;
  }

  .hero {
    flex-direction: column;
  }
}
</style>
