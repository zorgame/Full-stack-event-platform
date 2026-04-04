const cacheStore = new Map()
const inflightStore = new Map()

function now() {
  return Date.now()
}

export function getCached(key) {
  const entry = cacheStore.get(key)
  if (!entry) return null
  if (entry.expiresAt <= now()) {
    cacheStore.delete(key)
    return null
  }
  return entry.value
}

export function setCached(key, value, ttlMs) {
  cacheStore.set(key, {
    value,
    expiresAt: now() + ttlMs,
  })
  return value
}

export async function getOrSetCached({ key, ttlMs, fetcher }) {
  const cached = getCached(key)
  if (cached !== null) return cached

  if (inflightStore.has(key)) {
    return inflightStore.get(key)
  }

  const promise = Promise.resolve()
    .then(fetcher)
    .then((value) => setCached(key, value, ttlMs))
    .finally(() => {
      inflightStore.delete(key)
    })

  inflightStore.set(key, promise)
  return promise
}

export function clearCacheByPrefix(prefix) {
  for (const key of cacheStore.keys()) {
    if (key.startsWith(prefix)) {
      cacheStore.delete(key)
    }
  }
}

export function clearCacheKey(key) {
  cacheStore.delete(key)
  inflightStore.delete(key)
}

export function clearAllCache() {
  cacheStore.clear()
  inflightStore.clear()
}
