const modulePromiseCache = new Map()

function normalizeModuleUrl(url) {
  const normalized = String(url || '').trim()
  if (!normalized) {
    throw new Error('La URL del modulo externo es requerida')
  }
  return normalized
}

export async function loadExternalModule(url) {
  const normalizedUrl = normalizeModuleUrl(url)

  const cachedPromise = modulePromiseCache.get(normalizedUrl)
  if (cachedPromise) {
    return cachedPromise
  }

  const loadPromise = import(/* @vite-ignore */ normalizedUrl)
    .then((mod) => mod)
    .catch((error) => {
      modulePromiseCache.delete(normalizedUrl)
      throw error
    })

  modulePromiseCache.set(normalizedUrl, loadPromise)
  return loadPromise
}

export function preloadExternalModule(url) {
  const normalizedUrl = String(url || '').trim()
  if (!normalizedUrl) return
  void loadExternalModule(normalizedUrl)
}
