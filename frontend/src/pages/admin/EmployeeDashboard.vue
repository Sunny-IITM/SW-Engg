<script setup>
import { computed, onMounted, ref, watch } from "vue"
import ImageUploader from "../../components/ImageUploader.vue"
import { getProducts } from "../../services/api"
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

const selectedMonth = ref(new Date().getMonth() + 1)
const selectedYear = ref(new Date().getFullYear())
const summaryDays = ref(10)
const attendanceEntries = ref([])
const productOptions = ref([])
const manualQuantity = ref(null)
const manualProductId = ref("")
const manualDate = ref(new Date().toISOString().slice(0, 10))
const manualMessage = ref("")
const detectedProductId = ref("")
const detectedDate = ref(new Date().toISOString().slice(0, 10))
const detectedImageFile = ref(null)
const detectedImagePreview = ref("")
const detectedQuantity = ref(null)
const detectedConfidence = ref(0)
const detectionMessage = ref("")
const detectionMessageType = ref("")
const isDetecting = ref(false)
const isSavingDetectedEntry = ref(false)
const productLoadError = ref("")
const todayIso = new Date().toISOString().slice(0, 10)

const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, index) => currentYear - 2 + index)
})

const availableProductOptions = computed(() =>
  productOptions.value.filter((product) => (product.name || "").trim())
)

const selectedProduct = computed(() =>
  availableProductOptions.value.find((product) => String(product.id) === String(manualProductId.value)) || null
)

const detectedProduct = computed(() =>
  availableProductOptions.value.find((product) => String(product.id) === String(detectedProductId.value)) || null
)

const summarizedEntries = computed(() => {
  const dailyMap = new Map()

  for (const entry of attendanceEntries.value) {
    if (Number(entry.total_quantity || 0) <= 0) {
      continue
    }

    const existing = dailyMap.get(entry.date)
    if (existing) {
      existing.total_quantity += Number(entry.total_quantity || 0)
      existing.daily_wage += Number(entry.daily_wage || 0)
      existing.product_count += 1
      if (entry.product_name) {
        existing.products.push(entry.product_name)
      }
      continue
    }

    dailyMap.set(entry.date, {
      date: entry.date,
      total_quantity: Number(entry.total_quantity || 0),
      daily_wage: Number(entry.daily_wage || 0),
      product_count: 1,
      products: entry.product_name ? [entry.product_name] : []
    })
  }

  return [...dailyMap.values()]
    .map((entry) => ({
      ...entry,
      product_label: entry.products.length <= 1
        ? (entry.products[0] || "-")
        : `${entry.products.length} products`
    }))
    .sort((left, right) => right.date.localeCompare(left.date))
})

const visibleSummaryEntries = computed(() => summarizedEntries.value.slice(0, summaryDays.value))

const attendanceSummary = computed(() => {
  const totalUnits = summarizedEntries.value.reduce((sum, entry) => sum + Number(entry.total_quantity || 0), 0)
  const totalDailyWages = summarizedEntries.value.reduce((sum, entry) => sum + Number(entry.daily_wage || 0), 0)
  const submittedDays = summarizedEntries.value.length

  return {
    totalUnits,
    totalDailyWages,
    submittedDays
  }
})

const recentProductionEntries = computed(() =>
  [...attendanceEntries.value]
    .filter((entry) => Number(entry.total_quantity || 0) > 0)
    .sort((left, right) => {
      const dateCompare = right.date.localeCompare(left.date)
      if (dateCompare !== 0) {
        return dateCompare
      }
      return (right.created_at || "").localeCompare(left.created_at || "")
    })
    .slice(0, 7)
)

watch([selectedMonth, selectedYear], loadAttendance)

async function loadAttendance() {
  try {
    attendanceEntries.value = await ProductionLogService.getEntries(selectedMonth.value, selectedYear.value)
  } catch {
    attendanceEntries.value = []
  }
}

async function loadProductOptions() {
  productLoadError.value = ""

  try {
    const products = await getProducts()
    productOptions.value = products.map((product) => ({
      id: product.id,
      name: product.name || "",
      category: product.category || "",
      wage_per_kulhad: Number(product.wage_per_kulhad || 0)
    }))
  } catch (error) {
    productOptions.value = []
    productLoadError.value = error.message || "Unable to load products right now."
  }
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  }).format(Number(value || 0))
}

