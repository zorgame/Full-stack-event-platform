import { Categoria, Producto } from './models'

export class ProductosClient {
  constructor(http, rootClient) {
    this._http = http
    this._root = rootClient
  }

  async list(options = {}) {
    const params = new URLSearchParams()
    if (options.skip != null) params.set('skip', String(options.skip))
    if (options.limit != null) params.set('limit', String(options.limit))
    if (options.only_active != null) params.set('only_active', String(Boolean(options.only_active)))

    const query = params.toString()
    const url = query ? `/productos/?${query}` : '/productos/'
    const items = await this._http.get(url)
    return items.map((p) => new Producto(this._root, p))
  }

  async get(id) {
    const data = await this._http.get(`/productos/${id}`)
    return new Producto(this._root, data)
  }

  async create(payload) {
    const data = await this._http.post('/productos/', payload)
    return new Producto(this._root, data)
  }

  async update(id, payload) {
    const data = await this._http.put(`/productos/${id}` , payload)
    return new Producto(this._root, data)
  }

  async delete(id) {
    return this._http.delete(`/productos/${id}`)
  }

  async createCategoria(productoId, payload) {
    const data = await this._http.post(`/productos/${productoId}/categorias`, payload)
    return new Categoria(this._root, data)
  }

  async uploadImagen(file) {
    const formData = new FormData()
    formData.append('file', file)
    return this._http.post('/productos/upload-imagen', formData)
  }
}
