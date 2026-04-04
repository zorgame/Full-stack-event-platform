import { Categoria } from './models'

export class CategoriasClient {
  constructor(http, rootClient) {
    this._http = http
    this._root = rootClient
  }

  async list(options = {}) {
    const params = new URLSearchParams()
    if (options.productoId != null) params.set('producto_id', String(options.productoId))
    if (options.onlyActive != null) params.set('only_active', String(options.onlyActive))

    const query = params.toString()
    const url = query ? `/categorias/?${query}` : '/categorias/'
    const items = await this._http.get(url)
    return items.map((c) => new Categoria(this._root, c))
  }

  async get(id) {
    const data = await this._http.get(`/categorias/${id}`)
    return new Categoria(this._root, data)
  }

  async create(payload) {
    const data = await this._http.post('/categorias/', payload)
    return new Categoria(this._root, data)
  }

  async update(id, payload) {
    const data = await this._http.put(`/categorias/${id}`, payload)
    return new Categoria(this._root, data)
  }

  async delete(id) {
    return this._http.delete(`/categorias/${id}`)
  }
}
