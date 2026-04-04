<script setup>
import { computed, onMounted, ref } from 'vue'
import InternalPanelLayout from '../../../components/layout/InternalPanelLayout.vue'
import UserConfigCard from '../../../components/admin/UserConfigCard.vue'
import AppLoader from '../../../components/common/AppLoader.vue'
import { USER_FORM_FIELDS } from '../../../config/adminForms'
import { ROUTES } from '../../../config/routes'
import { useAdminConfigStore } from '../../../stores/adminConfig'

const PAGE_SIZE_OPTIONS = [10, 20, 50]

const adminStore = useAdminConfigStore()
const filterEmail = ref('')
const filterId = ref('')
const filterPais = ref('')

const links = [
  { label: 'Tickets', to: ROUTES.adminConfig },
  { label: 'Usuarios', to: ROUTES.adminUsuarios },
  { label: 'Pedidos', to: ROUTES.adminPedidos },
  { label: 'Métricas', to: ROUTES.adminMetricas },
]

const categoryOptions = computed(() => adminStore.categoryOptions)
const usuariosCargados = computed(() => adminStore.hasLoadedUsers)
const paginacionUsuarios = computed(() => adminStore.usersPagination)
const puedePaginaAnterior = computed(() => paginacionUsuarios.value.page > 1)
const puedePaginaSiguiente = computed(() => Boolean(paginacionUsuarios.value.hasMore))

const filteredUsers = computed(() => {
  if (!usuariosCargados.value) return []

  const emailQuery = filterEmail.value.trim().toLowerCase()
  const idQuery = filterId.value.trim()
  const paisQuery = filterPais.value.trim().toLowerCase()

  return adminStore.usersDraft.filter((user) => {
    const matchesEmail = !emailQuery || String(user.email || '').toLowerCase().includes(emailQuery)
    const matchesId = !idQuery || String(user.id || '').includes(idQuery)
    const matchesPais = !paisQuery || String(user.pais || '').toLowerCase().includes(paisQuery)
    return matchesEmail && matchesId && matchesPais
  })
})

const usersMetrics = computed(() => {
  const base = adminStore.usersDraft
  const filtered = filteredUsers.value
  return {
    total: base.length,
    admins: base.filter((u) => u.is_admin).length,
    activos: base.filter((u) => u.is_active).length,
    filtrados: filtered.length,
  }
})

const messageClass = computed(() => {
  if (!adminStore.saveMessages.length) return ''
  return adminStore.saveMessages.some((item) => item.toLowerCase().includes('no fue posible'))
    ? 'alert alert-warning'
    : 'alert alert-success'
})

function toErrorMessage(error) {
  return error?.message || 'No se pudieron cargar los usuarios.'
}

async function cargarUsuarios({ force = false, page = null, pageSize = null } = {}) {
  adminStore.clearMessages()
  try {
    await Promise.all([
      adminStore.loadUsersPage({
        page: page ?? paginacionUsuarios.value.page,
        pageSize: pageSize ?? paginacionUsuarios.value.pageSize,
        force,
      }),
      adminStore.loadCategoryOptions(),
    ])
  } catch (error) {
    adminStore.saveMessages = [toErrorMessage(error)]
  }
}

async function cambiarPagina(delta) {
  await cargarUsuarios({
    page: paginacionUsuarios.value.page + delta,
  })
}

async function cambiarTamanoPagina(event) {
  const nuevoTamano = Number(event?.target?.value || paginacionUsuarios.value.pageSize)
  await cargarUsuarios({
    page: 1,
    pageSize: nuevoTamano,
  })
}

async function onSave() {
  try {
    await adminStore.saveUserChanges()
  } catch (error) {
    adminStore.saveMessages = [error?.message || 'No se pudieron guardar los cambios.']
  }
}

async function onAddUser() {
  if (!usuariosCargados.value) {
    await cargarUsuarios()
  }
  if (!adminStore.hasLoadedUsers) return
  adminStore.addUserDraft()
}

onMounted(() => {
  if (!adminStore.hasLoadedUsers) {
    cargarUsuarios()
  }
})
</script>

