import { getAuthToken } from "./auth"

const API_BASE = "/api/production"
const USE_CV_DETECTION_MOCK = import.meta.env.VITE_USE_CV_DETECTION_MOCK === "true"

function authHeaders(extraHeaders = {}) {
  const token = getAuthToken()
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extraHeaders
  }
}

async function parseResponse(response, fallbackMessage) {
  const contentType = response.headers.get("content-type") || ""
  const isJson = contentType.includes("application/json")
  const payload = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    const message =
      (isJson && (payload.error || payload.message || payload.msg)) ||
      (typeof payload === "string" && payload) ||
      fallbackMessage

    throw new Error(message)
  }

  return payload
}

export default {
  async detectImage(file) {
    if (USE_CV_DETECTION_MOCK) {
      await new Promise((resolve) => setTimeout(resolve, 500))
      return {
        count: Math.floor(Math.random() * 5) + 1,
        confidence: 0.8
      }
    }

    const formData = new FormData()
    formData.append("image", file)

    const response = await fetch(`${API_BASE}/detect`, {
      method: "POST",
      body: formData
    })

    const data = await parseResponse(response, "Failed to detect kulhads from image")
    const detections = Array.isArray(data.detections) ? data.detections : []
    const averageConfidence = detections.length
      ? detections.reduce((sum, detection) => sum + Number(detection.confidence || 0), 0) / detections.length
      : 0

    return {
      count: Number(data.kulhad_count || 0),
      confidence: Number(averageConfidence.toFixed(4))
    }
  },

  async logProduction(logData) {
    const response = await fetch(`${API_BASE}/log`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(logData)
    })

    return parseResponse(response, "Failed to log production")
  },

  async getEntries(month, year) {
    const response = await fetch(`${API_BASE}/entries?month=${month}&year=${year}`, {
      headers: authHeaders()
    })

    return parseResponse(response, "Failed to load production entries")
  }
}
