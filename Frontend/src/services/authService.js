import { CACHE_CONFIG, STORAGE_KEYS } from '../config/constants'
import { clearCacheKey, getOrSetCached } from '../utils/requestCache'
import { clearSdkToken, getSdkClient, setSdkToken } from './sdkClient'

const ME_CACHE_KEY = 'auth:me'

export async function loginWithCredentials(email, password) {
  const sdk = getSdkClient()
  clearCacheKey(ME_CACHE_KEY)
  const token = await sdk.auth.login(email, password)
  setSdkToken(token.access_token)
  return token
}

export async function fetchCurrentUser() {
  return getOrSetCached({
    key: ME_CACHE_KEY,
    ttlMs: CACHE_CONFIG.meTtlMs,
    fetcher: async () => {
      const sdk = getSdkClient()
      return sdk.auth.me()
    },
  })
}

export function persistUser(user) {
  localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user))
}

export function getPersistedUser() {
  const raw = localStorage.getItem(STORAGE_KEYS.user)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function clearSession() {
  clearCacheKey(ME_CACHE_KEY)
  clearSdkToken()
  localStorage.removeItem(STORAGE_KEYS.user)
}