<template>
  <InternalPanelLayout
    title="Configuración de usuarios"
    subtitle="Carga bajo demanda y paginación para gestionar usuarios con menor carga en API."
    :links="links"
  >
    <div class="col-12">
      <section class="admin-toolbar mb-3">
        <div>
          <p class="admin-toolbar-kicker mb-1">Admin / Configuración / Usuarios</p>
          <h2 class="h5 fw-bold mb-0">Panel de usuarios</h2>
        </div>
        <div class="d-flex flex-wrap gap-2">
          <button
            class="btn btn-outline-primary"
            type="button"
            :disabled="adminStore.isLoading || adminStore.isLoadingCategoryOptions"
            @click="onAddUser"
          >
            + Crear usuario
          </button>
          <button
            class="btn btn-primary"
            type="button"
            :disabled="adminStore.isLoading || adminStore.isLoadingCategoryOptions"
            @click="cargarUsuarios({ force: usuariosCargados })"
          >
            {{
              adminStore.isLoading || adminStore.isLoadingCategoryOptions
                ? 'Cargando...'
                : usuariosCargados
                  ? 'Actualizar página'
                  : 'Cargar usuarios'
            }}
          </button>
        </div>
      </section>

      <div v-if="adminStore.saveMessages.length" :class="messageClass" role="alert">
        <p v-for="(message, idx) in adminStore.saveMessages" :key="idx" class="mb-1">{{ message }}</p>
      </div>

      <div v-if="!usuariosCargados" class="empty-state-admin">
        <p class="mb-2">Este módulo usa carga bajo demanda. Presiona el botón para obtener la primera página.</p>
      </div>

      <template v-else>
        <section class="admin-filters-panel mb-3">
          <div class="row g-2">
            <div class="col-12 col-lg-3">
              <label class="form-label fw-semibold small text-uppercase mb-1">Buscar por correo</label>
              <input v-model.trim="filterEmail" class="form-control admin-control" type="text" placeholder="usuario@dominio.com" />
            </div>
            <div class="col-12 col-lg-3">
              <label class="form-label fw-semibold small text-uppercase mb-1">Buscar por ID</label>
              <input v-model.trim="filterId" class="form-control admin-control" type="text" inputmode="numeric" placeholder="Ej: 12" />
            </div>
            <div class="col-12 col-lg-3">
              <label class="form-label fw-semibold small text-uppercase mb-1">Buscar por país</label>
              <input v-model.trim="filterPais" class="form-control admin-control" type="text" placeholder="Ej: Colombia" />
            </div>
            <div class="col-12 col-lg-3">
              <label class="form-label fw-semibold small text-uppercase mb-1">Items por página</label>
              <select class="form-select admin-control" :value="paginacionUsuarios.pageSize" @change="cambiarTamanoPagina">
                <option v-for="size in PAGE_SIZE_OPTIONS" :key="size" :value="size">{{ size }}</option>
              </select>
            </div>
          </div>

          <div class="admin-metrics-grid mt-3">
            <article class="admin-metric-card">
              <p class="admin-metric-label mb-1">Página</p>
              <p class="admin-metric-value mb-0">{{ paginacionUsuarios.page }}</p>
            </article>
            <article class="admin-metric-card">
              <p class="admin-metric-label mb-1">Usuarios cargados</p>
              <p class="admin-metric-value mb-0">{{ usersMetrics.total }}</p>
            </article>
            <article class="admin-metric-card">
              <p class="admin-metric-label mb-1">Admins</p>
              <p class="admin-metric-value mb-0">{{ usersMetrics.admins }}</p>
            </article>
            <article class="admin-metric-card">
              <p class="admin-metric-label mb-1">Coincidencias</p>
              <p class="admin-metric-value mb-0">{{ usersMetrics.filtrados }}</p>
            </article>
          </div>
        </section>

        <div v-if="adminStore.isLoading" class="admin-loading-box">
          <AppLoader variant="skeleton-cards" :count="3" />
        </div>

        <div v-else class="d-grid gap-3">
          <UserConfigCard
            v-for="(user, index) in filteredUsers"
            :key="user.localKey"
            :user="user"
            :index="index"
            :user-fields="USER_FORM_FIELDS"
            :category-options="categoryOptions"
            @update-user-field="adminStore.updateUserField"
            @remove-user="adminStore.removeUserDraft"
            @ensure-assignments="adminStore.ensureUserAssignments"
            @add-assignment="adminStore.addAssignment"
            @remove-assignment="adminStore.removeAssignment"
            @update-assignment-field="adminStore.updateAssignmentField"
          />

          <div v-if="!filteredUsers.length" class="empty-state-admin">
            <p v-if="adminStore.usersDraft.length" class="mb-0">No hay usuarios que coincidan con los filtros actuales.</p>
            <p v-else class="mb-0">No hay usuarios en esta página. Cambia de página o crea uno nuevo.</p>
          </div>
        </div>

        <section class="admin-pagination mt-3">
          <button class="btn btn-outline-light" type="button" :disabled="!puedePaginaAnterior || adminStore.isLoading" @click="cambiarPagina(-1)">
            Anterior
          </button>
          <p class="admin-pagination-label mb-0">Página {{ paginacionUsuarios.page }}</p>
          <button class="btn btn-outline-light" type="button" :disabled="!puedePaginaSiguiente || adminStore.isLoading" @click="cambiarPagina(1)">
            Siguiente
          </button>
        </section>

        <footer class="admin-actions-footer mt-4">
          <button class="btn btn-outline-primary" type="button" :disabled="adminStore.isLoading" @click="onAddUser">
            + Crear usuario
          </button>
          <button class="btn btn-outline-light" type="button" :disabled="!adminStore.hasUserChanges" @click="adminStore.cancelUserChanges">
            Cancelar
          </button>
          <button class="btn btn-primary" type="button" :disabled="!adminStore.hasUserChanges || adminStore.isSavingUsers" @click="onSave">
            {{ adminStore.isSavingUsers ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </footer>
      </template>
    </div>
  </InternalPanelLayout>
</template>
