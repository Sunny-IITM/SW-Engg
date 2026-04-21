<template>
  <div class="card h-100 product-card">
    <img v-if="product.image" :src="product.image" class="card-img-top product-image" />
    <div v-else class="product-image product-image-empty">No image</div>

    <div class="card-body product-body">
      <div class="product-top">
        <div class="product-heading">
          <h5 class="product-title">{{ product.name }}</h5>
        </div>

        <span v-if="product.category" class="category-badge">
          {{ product.category }}
        </span>
      </div>

      <div class="stock-row">
        <span :class="['stock-badge', product.stock > 0 ? 'in-stock' : 'out-of-stock']">
          {{ product.stock > 0 ? `${product.stock} in stock` : "Out of stock" }}
        </span>
      </div>

      <p class="text-muted small product-description">
        {{ product.description || "Authentic handcrafted kulhad ready for your next chai serving." }}
      </p>

      <div class="price-row">
        <h5 class="price">Rs {{ product.price }}</h5>
        <span class="volume">
          {{ product.stock > 0 ? `${product.stock} in stock` : "Out of stock" }}
        </span>
      </div>

      <button
        class="btn btn-dark w-100"
        :disabled="product.stock <= 0"
        @click="handleAddToCart"
      >
        Add to Cart
      </button>
    </div>
  </div>
</template>

<script>
import { useRouter } from "vue-router"
import { getAuthSession } from "../services/auth"
import { useCart } from "../store/cart"

export default {
  props: ["product"],
  setup() {
    const router = useRouter()
    const { addToCart } = useCart()

    return {
      addToCart,
      router
    }
  },
  emits: ["added-to-cart"],
  methods: {
    handleAddToCart() {
      const session = getAuthSession()

      if (!session?.token) {
        this.router.push({
          path: "/login",
          query: {
            intent: "cart",
            next: "/store"
          }
        })
        return
      }

      const wasAdded = this.addToCart(this.product)

      if (wasAdded) {
        this.$emit("added-to-cart", this.product)
      }
    }
  }
}
</script>

<style>
.product-card {
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  border: none;
  border-radius: 16px;
  overflow: hidden;
}

.product-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.product-image {
  width: 100%;
  height: 240px;
  display: block;
  object-fit: cover;
  background: #f3ead8;
}

.product-image-empty {
  display: flex;
  height: 240px;
  align-items: center;
  justify-content: center;
  color: #7a5330;
  font-weight: 600;
}

.product-body {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
}

.product-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  min-height: 56px;
}

.product-heading {
  flex: 1;
  min-width: 0;
}

.product-title {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.35;
}

.stock-row {
  margin: 10px 0 8px;
}

.category-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #6b7280;
  color: white;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.stock-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.in-stock {
  background: #dcfce7;
  color: #166534;
}

.out-of-stock {
  background: #fee2e2;
  color: #991b1b;
}

.product-description {
  margin: 0 0 16px;
  line-height: 1.5;
  min-height: 60px;
}

.price {
  color: #b45309;
  font-weight: bold;
  margin: 0;
}

.price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin-bottom: 1rem;
}

.volume {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.product-body .btn {
  margin-top: auto;
}
</style>
