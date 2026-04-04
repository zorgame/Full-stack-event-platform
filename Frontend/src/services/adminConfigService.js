import { getSdkClient } from './sdkClient'
import { API_CONFIG } from '../config/constants'

function deepClone(value) {
  return JSON.parse(JSON.stringify(value))
}

function buildTempKey(prefix) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`
}

function normalizeDateForInput(dateValue) {
  if (!dateValue) return ''
  const date = new Date(dateValue)
  if (Number.isNaN(date.getTime())) return ''
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

export function normalizeTicket(producto) {
  return {
    localKey: buildTempKey('ticket'),
    id: producto.id ?? null,
    nombre: producto.nombre ?? '',
    ubicacion: producto.ubicacion ?? '',
    estadio: producto.estadio ?? '',
    ubicacion_estadio: producto.ubicacion_estadio ?? '',
    fecha: normalizeDateForInput(producto.fecha),
    descripcion: producto.descripcion ?? '',
    imagen: producto.imagen ?? '',
    is_active: producto.is_active !== false,
    categorias: (producto.categorias ?? []).map((cat) => ({
      localKey: buildTempKey('cat'),
      id: cat.id ?? null,
      producto_id: cat.producto_id ?? producto.id ?? null,
      nombre: cat.nombre ?? '',
      descripcion: cat.descripcion ?? '',
      precio: Number(cat.precio ?? 0),
      moneda: cat.moneda ?? 'USD',
      unidades_disponibles: Number(cat.unidades_disponibles ?? 0),
      limite_por_usuario: cat.limite_por_usuario ?? null,
      activo: cat.activo !== false,
      is_active: cat.is_active !== false,
    })),
  }
}

export function normalizeUser(user) {
  return {
    localKey: buildTempKey('user'),
    id: user.id ?? null,
    email: user.email ?? '',
    telefono: user.telefono ?? '',
    nombre: user.nombre ?? '',
    apellido: user.apellido ?? '',
    pais: user.pais ?? '',
    password: '',
    is_active: user.is_active !== false,
    is_admin: user.is_admin === true,
    assignmentsLoaded: false,
    assignmentsLoading: false,
    assignments: [],
  }
}

function toIntOr(value, fallback) {
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed >= 0 ? parsed : fallback
}

function toPageLimit(value, fallback = 10) {
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback
}

export async function fetchTicketsConfigPage(options = {}) {
  const sdk = getSdkClient()
  const skip = toIntOr(options.skip, 0)
  const limit = toPageLimit(options.limit, 10)
  const only_active = options.only_active === true

  const productos = await sdk.productos.list({ skip, limit, only_active })
  return productos.map(normalizeTicket)
}

export async function fetchUsersConfigPage(options = {}) {
  const sdk = getSdkClient()
  const skip = toIntOr(options.skip, 0)
  const limit = toPageLimit(options.limit, 10)

  const usuarios = await sdk.usuarios.list({ skip, limit })
  return usuarios.map(normalizeUser)
}

export async function fetchCategoryOptionsCatalog(options = {}) {
  const sdk = getSdkClient()
  const skip = toIntOr(options.skip, 0)
  const limit = toPageLimit(options.limit, 500)
  const productos = await sdk.productos.list({
    skip,
    limit,
    only_active: false,
  })

  const optionsCatalog = []
  for (const ticket of productos) {
    for (const category of ticket.categorias ?? []) {
      if (!category?.id) continue
      optionsCatalog.push({
        value: Number(category.id),
        label: `${ticket.nombre || 'Ticket'} - ${category.nombre || 'Categoría'}`,
      })
    }
  }

  return optionsCatalog
}

export async function fetchAdminConfigSeed() {
  const sdk = getSdkClient()

  const [productos, usuarios] = await Promise.all([
    sdk.productos.list({ skip: 0, limit: 500, only_active: false }),
    sdk.usuarios.list({ skip: 0, limit: 500 }),
  ])

  const ticketDraft = productos.map(normalizeTicket)
  const userDraft = usuarios.map(normalizeUser)

  return {
    ticketsOriginal: deepClone(ticketDraft),
    ticketsDraft: deepClone(ticketDraft),
    usersOriginal: deepClone(userDraft),
    usersDraft: deepClone(userDraft),
  }
}

export async function fetchUserAssignments(usuarioId) {
  const sdk = getSdkClient()
  const tickets = await sdk.usuarios.listTickets(usuarioId)
  return tickets.map((item) => ({
    localKey: buildTempKey('assign'),
    id: item.id,
    categoria_id: item.categoria_id,
    cantidad: Number(item.cantidad ?? 1),
    nota: item.nota ?? '',
  }))
}

export async function uploadTicketImageAsset(file) {
  const sdk = getSdkClient()
  return sdk.productos.uploadImagen(file)
}

function toNullableString(value) {
  if (value === undefined || value === null || value === '') return null
  return String(value)
}

function toApiImagePath(value) {
  const raw = toNullableString(value)
  if (!raw) return null

  const baseURL = String(API_CONFIG.baseURL || '').replace(/\/+$/, '')
  if (baseURL && raw.startsWith(`${baseURL}/`)) {
    return `/${raw.slice(baseURL.length).replace(/^\/+/, '')}`
  }

  return raw
}

function toNullableInt(value) {
  if (value === undefined || value === null || value === '') return null
  return Number(value)
}

function mapTicketPayload(ticket) {
  return {
    nombre: ticket.nombre,
    ubicacion: ticket.ubicacion,
    estadio: toNullableString(ticket.estadio),
    ubicacion_estadio: toNullableString(ticket.ubicacion_estadio),
    fecha: ticket.fecha ? new Date(ticket.fecha).toISOString() : null,
    descripcion: toNullableString(ticket.descripcion),
    imagen: toApiImagePath(ticket.imagen),
    is_active: Boolean(ticket.is_active),
  }
}

function mapCategoryPayload(category) {
  return {
    nombre: category.nombre,
    descripcion: toNullableString(category.descripcion),
    precio: Number(category.precio),
    moneda: (category.moneda || 'USD').toUpperCase(),
    unidades_disponibles: Number(category.unidades_disponibles),
    limite_por_usuario: toNullableInt(category.limite_por_usuario),
    activo: Boolean(category.activo),
    is_active: Boolean(category.is_active),
  }
}

function mapUserCreatePayload(user) {
  return {
    email: String(user.email || '').trim(),
    telefono: toNullableString(user.telefono),
    nombre: toNullableString(user.nombre),
    apellido: toNullableString(user.apellido),
    pais: toNullableString(user.pais),
    password: String(user.password || '').trim(),
    is_admin: Boolean(user.is_admin),
  }
}

function mapUserUpdatePayload(user) {
  const payload = {
    telefono: toNullableString(user.telefono),
    nombre: toNullableString(user.nombre),
    apellido: toNullableString(user.apellido),
    pais: toNullableString(user.pais),
    is_active: Boolean(user.is_active),
    is_admin: Boolean(user.is_admin),
  }

  const password = String(user.password || '').trim()
  if (password) {
    payload.password = password
  }

  return payload
}

function validateUserPasswordIfPresent(user) {
  const password = String(user?.password || '').trim()
  if (!password) return
  if (password.length < 20) {
    const identity = String(user?.email || user?.id || 'usuario').trim()
    throw new Error(`La contraseña para ${identity} debe tener al menos 20 caracteres.`)
  }
  if (!/[a-z]/.test(password)) {
    throw new Error('La contraseña debe incluir al menos una letra minúscula.')
  }
  if (!/[A-Z]/.test(password)) {
    throw new Error('La contraseña debe incluir al menos una letra mayúscula.')
  }
  if (!/\d/.test(password)) {
    throw new Error('La contraseña debe incluir al menos un número.')
  }
  if (!/[^A-Za-z0-9]/.test(password)) {
    throw new Error('La contraseña debe incluir al menos un símbolo especial.')
  }
}

function mapAssignmentPayload(assignment) {
  return {
    categoria_id: Number(assignment.categoria_id),
    cantidad: Number(assignment.cantidad || 1),
    nota: toNullableString(assignment.nota),
  }
}

function haveSameKeys(a, b, keys) {
  return keys.every((key) => {
    const left = a?.[key] ?? null
    const right = b?.[key] ?? null
    return String(left) === String(right)
  })
}

async function runInBatches(tasks, batchSize = 3) {
  for (let i = 0; i < tasks.length; i += batchSize) {
    const batch = tasks.slice(i, i + batchSize)
    await Promise.all(batch.map((task) => task()))
  }
}

export async function saveTicketsInBatch({ original, draft }) {
  const sdk = getSdkClient()
  const originalById = new Map(original.filter((item) => item.id).map((item) => [item.id, item]))
  const draftById = new Map(draft.filter((item) => item.id).map((item) => [item.id, item]))

  const deletedProductIds = original
    .filter((item) => item.id && !draftById.has(item.id))
    .map((item) => item.id)

  const newProducts = draft.filter((item) => !item.id)
  const existingProducts = draft.filter((item) => item.id && !deletedProductIds.includes(item.id))

  const createdIdByLocalKey = new Map()

  const createTasks = newProducts.map((ticket) => async () => {
    const payload = {
      ...mapTicketPayload(ticket),
      categorias: (ticket.categorias ?? []).map(mapCategoryPayload),
    }
    const created = await sdk.productos.create(payload)
    createdIdByLocalKey.set(ticket.localKey, created.id)
  })

  await runInBatches(createTasks, 2)

  const updateProductTasks = []
  for (const ticket of existingProducts) {
    const before = originalById.get(ticket.id)
    if (!before) continue

    const changed = !haveSameKeys(before, ticket, [
      'nombre',
      'ubicacion',
      'estadio',
      'ubicacion_estadio',
      'fecha',
      'descripcion',
      'imagen',
      'is_active',
    ])
    if (changed) {
      updateProductTasks.push(async () => {
        await sdk.productos.update(ticket.id, mapTicketPayload(ticket))
      })
    }
  }

  await runInBatches(updateProductTasks, 3)

  const categoryTasks = []
  for (const ticket of existingProducts) {
    const originalTicket = originalById.get(ticket.id)
    if (!originalTicket) continue

    const originalCats = originalTicket.categorias ?? []
    const draftCats = ticket.categorias ?? []

    const originalCatsById = new Map(originalCats.filter((cat) => cat.id).map((cat) => [cat.id, cat]))
    const draftCatsById = new Map(draftCats.filter((cat) => cat.id).map((cat) => [cat.id, cat]))

    for (const cat of originalCats) {
      if (cat.id && !draftCatsById.has(cat.id)) {
        categoryTasks.push(async () => {
          await sdk.categorias.delete(cat.id)
        })
      }
    }

    for (const cat of draftCats) {
      if (!cat.id) {
        categoryTasks.push(async () => {
          await sdk.productos.createCategoria(ticket.id, mapCategoryPayload(cat))
        })
        continue
      }

      const beforeCat = originalCatsById.get(cat.id)
      if (!beforeCat) continue

      const changedCat = !haveSameKeys(beforeCat, cat, [
        'nombre',
        'descripcion',
        'precio',
        'moneda',
        'unidades_disponibles',
        'limite_por_usuario',
        'activo',
        'is_active',
      ])

      if (changedCat) {
        categoryTasks.push(async () => {
          await sdk.categorias.update(cat.id, mapCategoryPayload(cat))
        })
      }
    }
  }

  await runInBatches(categoryTasks, 4)

  const deleteProductTasks = deletedProductIds.map((id) => async () => {
    await sdk.productos.delete(id)
  })
  await runInBatches(deleteProductTasks, 2)

  return true
}

export async function saveUsersInBatch({ original, draft }) {
  const sdk = getSdkClient()
  const originalById = new Map(original.filter((item) => item.id).map((item) => [item.id, item]))
  const draftById = new Map(draft.filter((item) => item.id).map((item) => [item.id, item]))

  const removedExistingUsers = original
    .filter((item) => item.id && !draftById.has(item.id))
    .map((item) => item.id)

  const newUsers = draft.filter((item) => !item.id)
  const existingUsers = draft.filter((item) => item.id)

  for (const user of draft) {
    validateUserPasswordIfPresent(user)
  }

  for (const user of newUsers) {
    const email = String(user.email || '').trim()
    const password = String(user.password || '').trim()
    if (!email) {
      throw new Error('Todo usuario nuevo debe tener email.')
    }
    if (!password) {
      throw new Error(`El usuario nuevo ${email} requiere contraseña inicial.`)
    }
  }

  const createdUserIdByLocalKey = new Map()

  const createTasks = newUsers.map((user) => async () => {
      const created = await sdk.usuarios.create(mapUserCreatePayload(user))
      createdUserIdByLocalKey.set(user.localKey, created.id)
    })

  await runInBatches(createTasks, 2)

  const updateTasks = []

  for (const user of existingUsers) {
    const before = originalById.get(user.id)
    if (!before) continue

    const passwordChanged = Boolean(String(user.password || '').trim())
    const changed =
      passwordChanged ||
      !haveSameKeys(before, user, ['telefono', 'nombre', 'apellido', 'pais', 'is_active', 'is_admin'])
    if (changed) {
      updateTasks.push(async () => {
        await sdk.usuarios.update(user.id, mapUserUpdatePayload(user))
      })
    }
  }

  for (const userId of removedExistingUsers) {
    updateTasks.push(async () => {
      await sdk.usuarios.delete(userId)
    })
  }

  await runInBatches(updateTasks, 3)

  const assignmentTasks = []
  for (const user of draft) {
    const targetUserId = user.id || createdUserIdByLocalKey.get(user.localKey)
    if (!targetUserId) continue

    const before = user.id ? originalById.get(user.id) : null
    const beforeAssignments = before?.assignments ?? []
    const currentAssignments = user.assignments ?? []

    const beforeById = new Map(beforeAssignments.filter((item) => item.id).map((item) => [item.id, item]))
    const currentById = new Map(currentAssignments.filter((item) => item.id).map((item) => [item.id, item]))

    for (const oldItem of beforeAssignments) {
      if (oldItem.id && !currentById.has(oldItem.id)) {
        assignmentTasks.push(async () => {
          await sdk.usuarios.deleteTicket(targetUserId, oldItem.id)
        })
      }
    }

    for (const item of currentAssignments) {
      if (!item.categoria_id) continue

      if (!item.id) {
        assignmentTasks.push(async () => {
          await sdk.usuarios.assignTicket(targetUserId, mapAssignmentPayload(item))
        })
        continue
      }

      const beforeItem = beforeById.get(item.id)
      if (!beforeItem) continue

      const changedAssignment = !haveSameKeys(beforeItem, item, ['categoria_id', 'cantidad', 'nota'])
      if (changedAssignment) {
        assignmentTasks.push(async () => {
          await sdk.usuarios.updateTicket(targetUserId, item.id, {
            cantidad: Number(item.cantidad || 1),
            nota: item.nota || null,
          })
        })
      }
    }
  }

  await runInBatches(assignmentTasks, 4)

  return { warnings: [] }
}
