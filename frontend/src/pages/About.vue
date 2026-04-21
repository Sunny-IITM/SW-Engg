<script setup>
import { onBeforeUnmount, onMounted } from "vue"
import coreFourLogo from "../assets/cf.jpeg"
import arnavMehtaPhoto from "../assets/Arnav Mehta.jpeg"
import reneePhoto from "../assets/renee.jpeg"
import sunnyPhoto from "../assets/sunny.jpeg"
import surajPhoto from "../assets/suraj.jpeg"

const storyMoments = [
  {
    title: "The Art of Clay",
    lead: "Every kulhad begins with skilled hands shaping raw clay on a traditional potter's wheel.",
    body: "That rhythm of hand, earth, and motion is where the experience starts. We keep the process close to its roots so every piece carries the warmth of real craft.",
    image: "https://images.unsplash.com/photo-1767032485205-3eb089e5dc33?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHw1fHxwb3R0ZXIlMjB3b3JraW5nJTIwY2VyYW1pY3MlMjB3b3Jrc2hvcHxlbnwxfHx8fDE3NzQ5NjgyMDd8MA&ixlib=rb-4.1.0&q=80&w=1080",
    alt: "Artisan hands shaping clay"
  },
  {
    title: "Rooted in Tradition",
    lead: "We work to preserve India's pottery heritage by connecting timeless craft with modern access.",
    body: "Every order supports artisan communities and helps keep inherited techniques alive in everyday life, not just in museums or memories.",
    image: "https://images.unsplash.com/photo-1753164726495-9e5577228f1a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwb3R0ZXIlMjB3b3JraW5nJTIwY2VyYW1pY3MlMjB3b3Jrc2hvcHxlbnwxfHx8fDE3NzQ5NjgyMDd8MA&ixlib=rb-4.1.0&q=80&w=1080",
    alt: "Potter shaping pottery"
  },
  {
    title: "Handcrafted with Care",
    lead: "Each kulhad is shaped, dried, and kiln-fired with patience rather than shortcuts.",
    body: "That slower process creates texture, character, and an earthy drinking experience that feels different from mass-produced ware.",
    image: "https://images.unsplash.com/photo-1662845114342-256fdc45981d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHw4fHxwb3R0ZXIlMjB3b3JraW5nJTIwY2VyYW1pY3MlMjB3b3Jrc2hvcHxlbnwxfHx8fDE3NzQ5NjgyMDd8MA&ixlib=rb-4.1.0&q=80&w=1080",
    alt: "Artisan holding pottery"
  },
  {
    title: "Our Commitment",
    lead: "We care about fair trade, sustainability, and giving traditional craft a stronger digital future.",
    body: "Kulhad Shop exists to make heritage feel usable, visible, and valued in daily life while staying respectful to the people behind the work.",
    image: "https://images.unsplash.com/photo-1590605103416-230704277b05?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHw5fHxwb3R0ZXIlMjB3b3JraW5nJTIwY2VyYW1pY3MlMjB3b3Jrc2hvcHxlbnwxfHx8fDE3NzQ5NjgyMDd8MA&ixlib=rb-4.1.0&q=80&w=1080",
    alt: "Ceramic bowl"
  }
]

const values = [
  { eyebrow: "Authentic", title: "Traditional Craft", text: "Real kulhads shaped through time-tested methods and artisan skill.", theme: "sand" },
  { eyebrow: "Sustainable", title: "Natural Materials", text: "Clay-first products that feel grounded, biodegradable, and responsible.", theme: "sage" },
  { eyebrow: "Fair Trade", title: "People First", text: "Every purchase contributes to artisan visibility and community support.", theme: "terracotta" },
  { eyebrow: "Experience", title: "Flavor & Feel", text: "We design for the ritual too: texture, aroma, warmth, and memory.", theme: "amber" }
]

