import { Pedido } from './models'

export class PedidosClient {
  constructor(http, rootClient) {
    this._http = http
    this._root = rootClient
  }

  async add(payload) {
    return this.create(payload)
  }

  async create(payload) {
    const data = await this._http.post('/pedidos/', payload)
    return new Pedido(this._root, data)
  }

  async mine() {
    const items = await this._http.get('/pedidos/mis')
    return items.map((p) => new Pedido(this._root, p))
  }

  async list(options = {}) {
    const params = new URLSearchParams()
    if (options.skip != null) params.set('skip', String(options.skip))
    if (options.limit != null) params.set('limit', String(options.limit))
    if (options.estado != null && String(options.estado).trim()) {
      params.set('estado', String(options.estado).trim().toLowerCase())
    }
    const query = params.toString()
    const url = query ? `/pedidos/?${query}` : '/pedidos/'
    const items = await this._http.get(url)
    return items.map((p) => new Pedido(this._root, p))
  }

  async get(id) {
    const data = await this._http.get(`/pedidos/${id}`)
    return new Pedido(this._root, data)
  }

  async updateEstado(id, payload) {
    const data = await this._http.patch(`/pedidos/${id}/estado`, payload)
    return new Pedido(this._root, data)
  }

  async metrics(options = {}) {
    const params = new URLSearchParams()

    if (options.rango != null) params.set('rango', String(options.rango))
    if (options.fecha_desde != null) params.set('fecha_desde', String(options.fecha_desde))
    if (options.fecha_hasta != null) params.set('fecha_hasta', String(options.fecha_hasta))
    if (options.group_by != null) params.set('group_by', String(options.group_by))

    if (options.estado != null) {
      const estado = Array.isArray(options.estado)
        ? options.estado.join(',')
        : String(options.estado)
      if (estado.trim()) params.set('estado', estado)
    }

    if (options.pais != null) {
      const pais = Array.isArray(options.pais) ? options.pais.join(',') : String(options.pais)
      if (pais.trim()) params.set('pais', pais)
    }

    if (options.producto_ids != null) {
      const productoIds = Array.isArray(options.producto_ids)
        ? options.producto_ids.join(',')
        : String(options.producto_ids)
      if (productoIds.trim()) params.set('producto_ids', productoIds)
    }

    if (options.categoria_ids != null) {
      const categoriaIds = Array.isArray(options.categoria_ids)
        ? options.categoria_ids.join(',')
        : String(options.categoria_ids)
      if (categoriaIds.trim()) params.set('categoria_ids', categoriaIds)
    }

    if (options.min_total != null && String(options.min_total).trim() !== '') {
      params.set('min_total', String(options.min_total))
    }
    if (options.max_total != null && String(options.max_total).trim() !== '') {
      params.set('max_total', String(options.max_total))
    }
    if (options.top_n != null) params.set('top_n', String(options.top_n))
    if (options.ventas_solo_aprobadas != null) {
      params.set('ventas_solo_aprobadas', String(Boolean(options.ventas_solo_aprobadas)))
    }

    const query = params.toString()
    const url = query ? `/pedidos/metricas?${query}` : '/pedidos/metricas'
    return this._http.get(url)
  }

  async delete(id) {
    return this._http.delete(`/pedidos/${id}`)
  }
}
