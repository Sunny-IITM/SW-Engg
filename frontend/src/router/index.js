import { createRouter, createWebHistory } from "vue-router"

import Home from "../pages/Home.vue"
import Store from "../pages/Store.vue"
import Cart from "../pages/Cart.vue"
import Checkout from "../pages/Checkout.vue"
import About from "../pages/About.vue"
import Profile from "../pages/Profile.vue"
import Login from "../pages/Login.vue"
import Signup from "../pages/Signup.vue"
import Admin from "../pages/Admin.vue"
import Employee from "../pages/Employee.vue"
import Analytics from "../pages/Analytics.vue"
import AdminDashboard from "../pages/admin/Admindashboard.vue"
import AdminInventory from "../pages/admin/AdminInventory.vue"
import AdminRawInventory from "../pages/admin/AdminRawInventory.vue"
import AdminRawInventoryHistory from "../pages/admin/AdminRawInventoryHistory.vue"
import AdminCustomer from "../pages/admin/AdminCustomer.vue"
import AdminEmployee from "../pages/admin/AdminEmployee.vue"
import AdminOrder from "../pages/admin/AdminOrder.vue"
import AdminPayroll from "../pages/admin/AdminPayroll.vue"
import AdminProductHistory from "../pages/admin/AdminProductHistory.vue"
import EmployeeDashboard from "../pages/admin/EmployeeDashboard.vue"
import EmployeeEntries from "../pages/admin/EmployeeEntries.vue"
import EmployeePayroll from "../pages/admin/EmployeePayroll.vue"
import EmployeeProfile from "../pages/admin/EmployeeProfile.vue"
import AdminProductManagement from "../pages/admin/AdminProductManagement.vue"
import { getAuthSession } from "../services/auth"

const routes = [
  {
    path: "/",
    name: "home",
    component: Home
  },
  {
    path: "/store",
    name: "store",
    component: Store
  },
  {
    path: "/cart",
    name: "cart",
    component: Cart
  },
  {
    path: "/checkout",
    name: "checkout",
    component: Checkout,
    meta: { requiresAuth: true }
  },
  {
    path: "/about",
    name: "about",
    component: About
  },
  {
    path: "/account",
    name: "account",
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: "/login",
    name: "login",
    component: Login
  },
  {
    path: "/signup",
    name: "signup",
    component: Signup
  },
  {
    path: "/signin",
    redirect: { name: "login" }
  },
  {
    path: "/shop",
    redirect: { name: "store" }
  },
  {
    path: "/admin",
    component: Admin,
    meta: { requiresAuth: true, role: "admin" },
    children: [
      {
        path: "",
        name: "admin-dashboard",
        component: AdminDashboard
      },
      {
        path: "analytics",
        name: "admin-analytics",
        component: Analytics
      },
      {
        path: "inventory",
        name: "admin-inventory",
        component: AdminInventory
      },
      {
        path: "inventory/history",
        redirect: { name: "admin-inventory" }
      },
      {
        path: "raw-inventory",
        name: "admin-raw-inventory",
        component: AdminRawInventory
      },
      {
        path: "raw-inventory/history",
        name: "admin-raw-inventory-history",
        component: AdminRawInventoryHistory
      },
      {
        path: "orders",
        name: "admin-orders",
        component: AdminOrder
      },
      {
        path: "employees",
        name: "admin-employees",
        component: AdminEmployee
      },
      {
        path: "payroll",
        name: "admin-payroll",
        component: AdminPayroll
      },
      {
        path: "customers",
        name: "admin-customers",
        component: AdminCustomer
      },
      {
        path: "products",
        name: "admin-products",
        component: AdminProductManagement
      },
      {
        path: "products/history",
        name: "admin-product-history",
        component: AdminProductHistory
      }
    ]
  },
  {
    path: "/employee",
    component: Employee,
    meta: { requiresAuth: true, role: "employee" },
    children: [
      {
        path: "",
        name: "employee-dashboard",
        component: EmployeeDashboard
      },
      {
        path: "entries",
        name: "employee-entries",
        component: EmployeeEntries
      },
      {
        path: "payroll",
        name: "employee-payroll",
        component: EmployeePayroll
      },
      {
        path: "profile",
        name: "employee-profile",
        component: EmployeeProfile
      }
    ]
  },
  {
    path: "/production",
    redirect: { name: "employee-dashboard" }
  },
  {
    path: "/analytics",
    redirect: { name: "admin-analytics" }
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/"
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const session = getAuthSession()
  const requiredRole = to.matched.find((record) => record.meta?.role)?.meta?.role
  const requiresAuth = to.matched.some((record) => record.meta?.requiresAuth)

  if (requiresAuth && !session?.token) {
    return { name: "login" }
  }

  if (requiredRole && session?.role !== requiredRole) {
    if (session?.role === "admin") {
      return { name: "admin-dashboard" }
    }

    if (session?.role === "employee") {
      return { name: "employee-dashboard" }
    }

    return { name: "login" }
  }

  if ((to.name === "login" || to.name === "signup") && session?.token) {
    if (session.role === "admin") {
      return { name: "admin-dashboard" }
    }

    if (session.role === "employee") {
      return { name: "employee-dashboard" }
    }

    return { name: "store" }
  }

  return true
})

export default router