const teamMembers = [
  {
    name: "Suraj Kumar",
    role: "Frontend Developer",
    image: surajPhoto,
    description: "Builds responsive, interactive interfaces and shapes the visual feel of the product."
  },
  {
    name: "Sunny Kumar Gupta",
    role: "Backend Engineer",
    image: sunnyPhoto,
    description: "Owns robust APIs, data flow, and the system foundations that keep the platform reliable."
  },
  {
    name: "Renee Keerthana Paturi",
    role: "Product Manager & Scrum Master",
    image: reneePhoto,
    description: "Connects planning, delivery, and team coordination so ideas move into working features."
  },
  {
    name: "Arnav Mehta",
    role: "Code Reviewer & Tester",
    image: arnavMehtaPhoto,
    description: "Strengthens quality through careful review, testing, and attention to edge cases."
  }
]

const stackCards = [
  {
    title: "Vue + Vite",
    text: "A fast, component-driven frontend that supports a smooth shopping and admin experience.",
    theme: "blue"
  },
  {
    title: "Flask + SQLAlchemy",
    text: "A practical backend foundation for orders, inventory, payroll, and operational workflows.",
    theme: "cyan"
  },
  {
    title: "Full Workflow Design",
    text: "Customer storefront, employee tooling, and admin operations working together in one system.",
    theme: "indigo"
  }
]

let observer
let pointerHandler

function applyTilt(card, event) {
  const rect = card.getBoundingClientRect()
  const x = (event.clientX - rect.left) / rect.width
  const y = (event.clientY - rect.top) / rect.height
  const rotateX = (0.5 - y) * 10
  const rotateY = (x - 0.5) * 12

  card.style.setProperty("--tilt-x", `${rotateX.toFixed(2)}deg`)
  card.style.setProperty("--tilt-y", `${rotateY.toFixed(2)}deg`)
}

function resetTilt(card) {
  card.style.setProperty("--tilt-x", "0deg")
  card.style.setProperty("--tilt-y", "0deg")
}

function scrollToStory() {
  const target = document.querySelector(".story-section")
  if (!target) {
    return
  }

  target.scrollIntoView({
    behavior: "smooth",
    block: "start"
  })
}

onMounted(() => {
  const revealTargets = document.querySelectorAll(".reveal-on-scroll")
  const tiltCards = document.querySelectorAll(".tilt-card")

  observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("show")
        observer.unobserve(entry.target)
      }
    })
  }, {
    threshold: 0.2,
    rootMargin: "0px 0px -10% 0px"
  })

  revealTargets.forEach((element) => observer.observe(element))

  pointerHandler = (event) => {
    tiltCards.forEach((card) => {
      const bounds = card.getBoundingClientRect()
      const inside =
        event.clientX >= bounds.left &&
        event.clientX <= bounds.right &&
        event.clientY >= bounds.top &&
        event.clientY <= bounds.bottom

      if (inside) {
        applyTilt(card, event)
      }
    })
  }

  tiltCards.forEach((card) => {
    card.addEventListener("pointermove", pointerHandler)
    card.addEventListener("pointerleave", () => resetTilt(card))
  })
})

onBeforeUnmount(() => {
  observer?.disconnect()

  document.querySelectorAll(".tilt-card").forEach((card) => {
    if (pointerHandler) {
      card.removeEventListener("pointermove", pointerHandler)
    }
    resetTilt(card)
  })
})
</script>

