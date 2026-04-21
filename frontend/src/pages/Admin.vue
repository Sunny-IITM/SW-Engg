<template>
  <div class="admin-layout">
    <AdminSidebar />
    <main class="admin-main">
      <div v-if="loginMessage" class="status-card success">
        {{ loginMessage }}
      </div>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { useRoute } from "vue-router"
import AdminSidebar from "../components/AdminSidebar.vue"

const route = useRoute()

const loginMessage = computed(() => {
  if (route.query.login === "success") {
    return "Logged in successfully."
  }

  return ""
})
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #f3ead8;
}

.admin-main {
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
  .admin-layout {
    flex-direction: column;
  }

  .admin-main {
    margin-left: 0;
    padding-top: 0;
  }
}
</style>
