const AUTH_STORAGE_KEY = "kullad-auth"

export function getAuthSession() {
  const rawSession = localStorage.getItem(AUTH_STORAGE_KEY)

  if (!rawSession) {
    return null
  }

  try {
    return JSON.parse(rawSession)
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
}

export function saveAuthSession(session) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function updateAuthSession(updates) {
  const currentSession = getAuthSession()

  if (!currentSession) {
    return null
  }

  const nextSession = {
    ...currentSession,
    ...updates
  }

  saveAuthSession(nextSession)
  return nextSession
}

export function clearAuthSession() {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}

export function getAuthToken() {
  return getAuthSession()?.token || ""
}

export function getUserRole() {
  return getAuthSession()?.role || ""
}
