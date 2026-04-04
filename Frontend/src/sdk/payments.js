export class PaymentsClient {
  constructor(http, rootClient) {
    this._http = http
    this._root = rootClient
  }

  async create(payload) {
    return this._http.post('/payments/create', payload)
  }

  async get(paymentId, options = {}) {
    const id = String(paymentId || '').trim()
    if (!id) {
      throw new Error('paymentId is required')
    }

    const params = new URLSearchParams()

    if (options.pedido_id != null) {
      params.set('pedido_id', String(options.pedido_id))
    }

    if (options.referencia != null && String(options.referencia).trim()) {
      params.set('referencia', String(options.referencia).trim())
    }

    if (options.sync_order != null) {
      params.set('sync_order', String(Boolean(options.sync_order)))
    }

    const query = params.toString()
    const safeId = encodeURIComponent(id)
    const url = query ? `/payments/${safeId}?${query}` : `/payments/${safeId}`

    return this._http.get(url)
  }

  async status(paymentId, options = {}) {
    return this.get(paymentId, options)
  }

  async getByToken(paymentToken, options = {}) {
    const token = String(paymentToken || '').trim()
    if (!token) {
      throw new Error('paymentToken is required')
    }

    const params = new URLSearchParams()
    if (options.sync_order != null) {
      params.set('sync_order', String(Boolean(options.sync_order)))
    }

    const query = params.toString()
    const safeToken = encodeURIComponent(token)
    const url = query
      ? `/payments/session/${safeToken}?${query}`
      : `/payments/session/${safeToken}`

    return this._http.get(url)
  }

  async getSyncSummary(options = {}) {
    const params = new URLSearchParams()

    if (options.limit != null) {
      params.set('limit', String(options.limit))
    }
    if (options.sync_order != null) {
      params.set('sync_order', String(Boolean(options.sync_order)))
    }

    const query = params.toString()
    const url = query ? `/payments/sync/summary?${query}` : '/payments/sync/summary'
    return this._http.get(url)
  }
}