async function submitManual() {
  manualMessage.value = ""

  if (!manualQuantity.value || !manualProductId.value) {
    manualMessage.value = "Select a product and enter the number of kulhads produced."
    return
  }

  if (manualDate.value > todayIso) {
    manualMessage.value = "Future dates are not allowed."
    return
  }

  const product = selectedProduct.value
  if (!product) {
    manualMessage.value = "Please choose a valid product from Product Management."
    return
  }

  try {
    const saved = await ProductionLogService.logProduction({
      method: "manual",
      product_id: product.id,
      product: product.name,
      quantity: manualQuantity.value,
      date: manualDate.value
    })

    await loadAttendance()
    manualMessage.value = `Saved ${saved.total_quantity} units for ${saved.product_name}. Daily wage: ${formatCurrency(saved.daily_wage)}.`
    manualQuantity.value = null
    manualProductId.value = ""
  } catch (error) {
    manualMessage.value = error.message || "Could not save production entry."
  }
}

function handleDetectionImageSelected(file, previewUrl) {
  detectedImageFile.value = file
  detectedImagePreview.value = typeof previewUrl === "string" ? previewUrl : ""
  detectedQuantity.value = null
  detectedConfidence.value = 0
  detectionMessageType.value = "info"
  detectionMessage.value = "Image ready. Run detection to fetch the production quantity."
}

function resetDetectionForm() {
  detectedProductId.value = ""
  detectedDate.value = todayIso
  detectedImageFile.value = null
  detectedImagePreview.value = ""
  detectedQuantity.value = null
  detectedConfidence.value = 0
}

async function runImageDetection() {
  detectionMessage.value = ""
  detectionMessageType.value = ""

  if (!detectedProductId.value) {
    detectionMessageType.value = "error"
    detectionMessage.value = "Select a product before running image detection."
    return
  }

  if (!detectedImageFile.value) {
    detectionMessageType.value = "error"
    detectionMessage.value = "Capture or upload an image first."
    return
  }

  if (detectedDate.value > todayIso) {
    detectionMessageType.value = "error"
    detectionMessage.value = "Future dates are not allowed."
    return
  }

  isDetecting.value = true

  try {
    const detection = await ProductionLogService.detectImage(detectedImageFile.value)
    detectedQuantity.value = Number(detection.count || 0)
    detectedConfidence.value = Number(detection.confidence || 0)

    if (detectedQuantity.value <= 0) {
      detectionMessageType.value = "error"
      detectionMessage.value = "No kulhads were detected in this image. Please try another image or use manual entry."
      return
    }

    detectionMessageType.value = "success"
    detectionMessage.value = `Detected ${detectedQuantity.value} kulhads. Review the quantity and confirm to save the production entry.`
  } catch (error) {
    detectionMessageType.value = "error"
    detectionMessage.value = error.message || "Could not detect kulhads from the selected image."
  } finally {
    isDetecting.value = false
  }
}

async function submitDetectedEntry() {
  detectionMessage.value = ""
  detectionMessageType.value = ""

  if (!detectedProduct.value) {
    detectionMessageType.value = "error"
    detectionMessage.value = "Please choose a valid product from Product Management."
    return
  }

  if (detectedDate.value > todayIso) {
    detectionMessageType.value = "error"
    detectionMessage.value = "Future dates are not allowed."
    return
  }

  if (!detectedQuantity.value || Number(detectedQuantity.value) <= 0) {
    detectionMessageType.value = "error"
    detectionMessage.value = "Run detection first or enter a valid detected quantity."
    return
  }

  isSavingDetectedEntry.value = true

  try {
    const saved = await ProductionLogService.logProduction({
      method: "image",
      product_id: detectedProduct.value.id,
      product: detectedProduct.value.name,
      quantity: Number(detectedQuantity.value),
      confidence: detectedConfidence.value,
      date: detectedDate.value
    })

    await loadAttendance()
    detectionMessageType.value = "success"
    detectionMessage.value = `Saved ${saved.total_quantity} detected units for ${saved.product_name}. Daily wage: ${formatCurrency(saved.daily_wage)}.`
    resetDetectionForm()
  } catch (error) {
    detectionMessageType.value = "error"
    detectionMessage.value = error.message || "Could not save the detected production entry."
  } finally {
    isSavingDetectedEntry.value = false
  }
}

onMounted(() => {
  loadProductOptions()
  loadAttendance()
})
</script>

