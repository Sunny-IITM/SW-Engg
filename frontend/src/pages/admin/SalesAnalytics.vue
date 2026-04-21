<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import Chart from "chart.js/auto"

const props = defineProps({
  data: {
    type: Object,
    default: null
  }
})

const lineRef = ref(null)
const barRef = ref(null)
let lineChart
let barChart

function renderCharts() {
  if (!props.data || !lineRef.value || !barRef.value) {
    return
  }

  lineChart?.destroy()
  barChart?.destroy()

  lineChart = new Chart(lineRef.value, {
    type: "line",
    data: {
      labels: props.data.daily_revenue.labels,
      datasets: [{
        label: "Revenue",
        data: props.data.daily_revenue.values,
        fill: true,
        tension: 0.4,
        borderColor: "#8b4513",
        backgroundColor: "rgba(139, 69, 19, 0.15)"
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  })

  barChart = new Chart(barRef.value, {
    type: "bar",
    data: {
      labels: props.data.monthly_revenue_chart.labels,
      datasets: [{
        label: "Revenue",
        data: props.data.monthly_revenue_chart.values,
        backgroundColor: "#d97706",
        borderRadius: 8
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  })
}

onMounted(renderCharts)
watch(() => props.data, renderCharts, { deep: true })
onBeforeUnmount(() => {
  lineChart?.destroy()
  barChart?.destroy()
})
</script>

<template>
  <div v-if="data">
    <div class="grid">
      <div class="card">Rs {{ data.today_revenue }}<br /><small>Today's Revenue</small></div>
      <div class="card">Rs {{ data.monthly_revenue }}<br /><small>Monthly Revenue</small></div>
      <div class="card">{{ data.total_orders }}<br /><small>Total Orders</small></div>
      <div class="card">Rs {{ data.total_revenue }}<br /><small>Total Revenue</small></div>
    </div>

    <div class="charts mt-4">
      <div class="chart-box">
        <canvas ref="lineRef"></canvas>
      </div>
      <div class="chart-box">
        <canvas ref="barRef"></canvas>
      </div>
    </div>
  </div>
</template>
