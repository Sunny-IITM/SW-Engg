<template>
  <div class="category-filter">
    <button
      v-for="cat in categories"
      :key="cat"
      :class="['tab', selected === cat ? 'active' : '']"
      @click="$emit('change-category', cat)"
    >
      {{ cat }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  selected: String,
  categories: {
    type: Array,
    default: () => ["All"]
  }
})
</script>

<style scoped>
.category-filter {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin: 0;
  flex: 1;
}

.tab {
  padding: 8px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f5f5f5;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab:hover {
  background: #eaeaea;
}

.tab.active {
  background: #0b0f1a;
  color: white;
  border-color: #0b0f1a;
}

@media (max-width: 768px) {
  .category-filter {
    width: 100%;
  }
}
</style>