<template>
  <section class="employee-content">
    <div class="header">
      <h1>Employee Dashboard</h1>
      <p>Submit end-of-day production and review the daily wages calculated from product wage settings.</p>
    </div>

    <div class="panel attendance-panel">
      <div class="panel-header">
        <div>
          <h3>Monthly Work Summary</h3>
          <span>Summarized by day using all entries logged on the same date.</span>
        </div>

        <div class="attendance-filters">
          <select v-model="selectedMonth">
            <option v-for="month in monthOptions" :key="month.value" :value="month.value">{{ month.label }}</option>
          </select>
          <select v-model="selectedYear">
            <option v-for="year in yearOptions" :key="year" :value="year">{{ year }}</option>
          </select>
          <select v-model="summaryDays">
            <option :value="10">Last 10 days</option>
            <option :value="15">Last 15 days</option>
            <option :value="30">Last 30 days</option>
          </select>
        </div>
      </div>

      <div class="attendance-cards">
        <div class="attendance-card"><p>Submitted Days</p><h3>{{ attendanceSummary.submittedDays }}</h3></div>
        <div class="attendance-card"><p>Total Units</p><h3>{{ attendanceSummary.totalUnits }}</h3></div>
        <div class="attendance-card"><p>Monthly Wages</p><h3>{{ formatCurrency(attendanceSummary.totalDailyWages) }}</h3></div>
      </div>

      <div class="table-wrapper attendance-table-wrapper">
        <table class="table attendance-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Products</th>
              <th>Units</th>
              <th>Daily Wage</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in visibleSummaryEntries" :key="entry.date">
              <td>{{ entry.date }}</td>
              <td>{{ entry.product_label }}</td>
              <td>{{ entry.total_quantity }}</td>
              <td>{{ formatCurrency(entry.daily_wage) }}</td>
            </tr>
            <tr v-if="!visibleSummaryEntries.length">
              <td colspan="4">No submitted work entries available for this month yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="panel form-panel">
      <div class="panel-header">
        <h3>Daily Work Submission</h3>
        <span>Employees submit total kulhads produced at the end of the day.</span>
      </div>

      <form class="form" @submit.prevent="submitManual">
        <select v-model="manualProductId" required>
          <option disabled value="">Select product</option>
          <option v-for="product in availableProductOptions" :key="product.id" :value="String(product.id)">
            {{ product.name }} - {{ formatCurrency(product.wage_per_kulhad) }}/kulhad
          </option>
        </select>

        <input v-model.number="manualQuantity" type="number" min="1" placeholder="Kulhads produced" required />
        <input v-model="manualDate" type="date" :max="todayIso" required />

        <div class="rate-box">
          <span>Applied Wage</span>
          <strong>{{ formatCurrency(selectedProduct?.wage_per_kulhad || 0) }}/kulhad</strong>
        </div>

        <button class="btn-submit" type="submit">Submit Entry</button>
      </form>

      <p v-if="manualMessage" class="message">{{ manualMessage }}</p>
      <p v-if="productLoadError" class="error">{{ productLoadError }}</p>
    </div>

    <div class="panel form-panel">
      <div class="panel-header">
        <h3>Image-Based Detection</h3>
        <span>Capture or upload a photo, detect kulhads, then confirm the production entry.</span>
      </div>

      <div class="detect-form">
        <select v-model="detectedProductId" required>
          <option disabled value="">Select product</option>
          <option v-for="product in availableProductOptions" :key="product.id" :value="String(product.id)">
            {{ product.name }} - {{ formatCurrency(product.wage_per_kulhad) }}/kulhad
          </option>
        </select>

        <input v-model="detectedDate" type="date" :max="todayIso" required />

        <div class="rate-box">
          <span>Applied Wage</span>
          <strong>{{ formatCurrency(detectedProduct?.wage_per_kulhad || 0) }}/kulhad</strong>
        </div>
      </div>

      <ImageUploader @image-selected="handleDetectionImageSelected" />

      <div v-if="detectedImagePreview" class="detection-preview">
        <img :src="detectedImagePreview" alt="Selected production upload preview" />
      </div>

      <div class="detect-actions">
        <button class="btn-submit detect-btn" type="button" :disabled="isDetecting" @click="runImageDetection">
          {{ isDetecting ? "Detecting..." : "Detect Kulhads" }}
        </button>

        <label class="field-inline">
          <span>Detected Quantity</span>
          <input v-model.number="detectedQuantity" type="number" min="0" placeholder="Detected units" />
        </label>

        <div class="rate-box confidence-box">
          <span>Confidence</span>
          <strong>{{ (Number(detectedConfidence || 0) * 100).toFixed(2) }}%</strong>
        </div>

        <button class="btn-submit" type="button" :disabled="isSavingDetectedEntry || !detectedQuantity" @click="submitDetectedEntry">
          {{ isSavingDetectedEntry ? "Saving..." : "Confirm Detected Entry" }}
        </button>
      </div>

      <p v-if="detectionMessage" :class="detectionMessageType === 'error' ? 'error' : 'message'">{{ detectionMessage }}</p>
      <p v-if="productLoadError" class="error">{{ productLoadError }}</p>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h3>Latest Daily Wage Entries</h3>
        <span>Most recent submissions for the selected month</span>
      </div>

      <div class="table-wrapper">
        <table class="table">
          <thead>
            <tr>
              <th>Day</th>
              <th>Product</th>
              <th>Units</th>
              <th>Daily Wage</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in recentProductionEntries" :key="entry.id">
              <td>{{ entry.date }}</td>
              <td>{{ entry.product_name || "-" }}</td>
              <td>{{ entry.total_quantity }}</td>
              <td>{{ formatCurrency(entry.daily_wage) }}</td>
            </tr>
            <tr v-if="!recentProductionEntries.length">
              <td colspan="4">No production entries available for this month yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<style scoped>
