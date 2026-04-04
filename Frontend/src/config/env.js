const ENV = import.meta.env || {}

export function getEnvString(name, fallback = '') {
  const raw = ENV[name]
  if (raw === undefined || raw === null) {
    return fallback
  }

  const normalized = String(raw).trim()
  return normalized || fallback
}

export function getEnvInt(name, fallback, { min = Number.NEGATIVE_INFINITY, max = Number.POSITIVE_INFINITY } = {}) {
  const raw = Number(getEnvString(name, ''))
  if (!Number.isFinite(raw)) {
    return fallback
  }

  const normalized = Math.trunc(raw)
  if (normalized < min) return min
  if (normalized > max) return max
  return normalized
}

export function getEnvCsv(name, fallback = []) {
  const raw = getEnvString(name, '')
  if (!raw) {
    return [...fallback]
  }

  const values = raw
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean)

  return values.length ? values : [...fallback]
}
