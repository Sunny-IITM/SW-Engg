<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue"
import { useRouter } from "vue-router"
import { getAuthSession, getAuthToken, updateAuthSession } from "../services/auth"
import { buildProductImageUrl, getMyOrderHistory, getMyProfile, saveCheckoutProfile, updateMyProfile } from "../services/api"
import { useCart } from "../store/cart"

const router = useRouter()
const session = ref(getAuthSession())
const savedMessage = ref("")
const orderMessage = ref("")
const orders = ref([])
const isOrdersLoading = ref(false)
const token = getAuthToken()
const { addItemsToCart } = useCart()
let savedMessageTimeoutId = null
let orderMessageTimeoutId = null

const profile = reactive({
  name: session.value?.name || "",
  email: session.value?.email || "",
  phone: session.value?.phone || "",
  address: session.value?.address || "",
  city: session.value?.city || "",
  state: session.value?.state || "",
  postalCode: session.value?.postal_code || "",
  preferredDrink: session.value?.preferredDrink || "Masala Chai"
})

const passwordForm = reactive({
  currentPassword: "",
  newPassword: "",
  confirmPassword: ""
})

const memberSinceLabel = computed(() => {
  if (!session.value?.token) {
    return "Active member"
  }

  return session.value.role === "customer" ? "Kulhad member" : `${session.value.role} account`
})

const isCustomer = computed(() => session.value?.role === "customer")

function showOrderMessage(message) {
  orderMessage.value = message

  if (orderMessageTimeoutId) {
    clearTimeout(orderMessageTimeoutId)
  }

  orderMessageTimeoutId = window.setTimeout(() => {
    orderMessage.value = ""
    orderMessageTimeoutId = null
  }, 2500)
}

async function loadOrderHistory() {
  if (!token || !isCustomer.value) {
    orders.value = []
    return
  }

  isOrdersLoading.value = true

  try {
    orders.value = await getMyOrderHistory(token)
  } catch {
    orders.value = []
  } finally {
    isOrdersLoading.value = false
  }
}

async function loadProfile() {
  if (!token || !isCustomer.value) {
    return
  }

  try {
    const profileData = await getMyProfile(token)
    profile.name = profileData.name || ""
    profile.email = profileData.email || ""
    profile.phone = profileData.phone || ""
    profile.address = profileData.address || ""
    profile.city = profileData.city || ""
    profile.state = profileData.state || ""
    profile.postalCode = profileData.postal_code || ""

    session.value = updateAuthSession({
      name: profileData.name || "",
      email: profileData.email || "",
      phone: profileData.phone || "",
      address: profileData.address || "",
      city: profileData.city || "",
      state: profileData.state || "",
      postal_code: profileData.postal_code || ""
    })
  } catch {
    // Keep the locally cached profile if backend loading fails.
  }
}

function reorderOrder(order) {
  const availableItems = order.items
    .filter((item) => item.id && item.stock > 0)
    .map((item) => ({
      id: item.id,
      name: item.name,
      price: item.price,
      qty: item.quantity,
      image: buildProductImageUrl(item.image),
      stock: item.stock
    }))

  if (availableItems.length === 0) {
    showOrderMessage("These items are currently out of stock.")
    return
  }

  const addedCount = addItemsToCart(availableItems)
  if (addedCount === 0) {
    showOrderMessage("Cart already has the maximum available quantity for these items.")
    return
  }

  showOrderMessage("Previous order added to your cart.")
  router.push("/cart")
}

async function saveProfile() {
  if (token) {
    try {
      // Update name and other profile fields via /api/profile/me
      await updateMyProfile({
        name: profile.name.trim()
      }, token)
    } catch {
      // Keep local profile updates even if the backend call fails.
    }

    try {
      // Update address fields via checkout profile API
      await saveCheckoutProfile({
        phone: profile.phone.trim(),
        address: profile.address.trim(),
        city: profile.city.trim(),
        state: profile.state.trim(),
        postal_code: profile.postalCode.trim()
      }, token)
    } catch {
      // Keep local profile updates even if the backend call fails.
    }
  }

  const nextSession = updateAuthSession({
    name: profile.name.trim(),
    email: profile.email.trim(),
    phone: profile.phone.trim(),
    address: profile.address.trim(),
    city: profile.city.trim(),
    state: profile.state.trim(),
    postal_code: profile.postalCode.trim(),
    preferredDrink: profile.preferredDrink
  })

  session.value = nextSession
  savedMessage.value = "Profile updated successfully."

  if (savedMessageTimeoutId) {
    clearTimeout(savedMessageTimeoutId)
  }

  savedMessageTimeoutId = window.setTimeout(() => {
    savedMessage.value = ""
    savedMessageTimeoutId = null
  }, 2000)
}