.employee-content { min-height: 100vh; padding: 30px; background: #f3ead8; }
.header { margin-bottom: 24px; }
.header h1 { margin-bottom: 6px; }
.header p { margin: 0; color: #666; }
.panel { padding: 20px; border-radius: 12px; background: white; box-shadow: 0 6px 14px rgba(0, 0, 0, 0.08); margin-bottom: 20px; }
.attendance-filters { display: flex; gap: 10px; flex-wrap: wrap; }
.attendance-cards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
.attendance-card { padding: 16px; border-radius: 12px; background: #f9f5ee; }
.attendance-card p, .attendance-card h3 { margin: 0; }
.attendance-card p { color: #7a6a57; margin-bottom: 8px; }
.attendance-card h3 { color: #5f3817; }
.panel-header { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 14px; }
.panel-header h3 { margin: 0; }
.panel-header span { color: #8a7a66; font-size: 13px; }
.table-wrapper { overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; }
.table th, .table td { padding: 12px 10px; border-bottom: 1px solid #eee5d6; text-align: left; }
.form { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; }
.detect-form { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 16px; }
.detect-actions { display: grid; grid-template-columns: 180px minmax(180px, 220px) minmax(160px, 1fr) 220px; gap: 14px; align-items: end; margin-top: 16px; }
input, select { width: 100%; padding: 12px; border: 1px solid #ddd5c6; border-radius: 10px; }
.rate-box { display: grid; gap: 6px; align-content: center; padding: 12px; border-radius: 10px; background: #f9f5ee; color: #5f3817; }
.rate-box span { font-size: 12px; text-transform: uppercase; color: #8a7a66; }
.btn-submit { padding: 12px 16px; border: none; border-radius: 10px; cursor: pointer; font-weight: 600; background: #8b4513; color: white; }
.detect-btn { background: #2251e6; }
.field-inline { display: grid; gap: 8px; }
.field-inline span { font-size: 12px; text-transform: uppercase; color: #8a7a66; }
.confidence-box { min-height: 76px; }
.detection-preview { margin-top: 16px; max-width: 360px; overflow: hidden; border-radius: 14px; border: 1px solid #ddd5c6; background: #f9f5ee; }
.detection-preview img { display: block; width: 100%; height: 240px; object-fit: cover; }
.message { margin-top: 14px; color: #166534; }
.error { margin-top: 14px; color: #c2410c; }
@media (max-width: 1200px) { .attendance-cards { grid-template-columns: 1fr; } .form, .detect-form, .detect-actions { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 768px) { .employee-content { padding: 20px; } .attendance-filters { flex-direction: column; } .form, .detect-form, .detect-actions { grid-template-columns: 1fr; } .panel-header { flex-direction: column; align-items: flex-start; } .detection-preview { max-width: 100%; } }
</style>
