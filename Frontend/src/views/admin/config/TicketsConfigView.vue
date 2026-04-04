<script setup>
import { computed, onMounted, ref } from 'vue'
import InternalPanelLayout from '../../../components/layout/InternalPanelLayout.vue'
import TicketConfigCard from '../../../components/admin/TicketConfigCard.vue'
import AppLoader from '../../../components/common/AppLoader.vue'
import { TICKET_FORM_FIELDS, CATEGORY_FORM_FIELDS } from '../../../config/adminForms'
import { ROUTES } from '../../../config/routes'
import { useAdminConfigStore } from '../../../stores/adminConfig'

const PAGE_SIZE_OPTIONS = [10, 20, 50]

const adminStore = useAdminConfigStore()
const filterName = ref('')
const filterId = ref('')
const filterLocation = ref('')

const links = [
  { label: 'Tickets', to: ROUTES.adminConfig },
  { label: 'Usuarios', to: ROUTES.adminUsuarios },
  { label: 'Pedidos', to: ROUTES.adminPedidos },
  { label: 'Métricas', to: ROUTES.adminMetricas },
]

const messageClass = computed(() => {
  if (!adminStore.saveMessages.length) return ''
  return adminStore.saveMessages.some((item) => item.toLowerCase().includes('no fue posible'))
    ? 'alert alert-warning'
    : 'alert alert-success'
})

const ticketsCargados = computed(() => adminStore.hasLoadedTickets)
const paginacionTickets = computed(() => adminStore.ticketsPagination)
const puedePaginaAnterior = computed(() => paginacionTickets.value.page > 1)
const puedePaginaSiguiente = computed(() => Boolean(paginacionTickets.value.hasMore))

const filteredTickets = computed(() => {
  if (!ticketsCargados.value) return []

  const nameQuery = filterName.value.trim().toLowerCase()
  const idQuery = filterId.value.trim()
  const locationQuery = filterLocation.value.trim().toLowerCase()

  return adminStore.ticketsDraft.filter((ticket) => {
    const matchesName = !nameQuery || String(ticket.nombre || '').toLowerCase().includes(nameQuery)
    const matchesId = !idQuery || String(ticket.id || '').includes(idQuery)
    const matchesLocation = !locationQuery || String(ticket.ubicacion || '').toLowerCase().includes(locationQuery)
    return matchesName && matchesId && matchesLocation
  })
})

const ticketMetrics = computed(() => {
  const base = adminStore.ticketsDraft
  const totalCategorias = base.reduce((acc, item) => acc + (item.categorias?.length || 0), 0)
  return {
    total: base.length,
    activos: base.filter((item) => item.is_active).length,
    categorias: totalCategorias,
    filtrados: filteredTickets.value.length,
  }
})

function toErrorMessage(error) {
  return error?.message || 'No se pudieron cargar los tickets.'
}

async function cargarTickets({ force = false, page = null, pageSize = null } = {}) {
  adminStore.clearMessages()
  try {
    await adminStore.loadTicketsPage({
      page: page ?? paginacionTickets.value.page,
      pageSize: pageSize ?? paginacionTickets.value.pageSize,
      force,
    })
  } catch (error) {
    adminStore.saveMessages = [toErrorMessage(error)]
  }
}

async function cambiarPagina(delta) {
  await cargarTickets({
    page: paginacionTickets.value.page + delta,
  })
}

async function cambiarTamanoPagina(event) {
  const nuevoTamano = Number(event?.target?.value || paginacionTickets.value.pageSize)
  await cargarTickets({
    page: 1,
    pageSize: nuevoTamano,
  })
}

async function onSave() {
  try {
    await adminStore.saveTicketChanges()
  } catch (error) {
    adminStore.saveMessages = [error?.message || 'No se pudieron guardar los cambios.']
  }
}

async function onUploadTicketImage(ticketKey, file) {
  adminStore.clearMessages()
  try {
    await adminStore.uploadTicketImage(ticketKey, file)
    adminStore.saveMessages = ['Imagen subida correctamente. Recuerda guardar cambios para persistirla en el ticket.']
  } catch (error) {
    adminStore.saveMessages = [error?.message || 'No fue posible subir la imagen del ticket.']
  }
}

async function onAddTicket() {
  if (!ticketsCargados.value) {
    await cargarTickets()
  }
  if (!adminStore.hasLoadedTickets) return
  adminStore.addTicketDraft()
}

onMounted(() => {
  if (!adminStore.hasLoadedTickets) {
    cargarTickets()
  }
})
</script>

