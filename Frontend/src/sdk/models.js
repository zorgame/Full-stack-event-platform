export class BaseEntity {
  constructor(client, data) {
    Object.defineProperty(this, '_client', {
      value: client,
      enumerable: false,
      writable: false,
    })
    Object.assign(this, data)
  }
}

export class Usuario extends BaseEntity {}

export class Producto extends BaseEntity {
  async reload() {
    const fresh = await this._client.productos.get(this.id)
    Object.assign(this, fresh)
    return this
  }

  async update(payload) {
    const updated = await this._client.productos.update(this.id, payload)
    Object.assign(this, updated)
    return this
  }

  async delete() {
    return this._client.productos.delete(this.id)
  }

  async createCategoria(payload) {
    return this._client.productos.createCategoria(this.id, payload)
  }
}

export class Categoria extends BaseEntity {}

export class Pedido extends BaseEntity {
  async reload() {
    const fresh = await this._client.pedidos.get(this.id)
    Object.assign(this, fresh)
    return this
  }

  async updateEstado(estado) {
    const updated = await this._client.pedidos.updateEstado(this.id, { estado })
    Object.assign(this, updated)
    return this
  }

  async delete() {
    return this._client.pedidos.delete(this.id)
  }
}

export class UsuarioTicket extends BaseEntity {}
