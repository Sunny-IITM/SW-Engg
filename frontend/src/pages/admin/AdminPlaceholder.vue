<script setup>
defineProps({
  title: {
    type: String,
    required: true
  }
})
</script>

<template>
  <section class="placeholder">
    <h1>{{ title }}</h1>
    <p>This admin page is connected to routing and ready for content.</p>
  </section>
</template>

<style scoped>
.placeholder {
  min-height: 100vh;
  padding: 32px;
  background: #f3ead8;
  color: #5f3817;
}

.placeholder h1 {
  margin-bottom: 8px;
}
</style>