async function resetPassword() {
  if (!token || !isCustomer.value) {
    return
  }

  if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    savedMessage.value = "Fill all password fields."
    return
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    savedMessage.value = "New passwords do not match."
    return
  }

  try {
    await updateMyProfile({
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword
    }, token)
    passwordForm.currentPassword = ""
    passwordForm.newPassword = ""
    passwordForm.confirmPassword = ""
    savedMessage.value = "Password updated successfully."
  } catch (error) {
    savedMessage.value = error.message || "Unable to reset password."
  }
}

onMounted(() => {
  loadProfile()
  loadOrderHistory()
})

onBeforeUnmount(() => {
  if (savedMessageTimeoutId) {
    clearTimeout(savedMessageTimeoutId)
  }

  if (orderMessageTimeoutId) {
    clearTimeout(orderMessageTimeoutId)
  }
})
</script>

<template>
  <div class="profile-page">
    <section class="profile-hero">
      <div>
        <p class="eyebrow">My Account</p>
        <h1>{{ profile.name || "Kulhad Shop Customer" }}</h1>
        <p class="hero-copy">
          Manage your basic account details and shopping profile from one place.
        </p>
      </div>

      <div class="profile-badge">
        <span class="badge-label">{{ memberSinceLabel }}</span>
        <strong>{{ session?.role || "customer" }}</strong>
      </div>
    </section>

    <section class="profile-layout">
      <article class="profile-card summary-card">
        <h2>Account Summary</h2>
        <div class="summary-list">
          <p><span>Name</span>{{ profile.name || "Not set" }}</p>
          <p><span>Email</span>{{ profile.email || "Not set" }}</p>
          <p><span>Phone</span>{{ profile.phone || "Not set" }}</p>
          <p><span>Address</span>{{ profile.address || "Not set" }}</p>
          <p><span>City</span>{{ profile.city || "Not set" }}</p>
          <p><span>State</span>{{ profile.state || "Not set" }}</p>
          <p><span>PIN Code</span>{{ profile.postalCode || "Not set" }}</p>
          <p><span>Preferred Drink</span>{{ profile.preferredDrink }}</p>
        </div>
      </article>

      <article class="profile-card form-card">
        <div class="card-header">
          <div>
            <h2>Profile Details</h2>
            <p>Update the information you want us to remember for your account.</p>
          </div>
          <p v-if="savedMessage" class="saved-message">{{ savedMessage }}</p>
        </div>

        <form class="profile-form" @submit.prevent="saveProfile">
          <label class="field">
            <span>Full Name</span>
            <input v-model="profile.name" type="text" placeholder="Your full name" />
          </label>

          <label class="field">
            <span>Email</span>
            <input v-model="profile.email" type="email" placeholder="name@example.com" disabled />
          </label>

          <label class="field">
            <span>Phone</span>
            <input v-model="profile.phone" type="tel" placeholder="+91 98765 43210" />
          </label>

          <label class="field">
            <span>Preferred Drink</span>
            <select v-model="profile.preferredDrink">
              <option>Masala Chai</option>
              <option>Elaichi Chai</option>
              <option>Ginger Chai</option>
              <option>Lassi</option>
              <option>Filter Coffee</option>
            </select>
          </label>

          <label class="field field-full">
            <span>Delivery Address</span>
            <textarea
              v-model="profile.address"
              rows="4"
              placeholder="House number, street, area, city, state, pincode"
            />
          </label>

          <label class="field">
            <span>City</span>
            <input v-model="profile.city" type="text" placeholder="City" />
          </label>

          <label class="field">
            <span>State</span>
            <input v-model="profile.state" type="text" placeholder="State" />
          </label>

          <label class="field">
            <span>PIN Code</span>
            <input v-model="profile.postalCode" type="text" placeholder="Postal code" />
          </label>

          <button class="save-btn" type="submit">Save Profile</button>
        </form>
      </article>
    </section>

    <section class="profile-card form-card">
      <div class="card-header">
        <div>
          <h2>Reset Password</h2>
          <p>Use your current password to set a new one.</p>
        </div>
      </div>

      <form class="profile-form" @submit.prevent="resetPassword">
        <label class="field">
          <span>Current Password</span>
          <input v-model="passwordForm.currentPassword" type="password" />
        </label>

        <label class="field">
          <span>New Password</span>
          <input v-model="passwordForm.newPassword" type="password" />
        </label>

        <label class="field field-full">
          <span>Confirm New Password</span>
          <input v-model="passwordForm.confirmPassword" type="password" />
        </label>

        <button class="save-btn" type="submit">Update Password</button>
      </form>
    </section>

    <section v-if="isCustomer" class="profile-card orders-card">
      <div class="card-header">
        <div>
          <h2>Order History</h2>
          <p>Review your previous orders and quickly shop the same items again.</p>
        </div>
        <p v-if="orderMessage" class="saved-message">{{ orderMessage }}</p>
      </div>

      <div v-if="isOrdersLoading" class="order-empty">
        Loading your orders...
      </div>

      <div v-else-if="orders.length === 0" class="order-empty">
        No orders placed yet.
      </div>

      <div v-else class="order-history">
        <article v-for="order in orders" :key="order.id" class="order-card">
          <div class="order-top">
            <div>
              <p class="order-number">{{ order.order_number }}</p>
              <p class="order-date">{{ order.date || "Date not available" }}</p>
            </div>
            <div class="order-badges">
              <span class="pill">{{ order.status }}</span>
              <span class="pill soft">{{ order.payment }}</span>
            </div>
          </div>

          <div class="order-meta">
            <p><span>Total</span>Rs {{ order.amount }}</p>
            <p><span>Items</span>{{ order.item_count }} item(s)</p>
            <p><span>Payment</span>{{ order.method }}</p>
          </div>

          <div class="order-items">
            <div v-for="item in order.items" :key="`${order.id}-${item.id}-${item.name}`" class="order-item">
              <img :src="buildProductImageUrl(item.image)" :alt="item.name" class="order-item-image" />
              <div class="order-item-copy">
                <strong>{{ item.name }}</strong>
                <p>Qty {{ item.quantity }} | Rs {{ item.subtotal }}</p>
              </div>
            </div>
          </div>

          <div class="order-actions">
            <button type="button" class="save-btn" @click="reorderOrder(order)">Reorder</button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  padding: 40px 10%;
  background: linear-gradient(180deg, #f5efe3 0%, #efe5d0 100%);
}

