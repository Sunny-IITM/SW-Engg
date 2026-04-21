<template>
  <div>
    <Navbar v-if="showNavbar" />
    <router-view />
  </div>
</template>

<script setup>
import { computed } from "vue"
import { useRoute } from "vue-router"
import Navbar from "./components/Navbar.vue"
import { getAuthSession } from "./services/auth"

const route = useRoute()
const session = getAuthSession()

const showNavbar = computed(() => {
  return (route.path !== "/" || Boolean(session?.token)) &&
    route.path !== "/login" &&
    route.path !== "/signup" &&
    route.path !== "/signin" &&
    !route.path.startsWith("/admin") &&
    !route.path.startsWith("/employee")
})
</script>
