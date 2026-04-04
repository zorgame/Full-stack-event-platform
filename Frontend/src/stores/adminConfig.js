import { defineStore } from 'pinia'
import {
  fetchCategoryOptionsCatalog,
  fetchTicketsConfigPage,
  fetchUserAssignments,
  fetchUsersConfigPage,
  normalizeTicket,
  normalizeUser,
  saveTicketsInBatch,
  saveUsersInBatch,
  uploadTicketImageAsset,
} from '../services/adminConfigService'

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function tempKey(prefix) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`
}

function sanitizePositiveInt(value, fallback) {
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback
}

function buildPageKey(page, pageSize) {
  return `${page}:${pageSize}`
}

export const useAdminConfigStore = defineStore('admin-config', {
  state: () => ({
    isLoading: false,
    isSavingTickets: false,
    isSavingUsers: false,
    isLoadingCategoryOptions: false,
    uploadingTicketImageByKey: {},
    hasLoaded: false,
    hasLoadedTickets: false,
    hasLoadedUsers: false,
    hasLoadedCategoryOptions: false,
    ticketsOriginal: [],
    ticketsDraft: [],
    usersOriginal: [],
    usersDraft: [],
    categoryOptions: [],
    ticketsPageCache: {},
    usersPageCache: {},
    ticketsPagination: {
      page: 1,
      pageSize: 10,
      hasMore: false,
    },
    usersPagination: {
      page: 1,
      pageSize: 10,
      hasMore: false,
    },
    saveMessages: [],
  }),

  getters: {
    hasTicketChanges(state) {
      return JSON.stringify(state.ticketsOriginal) !== JSON.stringify(state.ticketsDraft)
    },
    hasUserChanges(state) {
      return JSON.stringify(state.usersOriginal) !== JSON.stringify(state.usersDraft)
    },
  },

  actions: {
    _setHasLoadedState() {
      this.hasLoaded = this.hasLoadedTickets || this.hasLoadedUsers
    },

    _syncCurrentTicketCache() {
      const key = buildPageKey(this.ticketsPagination.page, this.ticketsPagination.pageSize)
      const cached = this.ticketsPageCache[key]
      if (!cached) return

      this.ticketsPageCache = {
        ...this.ticketsPageCache,
        [key]: {
          ...cached,
          original: clone(this.ticketsOriginal),
          draft: clone(this.ticketsDraft),
          hasMore: Boolean(this.ticketsPagination.hasMore),
        },
      }
    },

    _syncCurrentUserCache() {
      const key = buildPageKey(this.usersPagination.page, this.usersPagination.pageSize)
      const cached = this.usersPageCache[key]
      if (!cached) return

      this.usersPageCache = {
        ...this.usersPageCache,
        [key]: {
          ...cached,
          original: clone(this.usersOriginal),
          draft: clone(this.usersDraft),
          hasMore: Boolean(this.usersPagination.hasMore),
        },
      }
    },

    _assertCanChangeTicketsPage({ page, pageSize, force }) {
      const changedPage =
        Number(page) !== Number(this.ticketsPagination.page) ||
        Number(pageSize) !== Number(this.ticketsPagination.pageSize)

      if (!force && changedPage && this.hasTicketChanges) {
        throw new Error('Guarda o cancela los cambios de tickets antes de cambiar de página.')
      }
    },

    _assertCanChangeUsersPage({ page, pageSize, force }) {
      const changedPage =
        Number(page) !== Number(this.usersPagination.page) ||
        Number(pageSize) !== Number(this.usersPagination.pageSize)

      if (!force && changedPage && this.hasUserChanges) {
        throw new Error('Guarda o cancela los cambios de usuarios antes de cambiar de página.')
      }
    },

    async loadTicketsPage({ page = 1, pageSize = this.ticketsPagination.pageSize, force = false } = {}) {
      const targetPage = sanitizePositiveInt(page, 1)
      const targetPageSize = sanitizePositiveInt(pageSize, 10)
      this._assertCanChangeTicketsPage({ page: targetPage, pageSize: targetPageSize, force })

      const cacheKey = buildPageKey(targetPage, targetPageSize)
      if (!force && this.ticketsPageCache[cacheKey]) {
        const cached = this.ticketsPageCache[cacheKey]
        this.ticketsOriginal = clone(cached.original)
        this.ticketsDraft = clone(cached.draft)
        this.ticketsPagination = {
          page: targetPage,
          pageSize: targetPageSize,
          hasMore: Boolean(cached.hasMore),
        }
        this.hasLoadedTickets = true
        this._setHasLoadedState()
        return
      }

      this.isLoading = true
      try {
        const skip = (targetPage - 1) * targetPageSize
        const rows = await fetchTicketsConfigPage({
          skip,
          limit: targetPageSize + 1,
          only_active: false,
        })

        const hasMore = rows.length > targetPageSize
        const pageRows = rows.slice(0, targetPageSize)

        this.ticketsOriginal = clone(pageRows)
        this.ticketsDraft = clone(pageRows)
        this.ticketsPagination = {
          page: targetPage,
          pageSize: targetPageSize,
          hasMore,
        }

        this.ticketsPageCache = {
          ...this.ticketsPageCache,
          [cacheKey]: {
            original: clone(pageRows),
            draft: clone(pageRows),
            hasMore,
          },
        }
        this.hasLoadedTickets = true
        this._setHasLoadedState()
      } finally {
        this.isLoading = false
      }
    },

    async loadUsersPage({ page = 1, pageSize = this.usersPagination.pageSize, force = false } = {}) {
      const targetPage = sanitizePositiveInt(page, 1)
      const targetPageSize = sanitizePositiveInt(pageSize, 10)
      this._assertCanChangeUsersPage({ page: targetPage, pageSize: targetPageSize, force })

      const cacheKey = buildPageKey(targetPage, targetPageSize)
      if (!force && this.usersPageCache[cacheKey]) {
        const cached = this.usersPageCache[cacheKey]
        this.usersOriginal = clone(cached.original)
        this.usersDraft = clone(cached.draft)
        this.usersPagination = {
          page: targetPage,
          pageSize: targetPageSize,
          hasMore: Boolean(cached.hasMore),
        }
        this.hasLoadedUsers = true
        this._setHasLoadedState()
        return
      }

      this.isLoading = true
      try {
        const skip = (targetPage - 1) * targetPageSize
        const rows = await fetchUsersConfigPage({ skip, limit: targetPageSize + 1 })

        const hasMore = rows.length > targetPageSize
        const pageRows = rows.slice(0, targetPageSize)

        this.usersOriginal = clone(pageRows)
        this.usersDraft = clone(pageRows)
        this.usersPagination = {
          page: targetPage,
          pageSize: targetPageSize,
          hasMore,
        }

        this.usersPageCache = {
          ...this.usersPageCache,
          [cacheKey]: {
            original: clone(pageRows),
            draft: clone(pageRows),
            hasMore,
          },
        }
        this.hasLoadedUsers = true
        this._setHasLoadedState()
      } finally {
        this.isLoading = false
      }
    },

    async loadCategoryOptions({ force = false } = {}) {
      if (this.hasLoadedCategoryOptions && !force) return

      this.isLoadingCategoryOptions = true
      try {
        this.categoryOptions = await fetchCategoryOptionsCatalog({
          skip: 0,
          limit: 500,
        })
        this.hasLoadedCategoryOptions = true
      } finally {
        this.isLoadingCategoryOptions = false
      }
    },

    async loadAdminConfig({ force = false } = {}) {
      await Promise.all([
        this.loadTicketsPage({
          page: 1,
          pageSize: this.ticketsPagination.pageSize,
          force,
        }),
        this.loadUsersPage({
          page: 1,
          pageSize: this.usersPagination.pageSize,
          force,
        }),
        this.loadCategoryOptions({ force }),
      ])
    },

    clearMessages() {
      this.saveMessages = []
    },

    clearTicketsPageCache() {
      this.ticketsPageCache = {}
    },

    clearUsersPageCache() {
      this.usersPageCache = {}
    },

    addTicketDraft() {
      this.ticketsDraft.push(
        normalizeTicket({
          nombre: '',
          ubicacion: '',
          estadio: '',
          ubicacion_estadio: '',
          fecha: null,
          descripcion: '',
          imagen: '',
          is_active: true,
          categorias: [],
        }),
      )
      this._syncCurrentTicketCache()
    },

    async uploadTicketImage(ticketKey, file) {
      const target = this.ticketsDraft.find((ticket) => ticket.localKey === ticketKey)
      if (!target) {
        throw new Error('No se encontró el ticket para subir la imagen.')
      }

      if (!(file instanceof File)) {
        throw new Error('Debes seleccionar un archivo de imagen válido.')
      }

      const allowedTypes = new Set(['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'])
      if (!allowedTypes.has(String(file.type || '').toLowerCase())) {
        throw new Error('Formato no permitido. Usa JPG, PNG, WEBP o GIF.')
      }

      const maxBytes = 5 * 1024 * 1024
      if (file.size > maxBytes) {
        throw new Error('La imagen supera el máximo permitido de 5 MB.')
      }

      this.uploadingTicketImageByKey = {
        ...this.uploadingTicketImageByKey,
        [ticketKey]: true,
      }

      try {
        const uploaded = await uploadTicketImageAsset(file)
        const imageUrl = String(uploaded?.imagen || uploaded?.url || '').trim()
        if (!imageUrl) {
          throw new Error('El servidor no devolvió una URL válida para la imagen.')
        }

        target.imagen = imageUrl
        this._syncCurrentTicketCache()
      } finally {
        this.uploadingTicketImageByKey = {
          ...this.uploadingTicketImageByKey,
          [ticketKey]: false,
        }
      }
    },

    removeTicketDraft(ticketKey) {
      this.ticketsDraft = this.ticketsDraft.filter((ticket) => ticket.localKey !== ticketKey)
      this._syncCurrentTicketCache()
    },

    updateTicketField(ticketKey, field, value) {
      const target = this.ticketsDraft.find((ticket) => ticket.localKey === ticketKey)
      if (!target) return
      target[field] = value
      this._syncCurrentTicketCache()
    },

    addCategoryDraft(ticketKey) {
      const ticket = this.ticketsDraft.find((item) => item.localKey === ticketKey)
      if (!ticket) return

      ticket.categorias.push({
        localKey: tempKey('cat'),
        id: null,
        producto_id: ticket.id ?? null,
        nombre: '',
        descripcion: '',
        precio: 1,
        moneda: 'USD',
        unidades_disponibles: 0,
        limite_por_usuario: null,
        activo: true,
        is_active: true,
      })
      this._syncCurrentTicketCache()
    },

    removeCategoryDraft(ticketKey, categoryKey) {
      const ticket = this.ticketsDraft.find((item) => item.localKey === ticketKey)
      if (!ticket) return
      ticket.categorias = ticket.categorias.filter((category) => category.localKey !== categoryKey)
      this._syncCurrentTicketCache()
    },

    updateCategoryField(ticketKey, categoryKey, field, value) {
      const ticket = this.ticketsDraft.find((item) => item.localKey === ticketKey)
      if (!ticket) return
      const category = ticket.categorias.find((item) => item.localKey === categoryKey)
      if (!category) return
      category[field] = value
      this._syncCurrentTicketCache()
    },

    cancelTicketChanges() {
      this.ticketsDraft = clone(this.ticketsOriginal)
      this._syncCurrentTicketCache()
      this.clearMessages()
    },

    async saveTicketChanges() {
      this.isSavingTickets = true
      this.clearMessages()
      try {
        await saveTicketsInBatch({
          original: this.ticketsOriginal,
          draft: this.ticketsDraft,
        })

        const currentPage = this.ticketsPagination.page
        const currentPageSize = this.ticketsPagination.pageSize
        this.clearTicketsPageCache()

        await this.loadTicketsPage({
          page: currentPage,
          pageSize: currentPageSize,
          force: true,
        })

        await this.loadCategoryOptions({ force: true })
        this.saveMessages.push('Cambios de tickets guardados correctamente.')
      } catch (error) {
        this.saveMessages.push(error?.message || 'No se pudieron guardar los cambios de tickets.')
        throw error
      } finally {
        this.isSavingTickets = false
      }
    },

    addUserDraft() {
      this.usersDraft.push(
        normalizeUser({
          email: '',
          telefono: '',
          nombre: '',
          apellido: '',
          pais: '',
          is_active: true,
          is_admin: false,
        }),
      )
      this._syncCurrentUserCache()
    },

    removeUserDraft(userKey) {
      this.usersDraft = this.usersDraft.filter((user) => user.localKey !== userKey)
      this._syncCurrentUserCache()
    },

    updateUserField(userKey, field, value) {
      const user = this.usersDraft.find((item) => item.localKey === userKey)
      if (!user) return
      user[field] = value
      this._syncCurrentUserCache()
    },

    async ensureUserAssignments(userKey) {
      const user = this.usersDraft.find((item) => item.localKey === userKey)
      if (!user || !user.id || user.assignmentsLoaded || user.assignmentsLoading) return

      user.assignmentsLoading = true
      try {
        const assignments = await fetchUserAssignments(user.id)
        user.assignments = assignments
        user.assignmentsLoaded = true

        const originalUser = this.usersOriginal.find((item) => item.id === user.id)
        if (originalUser) {
          originalUser.assignments = clone(assignments)
          originalUser.assignmentsLoaded = true
        }

        this._syncCurrentUserCache()
      } finally {
        user.assignmentsLoading = false
      }
    },

    addAssignment(userKey, categoriaId = null) {
      const user = this.usersDraft.find((item) => item.localKey === userKey)
      if (!user) return
      user.assignments.push({
        localKey: tempKey('assign'),
        id: null,
        categoria_id: categoriaId,
        cantidad: 1,
        nota: '',
      })
      user.assignmentsLoaded = true
      this._syncCurrentUserCache()
    },

    removeAssignment(userKey, assignmentKey) {
      const user = this.usersDraft.find((item) => item.localKey === userKey)
      if (!user) return
      user.assignments = user.assignments.filter((item) => item.localKey !== assignmentKey)
      this._syncCurrentUserCache()
    },

    updateAssignmentField(userKey, assignmentKey, field, value) {
      const user = this.usersDraft.find((item) => item.localKey === userKey)
      if (!user) return
      const assignment = user.assignments.find((item) => item.localKey === assignmentKey)
      if (!assignment) return
      assignment[field] = value
      this._syncCurrentUserCache()
    },

    cancelUserChanges() {
      this.usersDraft = clone(this.usersOriginal)
      this._syncCurrentUserCache()
      this.clearMessages()
    },

    async saveUserChanges() {
      this.isSavingUsers = true
      this.clearMessages()
      try {
        const result = await saveUsersInBatch({
          original: this.usersOriginal,
          draft: this.usersDraft,
        })

        const currentPage = this.usersPagination.page
        const currentPageSize = this.usersPagination.pageSize
        this.clearUsersPageCache()

        await this.loadUsersPage({
          page: currentPage,
          pageSize: currentPageSize,
          force: true,
        })

        this.saveMessages.push('Cambios de usuarios guardados correctamente.')
        if (result?.warnings?.length) {
          this.saveMessages.push(...result.warnings)
        }
      } catch (error) {
        this.saveMessages.push(error?.message || 'No se pudieron guardar los cambios de usuarios.')
        throw error
      } finally {
        this.isSavingUsers = false
      }
    },
  },
})
