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
const overviewRef = ref(null)
let stockChart
let overviewChart

function renderCharts() {
  if (!props.data || !chartRef.value || !overviewRef.value) {
    return
  }

  overviewChart?.destroy()
  stockChart?.destroy()

  overviewChart = new Chart(overviewRef.value, {
    type: "bar",
    data: {
      labels: props.data.movement.labels,
      datasets: [
        {
          label: "Items Added",
          data: props.data.movement.added,
          backgroundColor: "#4CAF50",
          borderRadius: 8
        },
        {
          label: "Items Sold",
          data: props.data.movement.sold,
          backgroundColor: "#FFC107",
          borderRadius: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top" } },
      scales: { y: { beginAtZero: true } }
    }
  })

  stockChart = new Chart(chartRef.value, {
    type: "doughnut",
    data: {
      labels: props.data.stock_status.labels,
      datasets: [{
        data: props.data.stock_status.values,
        backgroundColor: ["#4CAF50", "#FFC107", "#F44336"]
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  })
}

onMounted(renderCharts)
watch(() => props.data, renderCharts, { deep: true })
onBeforeUnmount(() => {
  overviewChart?.destroy()
  stockChart?.destroy()
})
</script>

<template>
  <div v-if="data">
    <div class="grid">
      <div class="card">{{ data.total_products }}<br /><small>Total Products</small></div>
      <div class="card">{{ data.low_stock }}<br /><small>Low Stock</small></div>
      <div class="card">Rs {{ data.inventory_value }}<br /><small>Inventory Value</small></div>
      <div class="card">{{ data.out_of_stock }}<br /><small>Out of Stock</small></div>
    </div>

    <div class="charts mt-4">
      <div class="chart-box">
        <div class="chart-title">Inventory Overview</div>
        <div class="chart-canvas">
          <canvas ref="overviewRef"></canvas>
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
