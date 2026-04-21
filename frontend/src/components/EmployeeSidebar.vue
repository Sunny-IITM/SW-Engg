<script setup>
import { useRoute, useRouter } from "vue-router"
import { clearAuthSession } from "../services/auth"

const route = useRoute()
const router = useRouter()

const isActive = (path) => route.path === path

function handleLogout() {
  clearAuthSession()
  router.push({
    path: "/login",
    query: {
      logout: "success"
    }
  })
}
</script>

<template>
  <aside class="sidebar">
    <div class="logo">
      <div class="brand">
        <span class="brand-mark">K</span>
        <span>Kulhad Shop</span>
      </div>
      <p>Employee Panel</p>
    </div>

    <nav>
      <router-link
        to="/employee"
        class="nav-item"
        :class="{ active: isActive('/employee') }"
      >
        Dashboard
      </router-link>

      <router-link
        to="/employee/entries"
        class="nav-item"
        :class="{ active: isActive('/employee/entries') }"
      >
        Entries
      </router-link>

      <router-link
        to="/employee/payroll"
        class="nav-item"
        :class="{ active: isActive('/employee/payroll') }"
      >
        Payroll
      </router-link>

      <router-link
        to="/employee/profile"
        class="nav-item"
        :class="{ active: isActive('/employee/profile') }"
      >
        Profile
      </router-link>
    </nav>

    <button class="logout" @click="handleLogout">
      Logout
    </button>
  </aside>
</template>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  width: 240px;
  height: 100vh;
  padding: 24px 18px;
  overflow: hidden;
  background: linear-gradient(180deg, #8b4513, #6b320e);
  color: white;
  box-shadow: 3px 0 15px rgba(0, 0, 0, 0.12);
}

.logo {
  margin-bottom: 10px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  font-weight: 700;
}

.logo p {
  margin-top: 4px;
  font-size: 12px;
  opacity: 0.7;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 35px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 10px;
  color: white;
  text-decoration: none;
  font-size: 14px;
  transition: 0.2s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(3px);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.2);
  font-weight: 500;
}

.logout {
  margin-top: auto;
  padding: 12px;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  cursor: pointer;
  text-align: left;
  transition: 0.2s;
}

.logout:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
