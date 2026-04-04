export class TicketsApiError extends Error {
  constructor(message, options = {}) {
    super(message)
    this.name = 'TicketsApiError'
    this.status = options.status ?? null
    this.code = options.code ?? null
    this.method = options.method ?? null
    this.url = options.url ?? null
    this.data = options.data ?? null
    this.headers = options.headers ?? null
  }
}

export function normalizeAxiosError(error) {
  if (!error || !error.isAxiosError) {
    return new TicketsApiError(error?.message || 'Unknown error', {
      data: error,
    })
  }

  const response = error.response
  const request = error.config

  if (!response) {
    return new TicketsApiError('Network error or no response from API', {
      code: error.code,
      method: request?.method?.toUpperCase() ?? null,
      url: request?.url ?? null,
      data: null,
    })
  }

  const detail =
    typeof response.data?.detail === 'string'
      ? response.data.detail
      : response.data?.message || `HTTP ${response.status}`

  return new TicketsApiError(detail, {
    status: response.status,
    code: error.code,
    method: request?.method?.toUpperCase() ?? null,
    url: request?.url ?? null,
    data: response.data,
    headers: response.headers,
  })
}
