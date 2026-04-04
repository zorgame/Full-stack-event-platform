import { defineStore } from 'pinia'

const CLAVE_STORAGE_CARRITO = 'tickets_carrito_v1'

function normalizarMaximoPermitido(valor) {
  if (valor === undefined || valor === null || valor === '') return null
  const numero = Number(valor)
  if (Number.isNaN(numero) || numero <= 0) return null
  return Math.floor(numero)
}

function normalizarItems(items) {
  if (!Array.isArray(items)) return []

  return items
    .map((item) => ({
      idCategoria: Number(item?.idCategoria),
      idProducto: Number(item?.idProducto || 0),
      nombreEvento: String(item?.nombreEvento || ''),
      nombreCategoria: String(item?.nombreCategoria || ''),
      fechaEvento: String(item?.fechaEvento || ''),
      maximoPermitido: normalizarMaximoPermitido(item?.maximoPermitido),
      precioUnitario: Number(item?.precioUnitario || 0),
      cantidad: Number(item?.cantidad || 0),
    }))
    .filter((item) => Number.isFinite(item.idCategoria) && item.idCategoria > 0)
    .filter((item) => item.cantidad > 0)
}

function normalizarCantidad(cantidad) {
  const valor = Number(cantidad)
  if (Number.isNaN(valor) || valor < 0) return 0
  return Math.floor(valor)
}

function aplicarLimiteCantidad(item, cantidad) {
  const cantidadNormalizada = normalizarCantidad(cantidad)
  const maximo = normalizarMaximoPermitido(item?.maximoPermitido)
  if (!maximo) return cantidadNormalizada
  return Math.min(cantidadNormalizada, maximo)
}

export const useCarritoStore = defineStore('carrito', {
  state: () => ({
    items: [],
    estaInicializado: false,
  }),

  getters: {
    cantidadTotal: (state) => state.items.reduce((acumulado, item) => acumulado + item.cantidad, 0),
    subtotal: (state) =>
      state.items.reduce((acumulado, item) => acumulado + item.cantidad * item.precioUnitario, 0),
  },

  actions: {
    inicializar() {
      if (this.estaInicializado) return

      this.estaInicializado = true
      if (typeof window === 'undefined') return

      try {
        const valor = window.localStorage.getItem(CLAVE_STORAGE_CARRITO)
        if (!valor) return
        this.items = normalizarItems(JSON.parse(valor))
      } catch {
        this.items = []
      }
    },

    guardar() {
      if (typeof window === 'undefined') return
      window.localStorage.setItem(CLAVE_STORAGE_CARRITO, JSON.stringify(this.items))
    },

    agregarItem(itemNuevo) {
      const [itemNormalizado] = normalizarItems([itemNuevo])
      if (!itemNormalizado) return

      const indiceExistente = this.items.findIndex((item) => item.idCategoria === itemNormalizado.idCategoria)

      if (indiceExistente >= 0) {
        const itemActual = this.items[indiceExistente]
        const maximoPermitido = normalizarMaximoPermitido(
          itemActual.maximoPermitido ?? itemNormalizado.maximoPermitido
        )
        const cantidadSiguiente = aplicarLimiteCantidad(
          { maximoPermitido },
          itemActual.cantidad + itemNormalizado.cantidad
        )

        this.items[indiceExistente] = {
          ...itemActual,
          idProducto: itemActual.idProducto || itemNormalizado.idProducto,
          nombreEvento: itemActual.nombreEvento || itemNormalizado.nombreEvento,
          nombreCategoria: itemActual.nombreCategoria || itemNormalizado.nombreCategoria,
          fechaEvento: itemActual.fechaEvento || itemNormalizado.fechaEvento,
          maximoPermitido,
          cantidad: cantidadSiguiente,
        }
      } else {
        itemNormalizado.cantidad = aplicarLimiteCantidad(itemNormalizado, itemNormalizado.cantidad)
        this.items.push(itemNormalizado)
      }

      this.guardar()
    },

    actualizarCantidad(idCategoria, cantidadNueva) {
      const id = Number(idCategoria)
      const indice = this.items.findIndex((item) => item.idCategoria === id)
      if (indice < 0) return

      const cantidad = aplicarLimiteCantidad(this.items[indice], cantidadNueva)

      if (cantidad <= 0) {
        this.items = this.items.filter((item) => item.idCategoria !== id)
      } else {
        this.items[indice] = {
          ...this.items[indice],
          cantidad,
        }
      }

      this.guardar()
    },

    actualizarMetadatosItem(idCategoria, metadatos = {}) {
      const id = Number(idCategoria)
      const indice = this.items.findIndex((item) => item.idCategoria === id)
      if (indice < 0) return

      const maximoPermitido = normalizarMaximoPermitido(
        metadatos.maximoPermitido ?? this.items[indice].maximoPermitido
      )

      const siguiente = {
        ...this.items[indice],
        idProducto: Number(metadatos.idProducto ?? this.items[indice].idProducto ?? 0),
        nombreEvento: String(metadatos.nombreEvento ?? this.items[indice].nombreEvento ?? ''),
        nombreCategoria: String(metadatos.nombreCategoria ?? this.items[indice].nombreCategoria ?? ''),
        fechaEvento: String(metadatos.fechaEvento ?? this.items[indice].fechaEvento ?? ''),
        maximoPermitido,
      }
      siguiente.cantidad = aplicarLimiteCantidad(siguiente, siguiente.cantidad)

      this.items[indice] = siguiente
      this.guardar()
    },

    incrementarCantidad(idCategoria) {
      const id = Number(idCategoria)
      const item = this.items.find((valor) => valor.idCategoria === id)
      if (!item) return
      this.actualizarCantidad(id, item.cantidad + 1)
    },

    decrementarCantidad(idCategoria) {
      const id = Number(idCategoria)
      const item = this.items.find((valor) => valor.idCategoria === id)
      if (!item) return
      this.actualizarCantidad(id, item.cantidad - 1)
    },

    removerItem(idCategoria) {
      const id = Number(idCategoria)
      this.items = this.items.filter((item) => item.idCategoria !== id)
      this.guardar()
    },

    vaciar() {
      this.items = []
      this.guardar()
    },
  },
})