<template>
  <InternalPanelLayout
    title="Configuración de tickets"
    subtitle="Carga bajo demanda y paginación para editar tickets sin saturar la API."
    :links="links"
  >
    <div class="col-12">
      <section class="admin-toolbar mb-3">
        <div>
          <p class="admin-toolbar-kicker mb-1">Admin / Configuración / Tickets</p>
          <h2 class="h5 fw-bold mb-0">Panel de tickets</h2>
        </div>
        <div class="d-flex flex-wrap gap-2">
          <button
            class="btn btn-outline-primary"
            type="button"
            :disabled="adminStore.isLoading"
            @click="onAddTicket"
          >
            + Crear ticket
          </button>
          <button
            class="btn btn-primary"
            type="button"
            :disabled="adminStore.isLoading"
            @click="cargarTickets({ force: ticketsCargados })"
          >
            {{
              adminStore.isLoading
                ? 'Cargando...'
                : ticketsCargados
                  ? 'Actualizar página'
                  : 'Cargar tickets'
            }}
          </button>
        </div>
      </section>

      <div v-if="adminStore.saveMessages.length" :class="messageClass" role="alert">
        <p v-for="(message, idx) in adminStore.saveMessages" :key="idx" class="mb-1">{{ message }}</p>
      </div>

      <div v-if="!ticketsCargados" class="empty-state-admin">
        <p class="mb-2">Este módulo usa carga bajo demanda. Presiona el botón para obtener la primera página.</p>
      </div>

      <template v-else>
        <section class="admin-filters-panel mb-3">
          <div class="row g-2">
            <div class="col-12 col-lg-3">
              <label class="form-label fw-semibold small text-uppercase mb-1">Buscar por nombre</label>
              <input v-model.trim="filterName" class="form-control admin-control" type="text" placeholder="Ej: Quarterfinals" />
            </div>
            <div class="col-12 col-lg-3">
              <label class="form-label fw-semibold small text-uppercase mb-1">Buscar por ID</label>
              <input v-model.trim="filterId" class="form-control admin-control" type="text" inputmode="numeric" placeholder="Ej: 7" />
            </div>
            <div class="col-12 col-lg-3">
              <label class="form-label fw-semibold small text-uppercase mb-1">Buscar por ubicación</label>
              <input v-model.trim="filterLocation" class="form-control admin-control" type="text" placeholder="Ej: Miami" />
            </div>
            <div class="col-12 col-lg-3">
              <label class="form-label fw-semibold small text-uppercase mb-1">Items por página</label>
              <select class="form-select admin-control" :value="paginacionTickets.pageSize" @change="cambiarTamanoPagina">
                <option v-for="size in PAGE_SIZE_OPTIONS" :key="size" :value="size">{{ size }}</option>
              </select>
            </div>
          </div>

          <div class="admin-metrics-grid mt-3">
            <article class="admin-metric-card">
              <p class="admin-metric-label mb-1">Página</p>
              <p class="admin-metric-value mb-0">{{ paginacionTickets.page }}</p>
            </article>
            <article class="admin-metric-card">
              <p class="admin-metric-label mb-1">Tickets cargados</p>
              <p class="admin-metric-value mb-0">{{ ticketMetrics.total }}</p>
            </article>
            <article class="admin-metric-card">
              <p class="admin-metric-label mb-1">Activos</p>
              <p class="admin-metric-value mb-0">{{ ticketMetrics.activos }}</p>
            </article>
            <article class="admin-metric-card">
              <p class="admin-metric-label mb-1">Coincidencias</p>
              <p class="admin-metric-value mb-0">{{ ticketMetrics.filtrados }}</p>
            </article>
          </div>
        </section>

        <div v-if="adminStore.isLoading" class="admin-loading-box">
          <AppLoader variant="skeleton-cards" :count="3" />
        </div>

        <div v-else class="d-grid gap-3">
          <TicketConfigCard
            v-for="ticket in filteredTickets"
            :key="ticket.localKey"
            :ticket="ticket"
            :ticket-fields="TICKET_FORM_FIELDS"
            :category-fields="CATEGORY_FORM_FIELDS"
            :is-uploading-image="Boolean(adminStore.uploadingTicketImageByKey[ticket.localKey])"
            @update-ticket-field="adminStore.updateTicketField"
            @remove-ticket="adminStore.removeTicketDraft"
            @add-category="adminStore.addCategoryDraft"
            @update-category-field="adminStore.updateCategoryField"
            @remove-category="adminStore.removeCategoryDraft"
            @upload-ticket-image="onUploadTicketImage"
          />

          <div v-if="!filteredTickets.length" class="empty-state-admin">
            <p v-if="adminStore.ticketsDraft.length" class="mb-0">No hay tickets que coincidan con los filtros actuales.</p>
            <p v-else class="mb-0">No hay tickets en esta página. Cambia de página o añade uno nuevo.</p>
          </div>
        </div>

        <section class="admin-pagination mt-3">
          <button class="btn btn-outline-light" type="button" :disabled="!puedePaginaAnterior || adminStore.isLoading" @click="cambiarPagina(-1)">
            Anterior
          </button>
          <p class="admin-pagination-label mb-0">Página {{ paginacionTickets.page }}</p>
          <button class="btn btn-outline-light" type="button" :disabled="!puedePaginaSiguiente || adminStore.isLoading" @click="cambiarPagina(1)">
            Siguiente
          </button>
        </section>

        <footer class="admin-actions-footer mt-4">
          <button class="btn btn-outline-primary" type="button" :disabled="adminStore.isLoading" @click="onAddTicket">
            + Crear ticket
          </button>
          <button class="btn btn-outline-light" type="button" :disabled="!adminStore.hasTicketChanges" @click="adminStore.cancelTicketChanges">
            Cancelar
          </button>
          <button class="btn btn-primary" type="button" :disabled="!adminStore.hasTicketChanges || adminStore.isSavingTickets" @click="onSave">
            {{ adminStore.isSavingTickets ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </footer>
      </template>
    </div>
  </InternalPanelLayout>
</template>
