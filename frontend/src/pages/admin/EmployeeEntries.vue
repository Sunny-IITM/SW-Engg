<script setup>
import { computed, onMounted, ref } from "vue"
import ProductionLogService from "../../services/ProductionLogService"

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
const searchQuery = ref("")
const entries = ref([])
const isLoading = ref(true)
const errorMessage = ref("")
const selectedEntry = ref(null)

const yearOptions = computed(() => {
  const currentYear = today.getFullYear()
  return Array.from({ length: 5 }, (_, index) => currentYear - 2 + index)
})

const filteredEntries = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return entries.value.filter((entry) =>
    !query ||
    entry.date.toLowerCase().includes(query) ||
    (entry.product_name || "").toLowerCase().includes(query)
  )
})

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(Number(value || 0))
}

async function loadEntries() {
  isLoading.value = true
  errorMessage.value = ""

  try {
    entries.value = await ProductionLogService.getEntries(selectedMonth.value, selectedYear.value)
  } catch (error) {
    errorMessage.value = error.message || "Unable to load employee entries."
  } finally {
    isLoading.value = false
  }
}

function openEntry(entry) {
  selectedEntry.value = entry
}

function exportEntries() {
  const lines = [
    "Kulhad Shop Employee Work Entries",
    `${monthOptions.find((item) => item.value === selectedMonth.value)?.label || ""} ${selectedYear.value}`,
    "",
    "Date,Product,Units,Wage Per Kulhad,Daily Wage"
  ]

  filteredEntries.value.forEach((entry) => {
    lines.push([
      entry.date,
      entry.product_name || "",
      entry.total_quantity,
      entry.wage_per_kulhad,
      entry.daily_wage
    ].join(","))
  })

  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = `employee-entries-${selectedMonth.value}-${selectedYear.value}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

onMounted(loadEntries)
</script>

<template>
  <section class="entries-page">
    <div class="filter-card">
      <label class="field">
        <span>Month</span>
        <select v-model="selectedMonth" @change="loadEntries">
          <option v-for="month in monthOptions" :key="month.value" :value="month.value">{{ month.label }}</option>
        </select>
      </label>

      <label class="field">
        <span>Year</span>
        <select v-model="selectedYear" @change="loadEntries">
          <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
        </select>
      </label>

      <input v-model="searchQuery" class="search" placeholder="Search by date or product..." />
      <button class="export-btn" @click="exportEntries">Export</button>
    </div>

    <div v-if="errorMessage" class="notice error">{{ errorMessage }}</div>
    <div v-if="isLoading" class="notice">Loading entries...</div>

    <div v-else class="table-card">
      <table class="entries-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Product</th>
            <th>Units</th>
            <th>Wage / Kulhad</th>
            <th>Daily Wage</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in filteredEntries" :key="entry.id">
            <td>{{ entry.date }}</td>
            <td>{{ entry.product_name || "-" }}</td>
            <td>{{ entry.total_quantity }} units</td>
            <td>{{ formatCurrency(entry.wage_per_kulhad) }}</td>
            <td class="total">{{ formatCurrency(entry.daily_wage) }}</td>
            <td><button class="view-btn" @click="openEntry(entry)">View</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="selectedEntry" class="modal" @click="selectedEntry = null">
      <div class="modal-box" @click.stop>
        <div class="modal-header">
          <h2>Entry Details</h2>
          <button type="button" class="close-btn" @click="selectedEntry = null">&times;</button>
        </div>

        <div class="detail-grid">
          <p><span>Date</span>{{ selectedEntry.date }}</p>
          <p><span>Product</span>{{ selectedEntry.product_name || "-" }}</p>
          <p><span>Units</span>{{ selectedEntry.total_quantity }}</p>
          <p><span>Wage Per Kulhad</span>{{ formatCurrency(selectedEntry.wage_per_kulhad) }}</p>
          <p><span>Daily Wage</span>{{ formatCurrency(selectedEntry.daily_wage) }}</p>
        </div>

        <div v-if="selectedEntry.notes" class="notes-box">
          <strong>Notes</strong>
          <p>{{ selectedEntry.notes }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.entries-page { min-height: 100vh; padding: 30px; background: #f3ead8; }
.filter-card, .table-card { border-radius: 18px; background: white; box-shadow: 0 10px 22px rgba(113, 72, 24, 0.12); }
.filter-card { display: grid; grid-template-columns: 160px 120px minmax(220px, 1fr) auto; gap: 14px; align-items: end; padding: 18px; margin-bottom: 20px; }
.field { display: grid; gap: 8px; }
.field span { font-size: 13px; font-weight: 700; color: #5f3817; }
.field select, .search { width: 100%; box-sizing: border-box; padding: 12px 14px; border: 1px solid #ddd5c6; border-radius: 10px; background: white; font: inherit; }
.export-btn, .view-btn { border: none; border-radius: 10px; cursor: pointer; }
.export-btn { padding: 12px 18px; background: white; color: #8b4513; border: 1px solid #c17c40; }
.notice { padding: 14px 16px; border-radius: 10px; margin-bottom: 18px; background: #fff7ed; color: #9a3412; border: 1px solid #fdba74; }
.notice.error { background: #fef2f2; color: #b91c1c; border-color: #fca5a5; }
.table-card { overflow: hidden; }
.entries-table { width: 100%; border-collapse: collapse; }
.entries-table thead { background: #8b4513; color: white; }
.entries-table th, .entries-table td { padding: 16px 18px; text-align: left; border-bottom: 1px solid #eadfcb; }
.total { font-weight: 800; color: #111827; }
.view-btn { padding: 8px 12px; background: #eef2f7; color: #1d4ed8; }
.modal { position: fixed; inset: 0; background: rgba(23, 16, 8, 0.48); display: flex; justify-content: center; align-items: center; padding: 20px; z-index: 1000; }
.modal-box { width: min(540px, 100%); border-radius: 18px; background: #fffdf9; padding: 20px; display: grid; gap: 16px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; }
.modal-header h2 { margin: 0; color: #8b4513; }
.close-btn { border: none; background: transparent; font-size: 24px; line-height: 1; cursor: pointer; }
.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.detail-grid p { margin: 0; display: grid; gap: 4px; }
.detail-grid span { font-size: 12px; font-weight: 700; text-transform: uppercase; color: #9a3412; }
.notes-box { padding: 14px; border-radius: 12px; background: #f8fafc; }
.notes-box p, .notes-box strong { margin: 0; }
.notes-box p { margin-top: 6px; color: #6b7280; }
@media (max-width: 1100px) { .filter-card { grid-template-columns: 1fr; } }
@media (max-width: 900px) { .entries-page { padding: 20px; } .table-card { overflow-x: auto; } .detail-grid { grid-template-columns: 1fr; } }
</style>
