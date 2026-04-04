import { createTicketsClient } from '../sdk'
import { API_CONFIG, STORAGE_KEYS } from '../config/constants'

let client

function getPersistedToken() {
  return localStorage.getItem(STORAGE_KEYS.token)
}

export function getSdkClient() {
  if (!client) {
    client = createTicketsClient({
      baseURL: API_CONFIG.baseURL,
      token: getPersistedToken(),
      timeout: API_CONFIG.timeoutMs,
    })
  }
  return client
}

export function setSdkToken(token) {
  const sdk = getSdkClient()
  sdk.setToken(token)
  if (token) {
    localStorage.setItem(STORAGE_KEYS.token, token)
  } else {
    localStorage.removeItem(STORAGE_KEYS.token)
  }
}

export function clearSdkToken() {
  const sdk = getSdkClient()
  sdk.clearToken()
  localStorage.removeItem(STORAGE_KEYS.token)
}
