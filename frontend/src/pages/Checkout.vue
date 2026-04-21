<script setup>
import { computed, onMounted, reactive, ref } from "vue"
import { useRouter } from "vue-router"
import { useCart } from "../store/cart"
import { getAuthSession, updateAuthSession } from "../services/auth"
import { createOrder, getCheckoutProfile, saveCheckoutProfile } from "../services/api"

const router = useRouter()
const session = getAuthSession()
const freeShippingThreshold = 500
const { items, clearCart } = useCart()
const token = session?.token || ""
const isProfileLoading = ref(false)
const isSavingAddress = ref(false)
const isPlacingOrder = ref(false)
const savedAddress = ref(null)
const profileNotice = ref("")
const orderNotice = ref("")
const isCustomer = computed(() => session?.role === "customer")

const form = reactive({
  fullName: session?.name || "",
  email: session?.email || "",
  phone: session?.phone || "",
  address: session?.address || "",
  city: session?.city || "",
  state: session?.state || "",
  zipCode: session?.postal_code || "",
  paymentMethod: "Cash on Delivery",
  note: ""
})

const paymentOptions = [
  { label: "Cash on Delivery", value: "Cash on Delivery", disabled: false },
  { label: "UPI", value: "UPI", disabled: true },
  { label: "Credit / Debit Card", value: "Credit / Debit Card", disabled: true }
]

const subtotal = computed(() =>
  items.reduce((sum, item) => sum + item.price * item.qty, 0)
)

const shipping = computed(() => {
  if (items.length === 0 || subtotal.value >= freeShippingThreshold) {
    return 0
  }

  return 50
})

const total = computed(() => subtotal.value + shipping.value)

const isFormValid = computed(() =>
  form.fullName.trim() &&
  form.email.trim() &&
  form.phone.trim() &&
  form.address.trim() &&
  form.city.trim() &&
  form.state.trim() &&
  form.zipCode.trim()
)

const hasAddressDraft = computed(() =>
  form.phone.trim() ||
  form.address.trim() ||
  form.city.trim() ||
  form.state.trim() ||
  form.zipCode.trim()
)

const hasSavedAddress = computed(() =>
  Boolean(
    savedAddress.value &&
    (
      savedAddress.value.address ||
      savedAddress.value.city ||
      savedAddress.value.state ||
      savedAddress.value.postal_code
    )
  )
)

function applySavedAddress() {
  if (!savedAddress.value) {
    return
  }

  form.phone = savedAddress.value.phone || ""
  form.address = savedAddress.value.address || ""
  form.city = savedAddress.value.city || ""
  form.state = savedAddress.value.state || ""
  form.zipCode = savedAddress.value.postal_code || ""
  profileNotice.value = "Previous address loaded."
}

async function loadCheckoutProfile() {
  if (!token || !isCustomer.value) {
    return
  }

  isProfileLoading.value = true

  try {
    const profile = await getCheckoutProfile(token)
    savedAddress.value = profile
  } catch {
    savedAddress.value = null
  } finally {
    isProfileLoading.value = false
  }
}

async function saveAddress() {
  if (!isCustomer.value) {
    profileNotice.value = "Only customer accounts can save checkout addresses."
    return
  }

  if (!token || !hasAddressDraft.value) {
    profileNotice.value = "Enter an address before saving."
    return
  }

  isSavingAddress.value = true

  try {
    const profile = await saveCheckoutProfile({
      phone: form.phone,
      address: form.address,
      city: form.city,
      state: form.state,
      postal_code: form.zipCode
    }, token)

    savedAddress.value = profile
    updateAuthSession({
      phone: profile.phone,
      address: profile.address,
      city: profile.city,
      state: profile.state,
      postal_code: profile.postal_code
    })
    profileNotice.value = "Address saved successfully."
  } catch (error) {
    profileNotice.value = error.message || "Unable to save address right now."
  } finally {
    isSavingAddress.value = false
  }
}

function placeOrder() {
  if (!isCustomer.value) {
    orderNotice.value = "Only customer accounts can place orders."
    return
  }

  if (!isFormValid.value || items.length === 0) {
    return
  }

  placeOrderRequest()
}

async function placeOrderRequest() {
  isPlacingOrder.value = true
  orderNotice.value = ""

  try {
    const response = await createOrder({
      phone: form.phone,
      address: form.address,
      city: form.city,
      state: form.state,
      postal_code: form.zipCode,
      payment_method: form.paymentMethod,
      items: items.map((item) => ({
        id: item.id,
        qty: item.qty
      }))
    }, token)

    updateAuthSession({
      phone: form.phone.trim(),
      address: form.address.trim(),
      city: form.city.trim(),
      state: form.state.trim(),
      postal_code: form.zipCode.trim()
    })

    clearCart()
    window.alert(`${response.order_number} placed successfully.`)
    router.push("/store")
  } catch (error) {
    orderNotice.value = error.message || "Unable to place order right now."
  } finally {
    isPlacingOrder.value = false
  }
}
onMounted(loadCheckoutProfile)
</script>

