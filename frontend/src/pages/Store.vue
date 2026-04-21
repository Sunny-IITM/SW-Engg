<template>
  <section class="hero">
    <div class="hero-content">
      <h1>Authentic Handcrafted Kulhads</h1>
      <p>
        Experience the traditional taste of chai in our eco-friendly clay cups
      </p>
    </div>
  </section>

  <div class="store-container">
    <div v-if="loginMessage" class="status-card success">
      {{ loginMessage }}
    </div>

    <transition name="toast-fade">
      <div v-if="cartMessage" class="cart-toast">
        {{ cartMessage }}
      </div>
    </transition>

    <div class="top-bar">
      <CategoryFilter
        :categories="availableCategories"
        :selected="selectedCategory"
        @change-category="filterCategory"
      />

      <router-link
        to="/cart"
        :class="['cart-btn', 'text-decoration-none', { pulse: cartButtonPulse }]"
      >
        Cart ({{ itemCount }})
      </router-link>
    </div>

    <div v-if="isLoading" class="status-card">
      Loading products from the backend...
    </div>

    <div v-else-if="errorMessage" class="status-card error">
      {{ errorMessage }}
    </div>

    <ProductGrid :products="filteredProducts" @added-to-cart="showCartMessage" />
  </div>
</template>

<script>
import { useRoute } from "vue-router"
import CategoryFilter from "../components/CategoryFilter.vue"
import ProductGrid from "../components/ProductGrid.vue"
import { buildProductImageUrl, getProducts } from "../services/api"
import { useCart } from "../store/cart"

export default {
  setup() {
    const route = useRoute()
    const { itemCount, lastAddedAt } = useCart()

    return {
      route,
      itemCount,
      lastAddedAt
    }
  },

  components: {
    CategoryFilter,
    ProductGrid
  },

  data() {
    return {
      selectedCategory: "All",
      products: [],
      isLoading: true,
      errorMessage: "",
      cartMessage: "",
      cartMessageTimeoutId: null,
      cartButtonPulse: false,
      cartButtonPulseTimeoutId: null
    }
  },

  computed: {
    loginMessage() {
      if (this.route.query.login === "success") {
        return "Logged in successfully."
      }

      return ""
    },

    availableCategories() {
      const categories = this.products
        .map((product) => product.category)
        .filter(Boolean)

      return ["All", ...new Set(categories)]
    },

    filteredProducts() {
      if (this.selectedCategory === "All") {
        return this.products
      }

      return this.products.filter(
        (product) => product.category === this.selectedCategory
      )
    }
  },

  methods: {
    filterCategory(category) {
      this.selectedCategory = category
    },

    showCartMessage(product) {
      this.cartMessage = `${product.name} added to cart`

      if (this.cartMessageTimeoutId) {
        clearTimeout(this.cartMessageTimeoutId)
      }

      this.cartMessageTimeoutId = window.setTimeout(() => {
        this.cartMessage = ""
        this.cartMessageTimeoutId = null
      }, 1800)

      this.cartButtonPulse = false

      if (this.cartButtonPulseTimeoutId) {
        clearTimeout(this.cartButtonPulseTimeoutId)
      }

      window.setTimeout(() => {
        this.cartButtonPulse = true
        this.cartButtonPulseTimeoutId = window.setTimeout(() => {
          this.cartButtonPulse = false
          this.cartButtonPulseTimeoutId = null
        }, 500)
      }, 0)
    },

    normalizeProduct(product) {
      return {
        ...product,
        category: product.category || "",
        description:
          product.description || "Handcrafted kulhad from the Kulhad Shop collection.",
        image: buildProductImageUrl(product.image),
        volume: product.volume || "",
        stock: Number(product.stock ?? 0)
      }
    },

    async loadProducts() {
      this.isLoading = true
      this.errorMessage = ""

      try {
        const products = await getProducts()
        this.products = products.map(this.normalizeProduct)
      } catch (error) {
        this.errorMessage = error.message || "Unable to load products right now."
      } finally {
        this.isLoading = false
      }
    }
  },

  mounted() {
    this.loadProducts()
  },

  beforeUnmount() {
    if (this.cartMessageTimeoutId) {
      clearTimeout(this.cartMessageTimeoutId)
    }

    if (this.cartButtonPulseTimeoutId) {
      clearTimeout(this.cartButtonPulseTimeoutId)
    }
  }
}
</script>

<style scoped>
.hero {
  background: linear-gradient(90deg, #a94d00, #8b3e00);
  color: white;
  padding: 60px 10%;
}

.hero-content {
  max-width: 700px;
}

.hero h1 {
  font-size: 36px;
  font-weight: 700;
}

.hero p {
  margin-top: 10px;
  opacity: 0.9;
}

.store-container {
  max-width: 1200px;
  margin: auto;
  padding: 30px 20px;
}

.cart-toast {
  position: fixed;
  top: 78px;
  right: 24px;
  z-index: 1000;
  width: fit-content;
  max-width: min(calc(100vw - 32px), 420px);
  padding: 12px 16px;
  border-radius: 999px;
  background: #166534;
  color: white;
  box-shadow: 0 14px 24px rgba(22, 101, 52, 0.22);
  font-weight: 600;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.status-card {
  margin-bottom: 24px;
  padding: 14px 16px;
  border-radius: 10px;
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fdba74;
}

.status-card.error {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fca5a5;
}

.status-card.success {
  background: #ecfdf3;
  color: #166534;
  border-color: #86efac;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  gap: 16px;
  flex-wrap: wrap;
}

.top-bar :deep(.category-filter) {
  justify-content: flex-start;
}

.cart-btn {
  background: #0b0f1a;
  color: white;
  padding: 10px 16px;
  border-radius: 8px;
  font-weight: 500;
  transition: 0.2s;
}

.cart-btn.pulse {
  animation: cartButtonPulse 0.5s ease;
}

.cart-btn:hover {
  opacity: 0.9;
  color: white;
}

@keyframes cartButtonPulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 rgba(11, 15, 26, 0);
  }
  45% {
    transform: scale(1.07);
    box-shadow: 0 12px 24px rgba(11, 15, 26, 0.22);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 rgba(11, 15, 26, 0);
  }
}

@media (max-width: 768px) {
  .hero h1 {
    font-size: 26px;
  }

  .cart-toast {
    top: 72px;
    right: 16px;
  }

  .top-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .top-bar :deep(.category-filter) {
    width: 100%;
  }
}
</style>
