<template>
  <section class="hero">
    <div class="hero-content">
      <p v-if="session?.token" class="welcome-chip">
        Welcome back, {{ session.name || "there" }}
      </p>

      <h1>Experience Chai in <br /> Traditional Kulhad</h1>

      <p>
        Handcrafted clay cups that bring authentic taste and eco-friendly elegance to your tea time.
      </p>

      <div class="hero-buttons">
        <router-link to="/store">
          <button class="primary">Shop Now -></button>
        </router-link>

        <router-link :to="accountLink">
          <button class="secondary">{{ accountLabel }}</button>
        </router-link>
      </div>
    </div>

    <button class="scroll-indicator" type="button" @click="scrollToProducts">
      <span>Scroll to explore</span>
      <span class="scroll-arrow" aria-hidden="true">v</span>
    </button>
  </section>

  <section class="features reveal-on-scroll reveal-up">
    <div class="feature feature-slide">
      <div class="icon">1</div>
      <h3>Pure Clay</h3>
      <p>Made from natural clay without chemicals or synthetic additives.</p>
    </div>

    <div class="feature feature-slide">
      <div class="icon">2</div>
      <h3>Sustainable</h3>
      <p>Biodegradable drinkware that feels traditional and responsible.</p>
    </div>

    <div class="feature feature-slide">
      <div class="icon">3</div>
      <h3>Artisan Made</h3>
      <p>Each kulhad is shaped with care for a warm and authentic serving experience.</p>
    </div>
  </section>

  <section class="products reveal-on-scroll reveal-left">
    <h2>Featured Products</h2>
    <p class="subtitle">Discover our most popular kulhads</p>

    <div v-if="isLoadingProducts" class="product-state">
      Loading featured products...
    </div>

    <div v-else-if="productError" class="product-state error">
      {{ productError }}
    </div>

    <div v-else-if="featuredProducts.length === 0" class="product-state">
      No featured products available right now.
    </div>

    <div v-else class="grid">
      <div class="card" v-for="product in featuredProducts" :key="product.id">
        <img v-if="product.image" :src="product.image" :alt="product.name" loading="lazy" />
        <div v-else class="image-fallback">No image</div>

        <div class="body">
          <h3>{{ product.name }}</h3>
          <p>{{ product.description }}</p>
        </div>
      </div>
    </div>

    <router-link to="/store">
      <button class="view">View All Products</button>
    </router-link>
  </section>

  <section class="cta reveal-on-scroll reveal-scale">
    <h2>About Us</h2>
    <p>Discover our story, the artisans behind our kulhads, and the tradition we bring to every cup.</p>

    <router-link to="/about">
      <button>About Us</button>
    </router-link>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { buildProductImageUrl, getProducts } from "../services/api"
import { getAuthSession } from "../services/auth"

const session = getAuthSession()
const featuredProducts = ref([])
const isLoadingProducts = ref(true)
const productError = ref("")
let observer
let scrollFrame = null

const accountLink = computed(() => {
  if (session?.role === "admin") {
    return "/admin"
  }

  if (session?.role === "employee") {
    return "/employee"
  }

  if (session?.token) {
    return "/account"
  }

  return "/login"
})

const accountLabel = computed(() => {
  if (session?.role === "admin" || session?.role === "employee") {
    return "Open Dashboard"
  }

  if (session?.token) {
    return "My Account"
  }

  return "Login"
})

const easeInOutCubic = (value) => {
  return value < 0.5
    ? 4 * value * value * value
    : 1 - Math.pow(-2 * value + 2, 3) / 2
}

function normalizeProduct(product) {
  return {
    id: product.id,
    name: product.name || "Kulhad Product",
    description: product.description || "Handcrafted kulhad from the Kulhad Shop collection.",
    image: buildProductImageUrl(product.image)
  }
}

async function loadFeaturedProducts() {
  isLoadingProducts.value = true
  productError.value = ""

  try {
    const products = await getProducts()
    featuredProducts.value = products.slice(0, 4).map(normalizeProduct)
  } catch (error) {
    productError.value = error.message || "Unable to load featured products."
  } finally {
    isLoadingProducts.value = false
  }
}

const scrollToProducts = () => {
  const productsSection = document.querySelector(".products")

  if (!productsSection) {
    return
  }

  const startY = window.scrollY
  const targetY = productsSection.getBoundingClientRect().top + window.scrollY
  const duration = 1400
  const startTime = performance.now()

  if (scrollFrame) {
    cancelAnimationFrame(scrollFrame)
  }

  const animateScroll = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const easedProgress = easeInOutCubic(progress)
    const nextY = startY + (targetY - startY) * easedProgress

    window.scrollTo(0, nextY)

    if (progress < 1) {
      scrollFrame = requestAnimationFrame(animateScroll)
    }
  }

  scrollFrame = requestAnimationFrame(animateScroll)
}

onMounted(() => {
  loadFeaturedProducts()

  const elements = document.querySelectorAll(".reveal-on-scroll")
  const featureCards = document.querySelectorAll(".feature-slide")

  observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("show")
        observer.unobserve(entry.target)
      }
    })
  }, {
    threshold: 0.3,
    rootMargin: "0px 0px -12% 0px"
  })

  elements.forEach((el) => observer.observe(el))
  featureCards.forEach((card) => observer.observe(card))
})