<template>
  <div class="checkout-page">
    <div class="checkout-heading">
      <p class="eyebrow">Secure Checkout</p>
      <h1>Complete your order</h1>
      <p class="subcopy">
        Fill in your delivery details and review your kulhad order before placing it.
      </p>
    </div>

    <div class="checkout-shell">
      <section class="checkout-main">
        <div class="checkout-card">
          <h2>Contact Details</h2>
          <div class="field-grid">
            <label class="field">
              <span>Full Name</span>
              <input v-model="form.fullName" placeholder="Your full name" />
            </label>

            <label class="field">
              <span>Email</span>
              <input v-model="form.email" type="email" placeholder="you@example.com" />
            </label>

            <label class="field">
              <span>Phone</span>
              <input v-model="form.phone" placeholder="+91 98765 43210" />
            </label>

            <label class="field">
              <span>Payment Method</span>
              <select v-model="form.paymentMethod">
                <option
                  v-for="option in paymentOptions"
                  :key="option.value"
                  :value="option.value"
                  :disabled="option.disabled"
                >
                  {{ option.label }}{{ option.disabled ? " (Coming Soon)" : "" }}
                </option>
              </select>
              <small class="field-note">Only Cash on Delivery is currently available for checkout.</small>
            </label>
          </div>
        </div>

        <div class="checkout-card">
          <h2>Shipping Address</h2>
          <div v-if="isProfileLoading" class="saved-address-box muted">
            Loading saved address...
          </div>

          <div v-else-if="hasSavedAddress" class="saved-address-box">
            <div>
              <p class="saved-address-title">Use previous address</p>
              <p class="saved-address-text">
                {{ savedAddress.address }}
                <span v-if="savedAddress.city">, {{ savedAddress.city }}</span>
                <span v-if="savedAddress.state">, {{ savedAddress.state }}</span>
                <span v-if="savedAddress.postal_code"> - {{ savedAddress.postal_code }}</span>
              </p>
            </div>

            <button type="button" class="saved-address-action" @click="applySavedAddress">
              Use This Address
            </button>
          </div>

          <div class="field-grid">
            <label class="field field-full">
              <span>Address</span>
              <input v-model="form.address" placeholder="House number, street, landmark" />
            </label>

            <label class="field">
              <span>City</span>
              <input v-model="form.city" placeholder="City" />
            </label>

            <label class="field">
              <span>State</span>
              <input v-model="form.state" placeholder="State" />
            </label>

            <label class="field">
              <span>PIN Code</span>
              <input v-model="form.zipCode" placeholder="Postal code" />
            </label>

            <label class="field field-full">
              <span>Order Note</span>
              <textarea v-model="form.note" placeholder="Optional delivery note"></textarea>
            </label>
          </div>

          <div class="address-actions">
            <button
              type="button"
              class="save-address-btn"
              :disabled="isSavingAddress || !isCustomer"
              @click="saveAddress"
            >
              {{ isSavingAddress ? "Saving..." : "Add Address" }}
            </button>
            <p class="autosave-note">
              {{
                profileNotice ||
                (isCustomer
                  ? "Save this address to reuse it on your next checkout."
                  : "Sign in with a customer account to save checkout addresses.")
              }}
            </p>
          </div>
        </div>
      </section>

      <aside class="checkout-side">
        <div class="summary-card">
          <div class="summary-header">
            <div>
              <p class="eyebrow">Order Summary</p>
              <h2>{{ items.length }} item(s)</h2>
            </div>
            <router-link to="/cart" class="edit-link">Edit Cart</router-link>
          </div>

          <div v-if="items.length" class="summary-items">
            <article v-for="item in items" :key="item.id" class="summary-item">
              <img :src="item.image" :alt="item.name" class="summary-image" />

              <div class="summary-copy">
                <h3>{{ item.name }}</h3>
                <p>Qty {{ item.qty }}</p>
              </div>

              <strong>Rs {{ item.price * item.qty }}</strong>
            </article>
          </div>

          <div v-else class="empty-box">
            Your cart is empty.
          </div>

          <div class="price-table">
            <div class="price-row">
              <span>Subtotal</span>
              <span>Rs {{ subtotal }}</span>
            </div>
            <div class="price-row">
              <span>Shipping</span>
              <span>{{ shipping === 0 ? "Free" : `Rs ${shipping}` }}</span>
            </div>
            <div class="price-row total-row">
              <span>Total</span>
              <span>Rs {{ total }}</span>
            </div>
          </div>

          <button
            class="place-order"
            :disabled="!items.length || !isFormValid || isPlacingOrder"
            @click="placeOrder"
          >
            {{ isPlacingOrder ? "Placing Order..." : "Place Order" }}
          </button>

          <p v-if="orderNotice" class="order-notice">{{ orderNotice }}</p>
          <p class="secure-note">Encrypted checkout and carefully packed delivery.</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.checkout-page {
  min-height: 100vh;
  padding: 42px 24px 56px;
  background:
    radial-gradient(circle at top left, rgba(219, 186, 140, 0.35), transparent 28%),
    linear-gradient(180deg, #f8f0e2 0%, #efe2cf 100%);
}

.checkout-heading {
  max-width: 1240px;
  margin: 0 auto 28px;
  padding: 6px 4px 2px;
}

.checkout-shell {
  max-width: 1240px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(340px, 0.9fr);
  gap: 28px;
  align-items: stretch;
}

.checkout-main {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #a35b20;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.checkout-heading h1,
.summary-header h2,
.checkout-card h2 {
  margin: 0;
}

.subcopy {
  max-width: 640px;
  margin: 10px 0 0;
  color: #6b5a47;
  line-height: 1.6;
}

.checkout-card,
.summary-card {
  border: 1px solid rgba(140, 92, 46, 0.12);
  border-radius: 24px;
  background: rgba(255, 252, 247, 0.9);
  box-shadow: 0 24px 60px rgba(95, 56, 23, 0.08);
  backdrop-filter: blur(4px);
}

.checkout-card {
  padding: 26px;
}

.checkout-card h2 {
  margin-bottom: 18px;
  color: #3f2a18;
  font-size: 22px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.saved-address-box {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 18px;
  padding: 16px 18px;
  border-radius: 18px;
  background: #fff4e5;
  border: 1px solid #eed4b1;
}

.saved-address-box.muted {
  color: #7c6a58;
}

.saved-address-title {
  margin: 0 0 4px;
  color: #8b4513;
  font-weight: 700;
}

.saved-address-text {
  margin: 0;
  color: #6c5a49;
  line-height: 1.5;
}

.saved-address-action {
  border: none;
  border-radius: 12px;
  padding: 12px 16px;
  background: #8b4513;
  color: white;
  font-weight: 700;
  white-space: nowrap;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field span {
  font-size: 13px;
  font-weight: 700;
  color: #704626;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 13px 14px;
  border: 1px solid #dfd1bf;
  border-radius: 14px;
  background: white;
  color: #2f241b;
  font: inherit;
}

.field-note {
  color: #8a7764;
  font-size: 12px;
  line-height: 1.5;
}

.field textarea {
  min-height: 112px;
  resize: vertical;
}

.autosave-note {
  margin: 0;
  color: #7c6a58;
  font-size: 13px;
}

.address-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 14px;
}

.save-address-btn {
  border: none;
  border-radius: 12px;
  padding: 12px 16px;
  background: #8b4513;
  color: white;
  font-weight: 700;
  white-space: nowrap;
}

.save-address-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.field-full {
  grid-column: 1 / -1;
}

.checkout-side {
  display: flex;
  flex-direction: column;
}

.summary-card {
  position: sticky;
  top: 92px;
  padding: 24px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.edit-link {
  color: #8b4513;
  font-weight: 700;
  text-decoration: none;
}

.summary-items {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 22px;
}

.summary-item {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.summary-image {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 16px;
  background: #f1e6d6;
}

.summary-copy h3,
.summary-copy p {
  margin: 0;
}

.summary-copy h3 {
  font-size: 15px;
  color: #312319;
}

.summary-copy p {
  margin-top: 4px;
  color: #7b6854;
  font-size: 13px;
}

.empty-box {
  margin-bottom: 20px;
  padding: 16px;
  border-radius: 16px;
  background: #faf3e8;
  color: #7c6a58;
}

.price-table {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 18px;
  border-top: 1px solid #eadcca;
}

.price-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: #5f503f;
}

.total-row {
  padding-top: 8px;
  color: #24170f;
  font-weight: 800;
  font-size: 18px;
}

.place-order {
  width: 100%;
  margin-top: 22px;
  border: none;
  border-radius: 16px;
  padding: 15px 18px;
  background: linear-gradient(135deg, #9b4d14, #6f3111);
  color: white;
  font-size: 15px;
  font-weight: 700;
  box-shadow: 0 18px 34px rgba(111, 49, 17, 0.22);
}

.place-order:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}

.secure-note {
  margin: 14px 0 0;
  text-align: center;
  color: #7c6a58;
  font-size: 13px;
}

.order-notice {
  margin: 14px 0 0;
  color: #b91c1c;
  font-size: 13px;
  text-align: center;
}

@media (max-width: 980px) {
  .checkout-shell {
    grid-template-columns: 1fr;
  }

  .checkout-side {
    padding-top: 0;
  }

  .summary-card {
    position: static;
  }
}

@media (max-width: 700px) {
  .checkout-page {
    padding: 26px 16px 40px;
  }

  .checkout-heading {
    margin-bottom: 20px;
  }

  .checkout-card,
  .summary-card {
    padding: 20px;
    border-radius: 20px;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }

  .saved-address-box {
    flex-direction: column;
    align-items: flex-start;
  }

  .address-actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-header,
  .summary-item {
    grid-template-columns: 1fr;
  }

  .summary-item {
    gap: 10px;
  }
}
</style>
