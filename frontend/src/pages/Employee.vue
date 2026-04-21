<script setup>
import { computed } from "vue"
import { useRoute } from "vue-router"
import EmployeeSidebar from "../components/EmployeeSidebar.vue"

const route = useRoute()

const loginMessage = computed(() => {
  if (route.query.login === "success") {
    return "Logged in successfully."
  }

  return ""
})
</script>

<template>
  <div class="employee-layout">
    <EmployeeSidebar />
    <main class="employee-main">
      <div v-if="loginMessage" class="status-card success">
        {{ loginMessage }}
      </div>
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.employee-layout {
  display: flex;
  min-height: 100vh;
  background: #f3ead8;
}

.employee-main {
  flex: 1;
  min-width: 0;
  margin-left: 240px;
  padding-top: 20px;
}

.status-card {
  margin: 0 24px 20px;
  padding: 14px 16px;
  border-radius: 10px;
}

.status-card.success {
  background: #ecfdf3;
  color: #166534;
  border: 1px solid #86efac;
}

@media (max-width: 900px) {
  .employee-layout {
    flex-direction: column;
  }

  .employee-main {
    margin-left: 0;
    padding-top: 0;
  }
}
</style>