<template>
  <div class="about-page">
    <section class="about-hero">
      <div class="hero-backdrop"></div>
      <div class="hero-orb orb-one"></div>
      <div class="hero-orb orb-two"></div>

      <div class="hero-copy reveal-on-scroll reveal-up show">
        <p class="eyebrow">About Kulhad Shop</p>
        <h1>Tradition, craftsmanship, and a digital storefront built with intention.</h1>
        <p class="hero-text">
          We’re preserving the ritual of chai in clay while building a modern experience around the people, process, and culture that make it meaningful.
        </p>

        <div class="hero-actions">
          <router-link to="/store" class="hero-link primary-link">Explore Products</router-link>
          <button type="button" class="hero-link secondary-link" @click="scrollToStory">Read Our Story</button>
        </div>
      </div>

      <div class="hero-panel reveal-on-scroll reveal-scale show">
        <div class="panel-chip">Crafted by artisans</div>
        <div class="hero-stats">
          <article>
            <strong>Earth</strong>
            <span>Natural materials and tactile design</span>
          </article>
          <article>
            <strong>Heritage</strong>
            <span>Traditional pottery made relevant online</span>
          </article>
          <article>
            <strong>Systems</strong>
            <span>Storefront, admin, inventory, payroll, and analytics in one workflow</span>
          </article>
        </div>
      </div>

      <button class="scroll-indicator" type="button" @click="scrollToStory">
        <span>Scroll to explore</span>
        <span class="scroll-arrow" aria-hidden="true">v</span>
      </button>
    </section>

    <section class="story-section">
      <div
        v-for="(moment, index) in storyMoments"
        :key="moment.title"
        :class="['story-band', index % 2 === 0 ? 'band-warm' : 'band-light']"
      >
        <div class="story-grid reveal-on-scroll" :class="index % 2 === 0 ? 'reveal-left' : 'reveal-right'">
          <div class="story-media tilt-card" :class="{ 'story-media-order': index % 2 === 1 }">
            <img :src="moment.image" :alt="moment.alt" class="story-image" />
          </div>

          <article class="story-copy">
            <p class="story-index">0{{ index + 1 }}</p>
            <h2>{{ moment.title }}</h2>
            <p class="story-lead">{{ moment.lead }}</p>
            <p class="story-body">{{ moment.body }}</p>
          </article>
        </div>
      </div>
    </section>

    <section class="values-section reveal-on-scroll reveal-up">
      <div class="section-intro">
        <p class="eyebrow">What We Value</p>
        <h2>Built around authenticity, responsibility, and human craft.</h2>
      </div>

      <div class="values-grid">
        <article
          v-for="value in values"
          :key="value.title"
          :class="['value-card', 'tilt-card', `theme-${value.theme}`]"
        >
          <p class="value-eyebrow">{{ value.eyebrow }}</p>
          <h3>{{ value.title }}</h3>
          <p>{{ value.text }}</p>
        </article>
      </div>
    </section>

    <section class="developer-section">
      <div class="developer-shell reveal-on-scroll reveal-scale">
        <div class="developer-header">
          <img :src="coreFourLogo" alt="CoreFour logo" class="developer-logo" />
          <p class="eyebrow eyebrow-light">Built By CoreFour</p>
          <h2>Engineering a storefront that respects craft and handles real operations.</h2>
          <p class="developer-subtitle">
            From browsing and checkout to inventory, employee logging, payroll, and analytics, the platform was designed as a complete working system.
          </p>
        </div>

        <div class="developer-copy">
          <article class="glass-card reveal-on-scroll reveal-left">
            <p>
              CoreFour approached Kulhad Shop as more than an e-commerce site. The goal was to create something that feels rooted in tradition on the outside while staying dependable and practical behind the scenes.
            </p>
            <p>
              That meant building a user-facing experience with warmth and clarity, while also supporting admin workflows, employee operations, and business visibility in one connected product.
            </p>
          </article>

          <article class="glass-card reveal-on-scroll reveal-right">
            <p>
              We focused on a system that can actually be used day to day: product management, order handling, raw inventory, stock flow, production logging, payroll summaries, and analytics all working together.
            </p>
            <p>
              The result is a platform that celebrates handmade work while solving practical workflow problems with software.
            </p>
          </article>
        </div>

        <div class="team-section reveal-on-scroll reveal-up">
          <div class="section-intro section-intro-light">
            <p class="eyebrow eyebrow-light">Meet The Team</p>
            <h3>The people behind the product.</h3>
          </div>

          <div class="team-grid">
            <article v-for="member in teamMembers" :key="member.name" class="team-card tilt-card">
              <div class="team-image-wrap">
                <img :src="member.image" :alt="member.name" class="team-image" />
              </div>
              <div class="team-card-body">
                <h4>{{ member.name }}</h4>
                <p class="team-role">{{ member.role }}</p>
                <p class="team-description">{{ member.description }}</p>
              </div>
            </article>
          </div>
        </div>

        <div class="stack-grid reveal-on-scroll reveal-up">
          <article v-for="card in stackCards" :key="card.title" :class="['stack-card', `stack-${card.theme}`]">
            <h3>{{ card.title }}</h3>
            <p>{{ card.text }}</p>
          </article>
        </div>

        <div class="closing-card reveal-on-scroll reveal-scale">
          <p class="closing-line">Thank you for being part of the Kulhad Shop journey.</p>
          <p class="closing-subline">Every visit, every order, and every interaction helps handmade tradition stay present in everyday life.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.about-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(244, 197, 143, 0.34), transparent 24%),
    linear-gradient(180deg, #f5ecdd 0%, #f8f4ed 45%, #10233b 100%);
}

