<script setup>
import AnalyticsDashboard from "./Admin/AnalyticsDashBoard.vue"
</script>

<template>
  <section class="analytics-content">
    <div class="page-header">
      <div class="page-copy">
        <h1>Analytics Dashboard</h1>
        <p>Track revenue, inventory movement, and payment health in one place.</p>
      </div>
    </div>

    <AnalyticsDashboard />
  </section>
</template>

<style scoped>
.analytics-content {
  box-sizing: border-box;
  width: 100%;
  min-height: calc(100vh - 20px);
  padding: 30px 50px;
  background: #f3ead8;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 25px;
}

.page-copy h1 {
  margin: 0 0 6px;
}

.page-copy p {
  margin: 0;
  color: #666;
}

@media (max-width: 640px) {
  .analytics-content {
    padding: 20px;
  }
}
</style>
