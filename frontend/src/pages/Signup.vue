<script setup>
import { reactive, ref } from "vue"
import { useRouter } from "vue-router"
import { registerUser } from "../services/api"

const router = useRouter()
const isSubmitting = ref(false)
const errorMessage = ref("")
const successMessage = ref("")

const form = reactive({
  name: "",
  email: "",
  password: "",
  confirmPassword: ""
})

async function handleSignup() {
  errorMessage.value = ""
  successMessage.value = ""

  if (!form.name.trim() || !form.email.trim() || !form.password || !form.confirmPassword) {
    errorMessage.value = "Please fill in all the fields."
    return
  }

  if (form.password !== form.confirmPassword) {
    errorMessage.value = "Passwords do not match."
    return
  }

  isSubmitting.value = true

  try {
    await registerUser({
      name: form.name.trim(),
      email: form.email.trim(),
      password: form.password
    })

    successMessage.value = "Account created successfully. Please sign in to continue."
    router.push({
      path: "/login",
      query: {
        signup: "success"
      }
    })
  } catch (error) {
    errorMessage.value = error.message || "Unable to create your account right now."
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

          <h2>Join Kulhad Community</h2>
          <p class="desc">
            Become a part of our growing family of chai enthusiasts
          </p>

          <div class="features">
            <div class="item">
              <div class="icon">OK</div>
              <div>
                <h4>Free Shipping</h4>
                <p>On orders above Rs 500</p>
              </div>
            </div>

            <div class="item">
              <div class="icon">OK</div>
              <div>
                <h4>Member Discounts</h4>
                <p>Get access to store offers and launches</p>
              </div>
            </div>

            <div class="item">
              <div class="icon">OK</div>
              <div>
                <h4>Order Tracking</h4>
                <p>Real-time updates once order APIs are connected</p>
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
        <h2>Create Account</h2>
        <p class="sub">Join thousands of chai lovers</p>

        <div class="divider-text">SIGN UP WITH EMAIL</div>

        <form class="auth-form" @submit.prevent="handleSignup">
          <input v-model.trim="form.name" type="text" placeholder="Full Name" />
          <input v-model.trim="form.email" type="email" placeholder="Email Address" />
          <input v-model="form.password" type="password" placeholder="Password" />
          <input v-model="form.confirmPassword" type="password" placeholder="Confirm Password" />

          <p v-if="successMessage" class="message success">{{ successMessage }}</p>
          <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>

          <button class="primary" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? "Creating Account..." : "Create Account" }}
          </button>
        </form>

        <p class="link">
          Already have an account?
          <router-link to="/login">Sign in</router-link>
        </p>
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

@media (max-width: 768px) {
  .auth-container {
    grid-template-columns: 1fr;
  }
}
</style>