.about-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 28px;
  align-items: center;
  min-height: 100vh;
  padding: 110px 8% 90px;
  overflow: hidden;
  color: white;
}

.hero-backdrop {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(120deg, rgba(25, 12, 4, 0.84), rgba(13, 34, 56, 0.68)),
    url("https://images.unsplash.com/photo-1623671100816-fa8bc447e37c?auto=format&fit=crop&w=1600&q=80") center/cover;
  transform: scale(1.04);
}

.hero-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(12px);
  opacity: 0.55;
}

.orb-one {
  top: 14%;
  right: 10%;
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(233, 146, 52, 0.7), transparent 70%);
  animation: drift 7s ease-in-out infinite;
}

.orb-two {
  bottom: 16%;
  left: 6%;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(85, 138, 205, 0.45), transparent 72%);
  animation: drift 9s ease-in-out infinite reverse;
}

.hero-copy,
.hero-panel,
.scroll-indicator {
  position: relative;
  z-index: 1;
}

.hero-copy {
  max-width: 720px;
}

.eyebrow {
  margin: 0 0 12px;
  color: #a0522d;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.eyebrow-light {
  color: #9bc9ff;
}

.hero-copy .eyebrow {
  color: #f2c58f;
}

.hero-copy h1 {
  margin: 0;
  font-size: clamp(2.8rem, 5vw, 5.2rem);
  line-height: 0.95;
  letter-spacing: -0.04em;
}

.hero-text {
  max-width: 620px;
  margin: 22px 0 0;
  color: rgba(255, 245, 230, 0.9);
  font-size: 1.1rem;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 30px;
}

.hero-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 168px;
  padding: 13px 18px;
  border-radius: 999px;
  text-decoration: none;
  font-weight: 700;
  transition: transform 0.3s ease, box-shadow 0.3s ease, background 0.3s ease, color 0.3s ease;
}

