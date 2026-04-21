<script setup>
import { computed, ref } from "vue"
import { useCart } from "../store/cart"

const freeShippingThreshold = 500
const { items, updateQuantity, removeFromCart } = useCart()
const quantityHints = ref({})

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
const remainingForFreeShipping = computed(() =>
  Math.max(freeShippingThreshold - subtotal.value, 0)
)

function decreaseQuantity(item) {
  updateQuantity(item.id, item.qty - 1)
}

function increaseQuantity(item) {
  updateQuantity(item.id, item.qty + 1)
}

function showStockHint(item) {
  quantityHints.value = {
    ...quantityHints.value,
    [item.id]: `Only ${item.stock} item(s) available in stock.`
  }

  window.clearTimeout(quantityHints.value[`${item.id}-timeout`])

  const timeoutId = window.setTimeout(() => {
    const nextHints = { ...quantityHints.value }
    delete nextHints[item.id]
    delete nextHints[`${item.id}-timeout`]
    quantityHints.value = nextHints
  }, 1800)

  quantityHints.value = {
    ...quantityHints.value,
    [`${item.id}-timeout`]: timeoutId
  }
}

function setQuantity(item, event) {
  const rawValue = event.target.value

  if (rawValue === "") {
    event.target.value = item.qty
    return
  }

  const nextQuantity = Number(rawValue)

  if (!Number.isFinite(nextQuantity)) {
    event.target.value = item.qty
    return
  }

  const requestedQuantity = Math.max(1, Math.floor(nextQuantity))
  const clampedQuantity = Math.min(
    requestedQuantity,
    Math.max(item.stock, 1)
  )

  if (requestedQuantity > item.stock) {
    showStockHint(item)
  }

  updateQuantity(item.id, clampedQuantity)
  event.target.value = clampedQuantity
}

function handleBackspace(item, event) {
  if (event.key !== "Backspace") {
    return
  }

  if (item.qty >= 10) {
    return
  }

  event.preventDefault()

  if (item.qty > 1) {
    updateQuantity(item.id, item.qty - 1)
    event.target.value = item.qty
  }
}
</script>

<template>
  <div class="cart-page">
    <h1>Shopping Cart</h1>
    <p class="sub">{{ items.length }} item(s) in your cart</p>

    <div v-if="items.length && remainingForFreeShipping > 0" class="alert">
      Add Rs {{ remainingForFreeShipping }} more to get <b>FREE SHIPPING!</b>
    </div>

    <div v-if="items.length" class="layout">
      <div>
        <div v-for="item in items" :key="item.id" class="item-card">
          <img
            :src="item.image || 'https://via.placeholder.com/100?text=Kulhad'"
            :alt="item.name"
          />

          <div class="item-info">
            <h3>{{ item.name }}</h3>
            <p v-if="item.size" class="size">{{ item.size }}</p>

            <div class="price-row">
              <span class="price">Rs {{ item.price }}</span>
              <span class="stock">{{ item.stock }} in stock</span>
            </div>

            <div class="qty-box">
              <button
                class="qty-btn"
                @click="decreaseQuantity(item)"
                :disabled="item.qty <= 1"
              >
                -
              </button>

              <input
                class="qty-input"
                type="number"
                min="1"
                :max="item.stock"
                step="1"
                :value="item.qty"
                @keydown.backspace="handleBackspace(item, $event)"
                @input="setQuantity(item, $event)"
                @blur="setQuantity(item, $event)"
              />

              <button
                class="qty-btn"
                @click="increaseQuantity(item)"
                :disabled="item.qty >= item.stock"
              >
                +
              </button>
            </div>

            <p v-if="quantityHints[item.id]" class="qty-hint">
              {{ quantityHints[item.id] }}
            </p>

            <p class="subtotal">Subtotal: Rs {{ item.price * item.qty }}</p>
          </div>

          <button class="delete" @click="removeFromCart(item.id)" aria-label="Remove item from cart">
            🗑
          </button>
        </div>
      </div>

      <div class="summary">
        <h2>Order Summary</h2>

        <div class="row">
          <span>Subtotal</span>
          <span>Rs {{ subtotal }}</span>
        </div>

        <div class="row">
          <span>Shipping</span>
          <span>Rs {{ shipping }}</span>
        </div>

        <hr />

        <div class="total">
          <span>Total</span>
          <span>Rs {{ total }}</span>
        </div>

        <router-link to="/checkout" class="checkout-link">
          <button class="checkout">Proceed to Checkout</button>
        </router-link>

        <router-link to="/store">
          <button class="secondary">Continue Shopping</button>
        </router-link>

        <div class="notes">
          <p>Secure checkout</p>
          <p>Free shipping on orders over Rs 500</p>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>Your cart is empty.</p>
      <router-link to="/store" class="continue-link">Browse products</router-link>
    </div>
  </div>
</template>

<style scoped>
.cart-page {
  background: #f3ead8;
  padding: 40px 10%;
}

.sub {
  margin-bottom: 20px;
  color: #555;
}

.empty-state {
  background: white;
  padding: 32px;
  border-radius: 12px;
  text-align: center;
}

.continue-link {
  color: #8b4513;
  font-weight: 600;
  text-decoration: none;
}

.alert {
  background: #fff3cd;
  border: 1px solid #f0c36d;
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 20px;
}

.layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 25px;
}

.item-card {
  display: flex;
  gap: 15px;
  background: white;
  padding: 15px;
  border-radius: 12px;
  margin-bottom: 15px;
  align-items: center;
  position: relative;
}

.item-card img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 10px;
}

.item-info {
  flex: 1;
}

.size {
  color: #777;
  font-size: 14px;
}

.price {
  font-weight: bold;
  color: #8b4513;
}

.stock {
  background: #d4edda;
  color: #2e7d32;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
}

.qty-box {
  display: inline-flex;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 10px;
  overflow: hidden;
  margin: 10px 0;
}

.qty-btn {
  background: #f5f5f5;
  border: none;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 16px;
  transition: 0.2s;
}

.qty-btn:hover {
  background: #e0e0e0;
}

.qty-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.qty-input {
  width: 56px;
  border: none;
  border-left: 1px solid #ddd;
  border-right: 1px solid #ddd;
  text-align: center;
  padding: 6px 4px;
  font-weight: 500;
  background: white;
}

.qty-input:focus {
  outline: none;
  background: #fffaf3;
}

.qty-input::-webkit-outer-spin-button,
.qty-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.qty-input[type="number"] {
  -moz-appearance: textfield;
}

.qty-hint {
  margin: -2px 0 8px;
  color: #b45309;
  font-size: 12px;
  font-weight: 600;
}

.subtotal {
  font-size: 14px;
  color: #555;
}

.delete {
  position: absolute;
  right: 10px;
  top: 10px;
  background: none;
  border: none;
  padding: 0;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.summary {
  background: white;
  padding: 20px;
  border-radius: 12px;
}

.row {
  display: flex;
  justify-content: space-between;
  margin: 10px 0;
}

.total {
  display: flex;
  justify-content: space-between;
  font-weight: bold;
  margin: 15px 0;
}

.checkout {
  width: 100%;
  background: #8b4513;
  color: white;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 10px;
  border: none;
}

.checkout-link {
  display: block;
}

.secondary {
  width: 100%;
  border: 1px solid #8b4513;
  padding: 10px;
  background: transparent;
  border-radius: 8px;
}

.notes {
  margin-top: 15px;
  font-size: 13px;
  color: #555;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