.profile-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 28px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #9a3412;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.profile-hero h1 {
  margin: 0;
  color: #4a2910;
}

.hero-copy {
  margin: 10px 0 0;
  max-width: 640px;
  color: #6b4a2d;
}

.profile-badge {
  min-width: 180px;
  padding: 18px 20px;
  border-radius: 16px;
  background: #fffaf2;
  border: 1px solid #e7d8bf;
  box-shadow: 0 10px 24px rgba(95, 56, 23, 0.08);
}

.badge-label {
  display: block;
  margin-bottom: 8px;
  color: #9a3412;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.profile-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 22px;
  margin-bottom: 22px;
}

.profile-card {
  padding: 24px;
  border-radius: 20px;
  background: #fffdf9;
  border: 1px solid #eadfcb;
  box-shadow: 0 12px 28px rgba(95, 56, 23, 0.08);
}

.profile-card h2 {
  margin: 0 0 16px;
  color: #4a2910;
}

.summary-list {
  display: grid;
  gap: 14px;
}

.summary-list p {
  margin: 0;
  display: grid;
  gap: 4px;
  color: #5f3817;
}

.summary-list span {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9a3412;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.card-header p {
  margin: 6px 0 0;
  color: #6b4a2d;
}

.saved-message {
  margin: 0;
  padding: 10px 12px;
  border-radius: 999px;
  background: #ecfdf3;
  color: #166534;
  font-size: 13px;
  font-weight: 700;
}

.profile-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.field {
  display: grid;
  gap: 7px;
}

.field-full {
  grid-column: 1 / -1;
}

.field span {
  color: #5f3817;
  font-size: 13px;
  font-weight: 700;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid #d8c8b2;
  border-radius: 12px;
  padding: 12px 14px;
  background: white;
  font: inherit;
}

.field textarea {
  resize: vertical;
}

.save-btn {
  grid-column: 1 / -1;
  justify-self: start;
  padding: 12px 18px;
  border: none;
  border-radius: 12px;
  background: #8b4513;
  color: white;
  font-weight: 700;
}

.orders-card {
  display: grid;
  gap: 18px;
}

.order-empty {
  padding: 18px;
  border-radius: 16px;
  background: #faf4ea;
  color: #7c6a58;
}

.order-history {
  display: grid;
  gap: 16px;
}

.order-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid #eadfcb;
  background: #fffaf4;
  display: grid;
  gap: 16px;
}

.order-top,
.order-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.order-number,
.order-date,
.order-item-copy p {
  margin: 0;
}

.order-number {
  color: #4a2910;
  font-weight: 700;
}

.order-date {
  margin-top: 4px;
  color: #7c6448;
}

.order-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.pill {
  padding: 8px 12px;
  border-radius: 999px;
  background: #8b4513;
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.pill.soft {
  background: #f3e3cd;
  color: #7a4d28;
}

.order-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.order-meta p {
  margin: 0;
  display: grid;
  gap: 4px;
  color: #5f3817;
}

.order-meta span {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9a3412;
}

.order-items {
  display: grid;
  gap: 12px;
}

.order-item {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.order-item-image {
  width: 58px;
  height: 58px;
  border-radius: 14px;
  object-fit: cover;
  background: #f2e5d4;
}

.order-item-copy {
  min-width: 0;
}

.order-item-copy strong {
  display: block;
  color: #3d2614;
}

.order-item-copy p {
  margin-top: 4px;
  color: #7a6247;
}

@media (max-width: 980px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .profile-page {
    padding: 24px;
  }

  .profile-hero,
  .card-header,
  .order-top,
  .order-actions {
    flex-direction: column;
  }

  .profile-form {
    grid-template-columns: 1fr;
  }

  .order-meta {
    grid-template-columns: 1fr;
  }
}
</style>