.primary-link {
  background: linear-gradient(135deg, #d9822b, #b85d18);
  color: white;
  box-shadow: 0 16px 30px rgba(116, 52, 15, 0.32);
}

.secondary-link {
  border: 1px solid rgba(255, 255, 255, 0.26);
  background: rgba(255, 255, 255, 0.08);
  color: white;
  cursor: pointer;
}

.hero-link:hover {
  transform: translateY(-3px);
}

.hero-panel {
  justify-self: end;
  width: min(100%, 430px);
  padding: 22px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 24px 60px rgba(4, 15, 28, 0.35);
  backdrop-filter: blur(14px);
}

.panel-chip {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(242, 197, 143, 0.16);
  color: #ffd6aa;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-stats {
  display: grid;
  gap: 16px;
  margin-top: 18px;
}

.hero-stats article {
  padding: 14px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.hero-stats article:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.hero-stats strong {
  display: block;
  margin-bottom: 6px;
  color: #ffffff;
  font-size: 1rem;
}

.hero-stats span {
  color: rgba(224, 236, 255, 0.82);
  line-height: 1.7;
}

.scroll-indicator {
  position: absolute;
  left: 50%;
  bottom: 26px;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
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

.story-band {
  padding: 72px 8%;
}

.band-warm {
  background: linear-gradient(180deg, rgba(248, 239, 224, 0.96), rgba(243, 232, 213, 0.96));
}

.band-light {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(249, 245, 238, 0.98));
}

.story-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 34px;
  align-items: center;
  max-width: 1240px;
  margin: 0 auto;
}

.story-media {
  --tilt-x: 0deg;
  --tilt-y: 0deg;
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  box-shadow: 0 26px 50px rgba(86, 50, 18, 0.18);
  transform: perspective(1200px) rotateX(var(--tilt-x)) rotateY(var(--tilt-y));
  transition: transform 0.22s ease, box-shadow 0.3s ease;
}

.story-media:hover {
  box-shadow: 0 34px 60px rgba(86, 50, 18, 0.24);
}

.story-media-order {
  order: 2;
}

.story-image {
  display: block;
  width: 100%;
  height: 520px;
  object-fit: cover;
  transition: transform 0.8s ease;
}

.story-media:hover .story-image {
  transform: scale(1.05);
}

.story-copy {
  padding: 10px 8px;
}

.story-index {
  margin: 0 0 8px;
  color: #d07b00;
  font-size: 0.85rem;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.story-copy h2 {
  margin: 0;
  color: #6e3812;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1;
}

.story-lead {
  margin: 20px 0 0;
  color: #3c2c1f;
  font-size: 1.18rem;
  line-height: 1.75;
}

.story-body {
  margin: 14px 0 0;
  color: #695847;
  font-size: 1rem;
  line-height: 1.9;
}

.values-section {
  padding: 88px 8%;
  background:
    radial-gradient(circle at 20% 20%, rgba(233, 203, 163, 0.28), transparent 26%),
    linear-gradient(180deg, #fff8ef 0%, #f4ebdd 100%);
}

.section-intro {
  max-width: 760px;
  margin: 0 auto 34px;
  text-align: center;
}

.section-intro h2,
.section-intro h3 {
  margin: 0;
  color: #4a2910;
  font-size: clamp(2rem, 4vw, 3.4rem);
  line-height: 1.02;
}

.section-intro-light h3 {
  color: white;
}

.values-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
  max-width: 1240px;
  margin: 0 auto;
}

.value-card {
  --tilt-x: 0deg;
  --tilt-y: 0deg;
  min-height: 220px;
  padding: 24px;
  border-radius: 24px;
  border: 1px solid rgba(110, 56, 18, 0.08);
  box-shadow: 0 18px 34px rgba(120, 75, 30, 0.1);
  transform: perspective(1200px) rotateX(var(--tilt-x)) rotateY(var(--tilt-y));
  transition: transform 0.22s ease, box-shadow 0.3s ease;
}

.value-card h3 {
  margin: 8px 0 10px;
  color: #4a2910;
  font-size: 1.3rem;
}

.value-card p:last-child {
  margin: 0;
  color: #5e4a36;
  line-height: 1.75;
}

.value-eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.theme-sand {
  background: linear-gradient(180deg, #fff9f0 0%, #f9ead5 100%);
}

.theme-sand .value-eyebrow {
  color: #a05921;
}

.theme-sage {
  background: linear-gradient(180deg, #f4faf0 0%, #e4f0dd 100%);
}

.theme-sage .value-eyebrow {
  color: #3f7b33;
}

.theme-terracotta {
  background: linear-gradient(180deg, #fff5f0 0%, #f5ddd1 100%);
}

.theme-terracotta .value-eyebrow {
  color: #b24e23;
}

.theme-amber {
  background: linear-gradient(180deg, #fff8ec 0%, #f7e2be 100%);
}

.theme-amber .value-eyebrow {
  color: #b67600;
}

.developer-section {
  position: relative;
  padding: 92px 8% 110px;
  background:
    radial-gradient(circle at top left, rgba(76, 132, 194, 0.24), transparent 20%),
    linear-gradient(180deg, #18314d 0%, #0f2033 100%);
}

.developer-shell {
  max-width: 1280px;
  margin: 0 auto;
}

.developer-header {
  max-width: 820px;
  margin: 0 auto 38px;
  text-align: center;
}

.developer-logo {
  display: block;
  width: 72px;
  height: 72px;
  margin: 0 auto 16px;
  border-radius: 18px;
  object-fit: cover;
  box-shadow: 0 18px 32px rgba(4, 15, 28, 0.42);
}

.developer-header h2 {
  margin: 0;
  color: white;
  font-size: clamp(2rem, 4vw, 3.6rem);
  line-height: 1;
}

.developer-subtitle {
  margin: 18px auto 0;
  color: #c9dbef;
  font-size: 1.06rem;
  line-height: 1.85;
}

.developer-copy {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px;
  margin-bottom: 34px;
}

.glass-card,
.team-card,
.closing-card {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 24px 44px rgba(2, 10, 22, 0.22);
  backdrop-filter: blur(14px);
}

.glass-card {
  padding: 24px;
  border-radius: 24px;
  color: #d6e6f6;
  line-height: 1.85;
}

.glass-card p {
  margin: 0;
}

.glass-card p + p {
  margin-top: 14px;
}

.team-section {
  margin-top: 24px;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
  margin-top: 24px;
}

.team-card {
  --tilt-x: 0deg;
  --tilt-y: 0deg;
  overflow: hidden;
  border-radius: 24px;
  transform: perspective(1200px) rotateX(var(--tilt-x)) rotateY(var(--tilt-y));
  transition: transform 0.22s ease, border-color 0.3s ease;
}

.team-card:hover {
  border-color: rgba(255, 255, 255, 0.24);
}

.team-image-wrap {
  overflow: hidden;
  aspect-ratio: 4 / 4.5;
}

.team-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.8s ease;
}

.team-card:hover .team-image {
  transform: scale(1.06);
}

.team-card-body {
  padding: 18px;
}

.team-card-body h4 {
  margin: 0;
  color: white;
  font-size: 1.05rem;
}

.team-role {
  margin: 6px 0 10px;
  color: #9bc9ff;
  font-size: 0.92rem;
}

.team-description {
  margin: 0;
  color: #d6e6f6;
  line-height: 1.7;
  font-size: 0.92rem;
}

.stack-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-top: 32px;
}

.stack-card {
  padding: 22px;
  border-radius: 22px;
  color: white;
  box-shadow: 0 20px 40px rgba(3, 14, 28, 0.25);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stack-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 28px 54px rgba(3, 14, 28, 0.34);
}

.stack-card h3 {
  margin: 0 0 10px;
}

.stack-card p {
  margin: 0;
  color: rgba(240, 247, 255, 0.86);
  line-height: 1.75;
}

.stack-blue {
  background: linear-gradient(135deg, rgba(36, 107, 227, 0.88), rgba(18, 56, 184, 0.88));
}

.stack-cyan {
  background: linear-gradient(135deg, rgba(10, 153, 153, 0.9), rgba(21, 95, 160, 0.88));
}

.stack-indigo {
  background: linear-gradient(135deg, rgba(78, 73, 210, 0.9), rgba(35, 52, 124, 0.9));
}

.closing-card {
  margin-top: 36px;
  padding: 30px;
  border-radius: 26px;
  text-align: center;
}

.closing-line {
  margin: 0;
  color: white;
  font-size: 1.4rem;
}

.closing-subline {
  margin: 12px 0 0;
  color: #d6e6f6;
  line-height: 1.8;
}

.reveal-on-scroll {
  opacity: 0;
  transition: opacity 0.9s ease, transform 0.9s ease;
}

.reveal-up {
  transform: translateY(56px);
}

.reveal-left {
  transform: translateX(-56px);
}

.reveal-right {
  transform: translateX(56px);
}

.reveal-scale {
  transform: translateY(34px) scale(0.96);
}

.reveal-on-scroll.show {
  opacity: 1;
  transform: translate(0, 0) scale(1);
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

@keyframes drift {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(0, -16px, 0);
  }
}

@media (max-width: 1180px) {
  .values-grid,
  .team-grid,
  .stack-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .about-hero,
  .story-grid,
  .developer-copy {
    grid-template-columns: 1fr;
  }

  .hero-panel {
    justify-self: start;
  }

  .story-media-order {
    order: initial;
  }
}

@media (max-width: 720px) {
  .about-hero,
  .story-band,
  .values-section,
  .developer-section {
    padding-left: 20px;
    padding-right: 20px;
  }

  .values-grid,
  .team-grid,
  .stack-grid,
  .detail-grid,
  .filter-grid {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    flex-direction: column;
  }

  .hero-link {
    width: 100%;
  }

  .story-image {
    height: 360px;
  }
}
</style>
