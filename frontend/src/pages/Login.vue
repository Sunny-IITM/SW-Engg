<script setup>
import { computed, reactive, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { loginUser } from "../services/api"
import { saveAuthSession } from "../services/auth"

const route = useRoute()
const router = useRouter()
const isSubmitting = ref(false)
const errorMessage = ref("")

const form = reactive({
  email: "",
  password: ""
})

const redirectMessage = computed(() => {
  if (route.query.intent === "cart") {
    return "Please sign in to add items to your cart. Your saved cart will stay available after you log back in."
  }

  if (route.query.signup === "success") {
    return "Account created successfully. Please log in to continue."
  }

  if (route.query.logout === "success") {
    return "Logged out successfully."
  }

  return ""
})

const redirectMessageClass = computed(() => {
  if (route.query.intent === "cart") {
    return "message success"
  }

  if (route.query.logout === "success") {
    return "message logout"
  }

  return "message success"
})

function getPostLoginRoute(role) {
  if (role === "admin") {
    return "/admin"
  }

  if (role === "employee") {
    return "/employee"
  }

  return "/store"
}

function getNextRoute(role) {
  const requestedNext = typeof route.query.next === "string" ? route.query.next : ""

  if (requestedNext.startsWith("/")) {
    return requestedNext
  }

  return getPostLoginRoute(role)
}

async function handleLogin() {
  errorMessage.value = ""

  if (!form.email.trim() || !form.password) {
    errorMessage.value = "Please enter both email and password."
    return
  }

  isSubmitting.value = true

  try {
    const session = await loginUser({
      email: form.email.trim(),
      password: form.password
    })

    session.email = session.email || form.email.trim()

    saveAuthSession(session)
    router.push({
      path: getNextRoute(session.role),
      query: {
        login: "success"
      }
    })
  } catch (error) {
    errorMessage.value = error.message || "Unable to sign in right now."
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="auth-wrapper">
    <div class="auth-container">
      <div class="left-panel">
        <div class="pattern"></div>

        <div class="content">
          <div class="logo">K</div>

          <h2>Welcome Back to Kulhad Shop</h2>

          <p class="desc">
            Experience the authentic taste of chai in traditional handcrafted clay cups
          </p>

          <div class="features">
            <div class="item">
              <div class="icon">OK</div>
              <div>
                <h4>Track Your Orders</h4>
                <p>Monitor your kulhad deliveries in real-time</p>
              </div>
            </div>

            <div class="item">
              <div class="icon">OK</div>
              <div>
                <h4>Save Favorites</h4>
                <p>Create wishlists of your favorite products</p>
              </div>
            </div>

            <div class="item">
              <div class="icon">OK</div>
              <div>
                <h4>Exclusive Offers</h4>
                <p>Get member-only discounts and early access</p>
              </div>
            </div>
          </div>

          <div class="divider"></div>

          <p class="quote">
            "The best kulhads I've ever used!"
          </p>
        </div>
      </div>

      <div class="right-panel">
        <h2>Sign In</h2>
        <p class="sub">Welcome back! Please enter your details</p>

        <div class="divider-text">CONTINUE WITH EMAIL</div>

        <form class="auth-form" @submit.prevent="handleLogin">
          <input v-model.trim="form.email" type="email" placeholder="Email Address" />
          <input v-model="form.password" type="password" placeholder="Password" />

          <p v-if="redirectMessage" :class="redirectMessageClass">{{ redirectMessage }}</p>
          <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>

          <button class="primary" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? "Signing In..." : "Sign In" }}
          </button>
        </form>

        <p class="link">
          Don't have an account?
          <router-link to="/signup">Sign up</router-link>
        </p>

        <router-link to="/store" class="back">
          Back to Shop
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(90deg, #efe5d0, #e6d7b8);
}

.auth-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: min(900px, 100%);
  min-height: 640px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
}

.left-panel {
  position: relative;
  background: linear-gradient(135deg, #8b4513, #6b320e);
  color: white;
  padding: 25px;
  overflow: hidden;
}

.pattern {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 20px 20px;
  opacity: 0.4;
}

.content {
  position: relative;
  z-index: 2;
}

.logo {
  font-size: 18px;
  margin-bottom: 10px;
  font-weight: 700;
}

.desc {
  font-size: 14px;
  margin-bottom: 15px;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item {
  display: flex;
  gap: 10px;
}

.item h4 {
  font-size: 14px;
}

.item p {
  font-size: 12px;
  color: #e7c6a8;
}

.icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255, 200, 0, 0.15);
  border: 1px solid #f4c542;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
}

.divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.2);
  margin: 15px 0;
}

.quote {
  font-size: 12px;
  font-style: italic;
}

.right-panel {
  background: #f9f9f9;
  padding: 25px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.sub {
  font-size: 14px;
  margin-bottom: 10px;
}

.divider-text {
  text-align: center;
  font-size: 11px;
  margin: 10px 0 14px;
}

.auth-form {
  display: flex;
  flex-direction: column;
}

input {
  width: 100%;
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 6px;
  border: 1px solid #ddd;
  font-size: 13px;
}

.message {
  margin: 4px 0 10px;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
}

.message.error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fca5a5;
}

.message.success {
  background: #ecfdf3;
  color: #166534;
  border: 1px solid #86efac;
}

.message.logout {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #facc15;
}

.primary {
  width: 100%;
  padding: 10px;
  font-size: 14px;
  border-radius: 6px;
  background: #8b4513;
  color: white;
}

.primary:disabled {
  opacity: 0.7;
  cursor: wait;
}

.link {
  text-align: center;
  font-size: 12px;
  margin-top: 12px;
}

.back {
  text-align: center;
  font-size: 12px;
  margin-top: 10px;
  color: #777;
  text-decoration: none;
}

.back:hover {
  color: #8b4513;
}

@media (max-width: 768px) {
  .auth-container {
    grid-template-columns: 1fr;
  }
}
</style>
