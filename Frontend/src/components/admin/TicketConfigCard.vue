<script setup>
import { computed, ref } from 'vue'
import AdminDynamicField from './AdminDynamicField.vue'
import { API_CONFIG } from '../../config/constants'

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    required: false,
    default: 0,
  },
  ticketFields: {
    type: Array,
    required: true,
  },
  categoryFields: {
    type: Array,
    required: true,
  },
  isUploadingImage: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update-ticket-field',
  'remove-ticket',
  'add-category',
  'update-category-field',
  'remove-category',
  'upload-ticket-image',
])

const isExpanded = ref(!props.ticket?.id)
const categoryExpandedState = ref({})
const fileInputRef = ref(null)

const ticketDisplayName = computed(() => props.ticket.nombre?.trim() || 'Nuevo ticket')

const imagePreviewUrl = computed(() => {
  const raw = String(props.ticket?.imagen || '').trim()
  if (!raw) return ''
  if (/^https?:\/\//i.test(raw) || raw.startsWith('data:')) return raw

  const baseURL = String(API_CONFIG.baseURL || '').replace(/\/+$/, '')
  if (!baseURL) return raw

  if (raw.startsWith('/')) {
    return `${baseURL}${raw}`
  }

  return `${baseURL}/${raw.replace(/^\/+/, '')}`
})

function categoryDisplayName(category) {
  return category?.nombre?.trim() || 'Nueva categoría'
}

function isCategoryExpanded(categoryKey) {
  return Boolean(categoryExpandedState.value[categoryKey])
}

function toggleCategory(categoryKey) {
  categoryExpandedState.value = {
    ...categoryExpandedState.value,
    [categoryKey]: !isCategoryExpanded(categoryKey),
  }
}

function updateTicketField(fieldKey, value) {
  emit('update-ticket-field', props.ticket.localKey, fieldKey, value)
}

function updateCategoryField(categoryKey, fieldKey, value) {
  emit('update-category-field', props.ticket.localKey, categoryKey, fieldKey, value)
}

function abrirSelectorImagen() {
  fileInputRef.value?.click()
}

function onArchivoImagenSeleccionado(event) {
  const file = event?.target?.files?.[0]
  if (!file) return
  emit('upload-ticket-image', props.ticket.localKey, file)
  event.target.value = ''
}

function limpiarImagenTicket() {
  emit('update-ticket-field', props.ticket.localKey, 'imagen', '')
}
</script>

<template>
  <article class="admin-card ticket-card-admin">
    <header class="admin-card-header">
      <button class="admin-collapse-btn" type="button" @click="isExpanded = !isExpanded">
        <span class="admin-collapse-icon" :class="{ open: isExpanded }">▾</span>
        <span class="fw-bold">{{ ticketDisplayName }}</span>
      </button>
      <div class="d-flex align-items-center gap-2">
        <span v-if="ticket.id" class="badge text-bg-light border">ID {{ ticket.id }}</span>
        <button class="btn btn-sm btn-outline-danger" type="button" @click="emit('remove-ticket', ticket.localKey)">
          Eliminar
        </button>
      </div>
    </header>

    <transition name="admin-expand">
      <div v-show="isExpanded" class="admin-card-body">
        <div class="row g-3">
          <div
            v-for="field in ticketFields"
            :key="field.key"
            class="col-12"
            :class="field.type === 'textarea' ? 'col-xl-12' : 'col-xl-6'"
          >
            <AdminDynamicField
              :field="field"
              :model-value="ticket[field.key]"
              @update:model-value="(value) => updateTicketField(field.key, value)"
            />
          </div>
        </div>

        <section class="admin-ticket-image-upload mt-3">
          <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-2">
            <p class="admin-pedido-etiqueta mb-0">Imagen del ticket</p>
            <div class="d-flex flex-wrap gap-2">
              <button
                class="btn btn-sm btn-primary"
                type="button"
                :disabled="isUploadingImage"
                @click="abrirSelectorImagen"
              >
                {{ isUploadingImage ? 'Subiendo...' : 'Subir imagen' }}
              </button>
              <button
                v-if="ticket.imagen"
                class="btn btn-sm btn-outline-danger"
                type="button"
                :disabled="isUploadingImage"
                @click="limpiarImagenTicket"
              >
                Quitar
              </button>
            </div>
          </div>

          <input
            ref="fileInputRef"
            class="d-none"
            type="file"
            accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
            @change="onArchivoImagenSeleccionado"
          />

          <p class="text-muted small mb-2">Formatos permitidos: JPG, PNG, WEBP y GIF (máx. 5 MB).</p>

          <div v-if="imagePreviewUrl" class="admin-ticket-image-preview">
            <img :src="imagePreviewUrl" :alt="`Imagen de ${ticketDisplayName}`" loading="lazy" />
          </div>
        </section>

        <div class="mt-4 d-flex justify-content-between align-items-center">
          <h4 class="h6 fw-bold mb-0">Categorías</h4>
          <button class="btn btn-sm btn-primary" type="button" @click="emit('add-category', ticket.localKey)">
            + Añadir categoría
          </button>
        </div>

        <div v-if="ticket.categorias.length" class="d-grid gap-2 mt-3">
          <article v-for="category in ticket.categorias" :key="category.localKey" class="category-subcard">
            <div class="d-flex justify-content-between align-items-center gap-2">
              <button class="admin-collapse-btn category-collapse-btn" type="button" @click="toggleCategory(category.localKey)">
                <span class="admin-collapse-icon" :class="{ open: isCategoryExpanded(category.localKey) }">▾</span>
                <span class="fw-semibold">{{ categoryDisplayName(category) }}</span>
              </button>
              <button class="btn btn-sm btn-outline-danger" type="button" @click="emit('remove-category', ticket.localKey, category.localKey)">
                Eliminar
              </button>
            </div>

            <transition name="admin-expand">
              <div v-show="isCategoryExpanded(category.localKey)" class="mt-3">
                <div class="row g-3">
                  <div
                    v-for="field in categoryFields"
                    :key="`${category.localKey}-${field.key}`"
                    class="col-12"
                    :class="field.type === 'textarea' ? 'col-xl-12' : 'col-xl-6'"
                  >
                    <AdminDynamicField
                      :field="field"
                      :model-value="category[field.key]"
                      @update:model-value="(value) => updateCategoryField(category.localKey, field.key, value)"
                    />
                  </div>
                </div>
              </div>
            </transition>
          </article>
        </div>

        <p v-else class="text-muted small mb-0 mt-3">Este ticket aún no tiene categorías.</p>
      </div>
    </transition>
  </article>
</template>
