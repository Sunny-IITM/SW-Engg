import { computed, reactive } from "vue"
import { buildProductImageUrl } from "../services/api"

const CART_STORAGE_KEY = "kullad-cart"

function readStoredCart() {
  const rawCart = localStorage.getItem(CART_STORAGE_KEY)

  if (!rawCart) {
    return []
  }

  try {
    const parsedCart = JSON.parse(rawCart)
    return Array.isArray(parsedCart)
      ? parsedCart.map((item) => ({
          ...item,
          image: buildProductImageUrl(item.image)
        }))
      : []
  } catch {
    localStorage.removeItem(CART_STORAGE_KEY)
    return []
  }
}

const state = reactive({
  items: readStoredCart(),
  lastAddedAt: 0
})

function persistCart() {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(state.items))
}

function normalizeCartItem(product) {
  return {
    id: product.id,
    name: product.name,
    price: Number(product.price ?? 0),
    qty: 1,
    image: buildProductImageUrl(product.image),
    size: product.volume || "",
    stock: Number(product.stock ?? 0)
  }
}

function addToCart(product) {
  const productStock = Number(product.stock ?? 0)

  if (productStock <= 0) {
    return false
  }

  const existingItem = state.items.find((item) => item.id === product.id)

  if (existingItem) {
    existingItem.stock = productStock

    if (existingItem.qty >= productStock) {
      return false
    }

    existingItem.qty += 1
  } else {
    state.items.push(normalizeCartItem(product))
  }

  state.lastAddedAt = Date.now()
  persistCart()
  return true
}

function addItemsToCart(products = []) {
  let addedCount = 0

  products.forEach((product) => {
    const requestedQuantity = Number(product.qty ?? product.quantity ?? 1)
    if (requestedQuantity <= 0) {
      return
    }

    for (let index = 0; index < requestedQuantity; index += 1) {
      const wasAdded = addToCart(product)
      if (!wasAdded) {
        break
      }
      addedCount += 1
    }
  })

  return addedCount
}

function updateQuantity(productId, quantity) {
  const item = state.items.find((entry) => entry.id === productId)

  if (!item) {
    return
  }

  if (quantity <= 0) {
    removeFromCart(productId)
    return
  }

  const maxQuantity = item.stock > 0 ? item.stock : quantity
  item.qty = Math.min(quantity, maxQuantity)
  persistCart()
}

function removeFromCart(productId) {
  const itemIndex = state.items.findIndex((item) => item.id === productId)

  if (itemIndex === -1) {
    return
  }

  state.items.splice(itemIndex, 1)
  persistCart()
}

function clearCart() {
  state.items.splice(0, state.items.length)
  persistCart()
}

const itemCount = computed(() =>
  state.items.reduce((total, item) => total + item.qty, 0)
)

export function useCart() {
  return {
    items: state.items,
    itemCount,
    lastAddedAt: computed(() => state.lastAddedAt),
    addToCart,
    addItemsToCart,
    updateQuantity,
    removeFromCart,
    clearCart
  }
}
