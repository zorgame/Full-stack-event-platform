import { Usuario, UsuarioTicket } from './models'

export class UsuariosClient {
  constructor(http, rootClient) {
    this._http = http
    this._root = rootClient
  }

  async create(payload) {
    const data = await this._http.post('/usuarios/', payload)
    return new Usuario(this._root, data)
  }

  async list(options = {}) {
    const params = new URLSearchParams()
    if (options.skip != null) params.set('skip', String(options.skip))
    if (options.limit != null) params.set('limit', String(options.limit))

    const query = params.toString()
    const url = query ? `/usuarios/?${query}` : '/usuarios/'
    const items = await this._http.get(url)
    return items.map((u) => new Usuario(this._root, u))
  }

  async update(id, payload) {
    const data = await this._http.put(`/usuarios/${id}`, payload)
    return new Usuario(this._root, data)
  }

  async delete(id) {
    return this._http.delete(`/usuarios/${id}`)
  }

  async listTickets(usuarioId) {
    const items = await this._http.get(`/usuarios/${usuarioId}/tickets`)
    return items.map((t) => new UsuarioTicket(this._root, t))
  }

  async assignTicket(usuarioId, payload) {
    const data = await this._http.post(`/usuarios/${usuarioId}/tickets`, payload)
    return new UsuarioTicket(this._root, data)
  }

  async updateTicket(usuarioId, usuarioTicketId, payload) {
    const data = await this._http.put(`/usuarios/${usuarioId}/tickets/${usuarioTicketId}`, payload)
    return new UsuarioTicket(this._root, data)
  }

  async deleteTicket(usuarioId, usuarioTicketId) {
    return this._http.delete(`/usuarios/${usuarioId}/tickets/${usuarioTicketId}`)
  }

  async transferMyTicket(payload) {
    return this._http.post('/usuarios/me/tickets/transferencia', payload)
  }
}
