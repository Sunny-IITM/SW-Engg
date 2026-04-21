<script setup>
import { computed, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { clearAuthSession, getAuthSession } from "../services/auth"
import { useCart } from "../store/cart"
import teamLogo from "../assets/cf.jpeg"

const route = useRoute()
const router = useRouter()
const session = ref(getAuthSession())
const { itemCount, lastAddedAt } = useCart()
const cartPulse = ref(false)

const dashboardLink = computed(() => {
  if (session.value?.role === "admin") {
    return "/admin"
  }

  if (session.value?.role === "employee") {
    return "/employee"
  }

  if (session.value?.token) {
    return "/account"
  }

  return ""
})

const dashboardLabel = computed(() => {
  if (session.value?.role === "admin" || session.value?.role === "employee") {
    return "Dashboard"
  }

  return "My Account"
})

function isActive(path) {
  return route.path === path
}

function handleLogout() {
  clearAuthSession()
  session.value = null
  router.push({
    path: "/login",
    query: {
      logout: "success"
    }
  })
}

watch(lastAddedAt, (value) => {
  if (!value) {
    return
  }

  cartPulse.value = false
  window.setTimeout(() => {
    cartPulse.value = true

    window.setTimeout(() => {
      cartPulse.value = false
    }, 550)
  }, 0)
})
</script>

<template>
  <nav class="navbar">
    <router-link to="/" class="brand">
      <img :src="teamLogo" alt="CodeFour logo" class="logo" />
      <span class="title">Kulhad Shop</span>
    </router-link>

    <div class="nav-links">
      <router-link to="/" class="link" :class="{ active: isActive('/') }">
        Home
      </router-link>

      <router-link to="/store" class="link" :class="{ active: isActive('/store') }">
        Products
      </router-link>

      <router-link to="/about" class="link" :class="{ active: isActive('/about') }">
        About
      </router-link>

      <router-link to="/cart" class="link cart-link" :class="{ active: isActive('/cart') }">
        Cart
        <span
          v-if="itemCount > 0"
          :class="['cart-indicator', { pulse: cartPulse }]"
          aria-label="Cart has items"
        ></span>
      </router-link>

      <router-link
        v-if="dashboardLink"
        :to="dashboardLink"
        class="link"
        :class="{ active: route.path.startsWith('/admin') || route.path.startsWith('/employee') || route.path === '/account' }"
      >
        {{ dashboardLabel }}
      </router-link>

      <button v-if="session" class="logout-btn" @click="handleLogout">
        Logout
      </button>

      <router-link
        v-else
        to="/login"
        class="link"
        :class="{ active: route.path === '/login' || route.path === '/signup' || route.path === '/signin' }"
      >
        Login
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 40px;
  background: #e8dfcf;
  color: #5f3817;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
}

.logo {
  width: 30px;
  height: 30px;
  display: block;
  border-radius: 999px;
  object-fit: cover;
}

.title {
  font-weight: 700;
  font-size: 18px;
  color: #5f3817;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 25px;
}

.link,
.logout-btn {
  color: #7a5330;
  text-decoration: none;
  font-size: 15px;
  position: relative;
  transition: 0.2s;
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  cursor: pointer;
}

.link:hover,
.logout-btn:hover {
  color: #4a2910;
}

.link::after,
.logout-btn::after {
  content: "";
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0%;
  height: 2px;
  background: #ffd9a0;
  transition: 0.3s;
}

.link:hover::after,
.logout-btn:hover::after {
  width: 100%;
}

.link.active,
.logout-btn.active {
  color: #4a2910;
}

.link.active::after,
.logout-btn.active::after {
  width: 100%;
}

.cart-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.cart-indicator {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #b45309;
  box-shadow: 0 0 0 4px rgba(180, 83, 9, 0.15);
}

.cart-indicator.pulse {
  animation: cartPulse 0.55s ease;
}

@keyframes cartPulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 4px rgba(180, 83, 9, 0.15);
  }
  45% {
    transform: scale(1.9);
    box-shadow: 0 0 0 9px rgba(180, 83, 9, 0.22);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 4px rgba(180, 83, 9, 0.15);
  }
}

@media (max-width: 768px) {
  .nav-links {
    gap: 15px;
  }

  .navbar {
    padding: 12px 20px;
  }
}
</style>
