import { HttpClient } from './http'
import { AuthClient } from './auth'
import { ProductosClient } from './productos'
import { CategoriasClient } from './categorias'
import { PedidosClient } from './pedidos'
import { PaymentsClient } from './payments'
import { UsuariosClient } from './usuarios'

export class TicketsClient {
  constructor(options = {}) {
    this.http = new HttpClient({
      baseURL: options.baseURL ?? null,
      token: options.token ?? null,
      headers: options.headers ?? {},
      timeout: options.timeout ?? 15000,
    })

    this.auth = new AuthClient(this.http, this)
    this.productos = new ProductosClient(this.http, this)
    this.categorias = new CategoriasClient(this.http, this)
    this.pedidos = new PedidosClient(this.http, this)
    this.payments = new PaymentsClient(this.http, this)
    this.usuarios = new UsuariosClient(this.http, this)

    this.create = {
      pedido: (payload) => this.pedidos.create(payload),
      producto: (payload) => this.productos.create(payload),
      categoria: (payload) => this.categorias.create(payload),
      user: (payload) => this.usuarios.create(payload),
      ticket: (usuarioId, payload) => this.usuarios.assignTicket(usuarioId, payload),
    }

    this.getProducto = (id) => this.productos.get(id)
    this.getProductos = () => this.productos.list()
  }

  setToken(token) {
    this.http.setToken(token)
  }

  clearToken() {
    this.http.clearToken()
  }
}

export function createTicketsClient(options) {
  return new TicketsClient(options)
}
