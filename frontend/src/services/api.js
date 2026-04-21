const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "/api"

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || ""
  const isJson = contentType.includes("application/json")
  const payload = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    const message =
      (isJson && (payload.message || payload.error || payload.msg)) ||
      response.statusText ||
      "Request failed"

    throw new Error(message)
  }

  return payload
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  })

  return parseResponse(response)
}

export function registerUser(payload) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  })
}

export function loginUser(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  })
}

export function getProducts() {
  return request("/products/")
}

export function getMyProfile(token) {
  return request("/profile/me", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function updateMyProfile(payload, token) {
  return request("/profile/me", {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function getInventoryProducts(token) {
  return request("/inventory/", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function getInventoryHistory(token) {
  return request("/inventory/history", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function getRawInventory(token) {
  return request("/inventory/raw", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function getRawInventoryHistory(token) {
  return request("/inventory/raw/history", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function createRawMaterial(payload, token) {
  return request("/inventory/raw", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function updateRawMaterial(itemId, payload, token) {
  return request(`/inventory/raw/${itemId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function adjustRawMaterial(itemId, payload, token) {
  return request(`/inventory/raw/${itemId}/adjust`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function deleteRawMaterial(itemId, token) {
  return request(`/inventory/raw/${itemId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function getAdminDashboard(token) {
  return request("/analytics/dashboard", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function getAnalyticsSummary(token) {
  return request("/analytics/summary", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function getAdminUsers(role, token) {
  const query = role ? `?role=${encodeURIComponent(role)}` : ""
  return request(`/admin/users${query}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function createAdminUser(payload, token) {
  return request("/admin/users", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function updateAdminUser(userId, payload, token) {
  return request(`/admin/users/${userId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function deleteAdminUser(userId, token) {
  return request(`/admin/users/${userId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function getAdminOrders(token) {
  return request("/orders/admin", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function getPayrollRecords(month, year, token, asOfDate = "") {
  const query = new URLSearchParams({
    month: String(month),
    year: String(year)
  })

  if (asOfDate) {
    query.set("as_of_date", asOfDate)
  }

  return request(`/payroll/?${query.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function getMyPayrollRecord(month, year, token, asOfDate = "") {
  const query = new URLSearchParams({
    month: String(month),
    year: String(year)
  })

  if (asOfDate) {
    query.set("as_of_date", asOfDate)
  }

  return request(`/payroll/me?${query.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function updatePayrollRecord(employeeId, payload, token) {
  return request(`/payroll/${employeeId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function updateBulkPayrollStatus(payload, token) {
  return request("/payroll/bulk-status", {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function updateAdminOrderStatus(orderId, payload, token) {
  return request(`/orders/${orderId}/status`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function updateBulkAdminPaymentStatus(payload, token) {
  return request("/orders/bulk-payment-status", {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function getCheckoutProfile(token) {
  return request("/orders/checkout-profile", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function saveCheckoutProfile(payload, token) {
  return request("/orders/checkout-profile", {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function createOrder(payload, token) {
  return request("/orders/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function getMyOrderHistory(token) {
  return request("/orders/my-history", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function adjustInventory(payload, token) {
  return request("/inventory/adjust", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function createProduct(payload, token) {
  return request("/products/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function getProductHistory(token) {
  return request("/products/history", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export function updateProduct(productId, payload, token) {
  return request(`/products/${productId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  })
}

export function deleteProduct(productId, token) {
  return request(`/products/${productId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

export async function uploadProductImage(file, token) {
  const formData = new FormData()
  formData.append("image", file)

  const response = await fetch(`${API_BASE_URL}/products/upload-image`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: formData
  })

  return parseResponse(response)
}

export function buildProductImageUrl(imageName) {
  if (!imageName) {
    return ""
  }

  const productImagePrefix = `${API_BASE_URL}/products/images/`

  if (imageName.startsWith(productImagePrefix)) {
    const encodedName = imageName.slice(productImagePrefix.length)

    try {
      const decodedName = decodeURIComponent(encodedName)

      if (
        decodedName.startsWith("/") ||
        decodedName.startsWith(API_BASE_URL) ||
        /^https?:\/\//i.test(decodedName) ||
        decodedName.startsWith("data:image/")
      ) {
        return buildProductImageUrl(decodedName)
      }
    } catch {
      // Keep the original value when decoding fails.
    }
  }

  if (
    /^https?:\/\//i.test(imageName) ||
    imageName.startsWith("data:image/") ||
    imageName.startsWith("/") ||
    imageName.startsWith(API_BASE_URL)
  ) {
    return imageName
  }

  return `${API_BASE_URL}/products/images/${encodeURIComponent(imageName)}`
}

export { API_BASE_URL }