onBeforeUnmount(() => {
  observer?.disconnect()
  if (scrollFrame) {
    cancelAnimationFrame(scrollFrame)
  }
})
</script>

<style scoped>
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-image: url("https://images.unsplash.com/photo-1623671100816-fa8bc447e37c");
  background-size: cover;
  background-position: center;
  min-height: 100vh;
  padding: 80px 10%;
  position: relative;
  color: white;
}

.hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.4));
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 600px;
}

.welcome-chip {
  display: inline-flex;
  margin: 0 0 14px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: 13px;
  font-weight: 700;
}

.scroll-indicator {
  position: absolute;
  left: 50%;
  bottom: 28px;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  z-index: 1;
  transform: translateX(-50%);
  padding: 0;
  border: none;
  background: transparent;
  color: white;
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  transition: color 0.3s ease, transform 0.3s ease;
}

.scroll-indicator:hover {
  color: #f9e5c5;
  transform: translateX(-50%) translateY(-2px);
}

.scroll-arrow {
  font-size: 18px;
  line-height: 1;
  animation: floatArrow 1.6s ease-in-out infinite;
}

.hero h1 {
  margin: 0;
  font-size: 48px;
  line-height: 1.1;
  animation: fadeSlide 1s ease forwards;
}

.hero p {
  margin: 20px 0 0;
  color: #eee;
  font-size: 18px;
  line-height: 1.7;
  animation: fadeSlide 1.4s ease forwards;
}

.hero-buttons {
  display: flex;
  gap: 12px;
  margin-top: 28px;
}

.primary {
  background: #8b4513;
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  border: none;
  transition: 0.3s;
}

.primary:hover {
  background: #a0522d;
  transform: translateY(-2px);
}

.secondary {
  border: 1px solid white;
  padding: 12px 20px;
  color: white;
  background: transparent;
  border-radius: 8px;
  transition: 0.3s;
}

.secondary:hover {
  background: white;
  color: #8b4513;
}

.features {
  display: flex;
  justify-content: space-around;
  padding: 60px 10%;
  background: #f5f5f5;
  text-align: center;
}

.feature {
  transition: 0.3s;
}

.feature-slide {
  opacity: 0;
  transform: translateX(64px);
  transition: opacity 0.8s ease, transform 0.8s ease;
}

.feature-slide:nth-child(2) {
  transition-delay: 0.12s;
}

.feature-slide:nth-child(3) {
  transition-delay: 0.24s;
}

.feature-slide.show {
  opacity: 1;
  transform: translateX(0);
}

.feature:hover {
  transform: translateY(-5px);
}

.icon {
  width: 42px;
  height: 42px;
  margin: 0 auto 10px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: #ead8bf;
  color: #8b4513;
  font-weight: 700;
}

.products {
  padding: 80px 10%;
  background: #e8dfcf;
  text-align: center;
  border-top: 1px solid #ddd;
}

.products h2 {
  color: #8b4513;
  font-size: 34px;
}

.subtitle {
  margin-bottom: 30px;
  color: #666;
}

.product-state {
  margin: 0 auto 24px;
  max-width: 560px;
  padding: 14px 16px;
  border-radius: 10px;
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fdba74;
}

.product-state.error {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fca5a5;
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 25px;
}

.card {
  background: #f9f6f1;
  border-radius: 16px;
  overflow: hidden;
  text-align: left;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  cursor: pointer;
}

.card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
}

.card img,
.image-fallback {
  width: 100%;
  height: 220px;
  object-fit: cover;
  background: #f3ead8;
}

.image-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7a5330;
  font-weight: 600;
}

.body {
  padding: 16px;
}

.body p {
  font-size: 14px;
  color: #666;
}

.view {
  margin-top: 30px;
  padding: 10px 22px;
  border: 1px solid #8b4513;
  background: transparent;
  color: #8b4513;
  border-radius: 8px;
  transition: 0.3s;
}

.view:hover {
  background: #8b4513;
  color: white;
}

.cta {
  background: linear-gradient(135deg, #8b4513, #a0522d);
  color: white;
  padding: 80px;
  text-align: center;
}

.cta button {
  margin-top: 20px;
  background: white;
  color: #8b4513;
  padding: 12px 22px;
  border-radius: 8px;
  border: none;
  transition: 0.3s;
}

.cta button:hover {
  transform: scale(1.05);
}

.reveal-on-scroll {
  opacity: 0;
  transition: opacity 0.85s ease, transform 0.85s ease;
}

.reveal-up {
  transform: translateY(48px);
}

.reveal-left {
  transform: translateX(56px);
}

.reveal-scale {
  transform: translateY(36px) scale(0.96);
}

.reveal-on-scroll.show {
  opacity: 1;
  transform: translate(0, 0) scale(1);
}

@keyframes fadeSlide {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes floatArrow {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(5px);
  }
}

@media (max-width: 1000px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .features {
    flex-wrap: wrap;
    gap: 20px;
  }
}

@media (max-width: 640px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .hero h1 {
    font-size: 32px;
  }

  .hero-buttons {
    flex-direction: column;
  }

  .scroll-indicator {
    bottom: 20px;
    font-size: 12px;
  }
}
</style>
