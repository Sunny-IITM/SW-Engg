<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import Chart from "chart.js/auto"

const props = defineProps({
  data: {
    type: Object,
    default: null
  }
})

const chartRef = ref(null)
const trendRef = ref(null)
let paymentChart
let trendChart

function renderCharts() {
  if (!props.data || !chartRef.value || !trendRef.value) {
    return
  }

  trendChart?.destroy()
  paymentChart?.destroy()

  trendChart = new Chart(trendRef.value, {
    type: "line",
    data: {
      labels: props.data.trend.labels,
      datasets: [
        {
          label: "Collections",
          data: props.data.trend.values,
          borderColor: "#2196F3",
          backgroundColor: "rgba(33, 150, 243, 0.18)",
          fill: true,
          tension: 0.35
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: true, position: "top" } },
      scales: { y: { beginAtZero: true } }
    }
  })

  paymentChart = new Chart(chartRef.value, {
    type: "pie",
    data: {
      labels: props.data.method_breakdown.labels,
      datasets: [{
        data: props.data.method_breakdown.values,
        backgroundColor: ["#2196F3", "#9C27B0", "#FF9800", "#10b981"]
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  })
}

onMounted(renderCharts)
watch(() => props.data, renderCharts, { deep: true })
onBeforeUnmount(() => {
  trendChart?.destroy()
  paymentChart?.destroy()
})
</script>

<template>
  <div v-if="data">
    <div class="grid">
      <div class="card">Rs {{ data.total_payments }}<br /><small>Total Payments</small></div>
      <div class="card">Rs {{ data.pending_amount }}<br /><small>Pending</small></div>
      <div class="card">Rs {{ data.completed_amount }}<br /><small>Completed</small></div>
      <div class="card">{{ data.transaction_count }}<br /><small>Transactions</small></div>
    </div>

    <div class="charts mt-4">
      <div class="chart-box">
        <div class="chart-title">Payment Trends</div>
        <div class="chart-canvas">
          <canvas ref="trendRef"></canvas>
        </div>
      </div>
      <div class="chart-box">
        <div class="chart-canvas">
          <canvas ref="chartRef"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-title {
  margin-bottom: 12px;
  font-weight: 600;
}

.chart-box {
  display: flex;
  flex-direction: column;
}
</style>
