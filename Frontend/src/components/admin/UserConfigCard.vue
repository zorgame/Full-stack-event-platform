<script setup>
import { computed, ref } from 'vue'
import AdminDynamicField from './AdminDynamicField.vue'
import { copiarTextoEnPortapapeles } from '../../utils/checkoutPresentation'

const props = defineProps({
  user: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    required: true,
  },
  userFields: {
    type: Array,
    required: true,
  },
  categoryOptions: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits([
  'update-user-field',
  'remove-user',
  'ensure-assignments',
  'add-assignment',
  'remove-assignment',
  'update-assignment-field',
])

const isExpanded = ref(!props.user?.id)
const passwordCopied = ref(false)

function firstWord(value) {
  const normalized = String(value || '').trim()
  if (!normalized) return ''
  return normalized.split(/\s+/)[0]
}

const userDisplayName = computed(() => {
  const firstName = firstWord(props.user.nombre)
  const firstLastName = firstWord(props.user.apellido)
  const fullName = [firstName, firstLastName].filter(Boolean).join(' ')
  return fullName || props.user.email || 'Nuevo usuario'
})

const selectedCategoryIds = computed(() => {
  const ids = new Set()
  for (const item of props.user.assignments ?? []) {
    const categoryId = Number(item.categoria_id)
    if (categoryId) ids.add(categoryId)
  }
  return ids
})

const availableCategoryCount = computed(() => {
  let count = 0
  for (const option of props.categoryOptions) {
    if (!selectedCategoryIds.value.has(Number(option.value))) {
      count += 1
    }
  }
  return count
})

const canAddAssignment = computed(() => {
  if (props.user.id && !props.user.assignmentsLoaded) return false
  return availableCategoryCount.value > 0
})

function optionsForAssignment(assignment) {
  const selected = Number(assignment.categoria_id) || null
  return props.categoryOptions.filter((option) => {
    const optionId = Number(option.value)
    return !selectedCategoryIds.value.has(optionId) || optionId === selected
  })
}

function firstAvailableCategoryId() {
  const candidate = props.categoryOptions.find((option) => !selectedCategoryIds.value.has(Number(option.value)))
  return candidate ? Number(candidate.value) : null
}

function onAddAssignment() {
  if (!canAddAssignment.value) return
  emit('add-assignment', props.user.localKey, firstAvailableCategoryId())
}

function updateUserField(fieldKey, value) {
  emit('update-user-field', props.user.localKey, fieldKey, value)
}

function updateAssignment(assignmentKey, fieldKey, value) {
  emit('update-assignment-field', props.user.localKey, assignmentKey, fieldKey, value)
}

function onToggleRole(event) {
  emit('update-user-field', props.user.localKey, 'is_admin', event.target.checked)
}

function randomIndex(max) {
  if (window?.crypto?.getRandomValues) {
    const randomBuffer = new Uint32Array(1)
    window.crypto.getRandomValues(randomBuffer)
    return randomBuffer[0] % max
  }
  return Math.floor(Math.random() * max)
}

function pickRandom(charset) {
  return charset[randomIndex(charset.length)]
}

function shuffleArray(values) {
  const output = [...values]
  for (let index = output.length - 1; index > 0; index -= 1) {
    const swapIndex = randomIndex(index + 1)
    const temp = output[index]
    output[index] = output[swapIndex]
    output[swapIndex] = temp
  }
  return output
}

function generarPasswordSegura(longitud = 20) {
  const targetLength = Number.isInteger(Number(longitud)) ? Math.max(20, Number(longitud)) : 20
  const lower = 'abcdefghijkmnopqrstuvwxyz'
  const upper = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
  const numbers = '23456789'
  const symbols = '!@#$%^&*()-_=+'
  const alphabet = `${lower}${upper}${numbers}${symbols}`

  const output = [pickRandom(lower), pickRandom(upper), pickRandom(numbers), pickRandom(symbols)]

  while (output.length < targetLength) {
    output.push(pickRandom(alphabet))
  }

  return shuffleArray(output).join('')
}

function onGeneratePassword() {
  const nuevaPassword = generarPasswordSegura(20)
  updateUserField('password', nuevaPassword)
  passwordCopied.value = false
}

async function onCopyPassword() {
  const password = String(props.user.password || '').trim()
  if (!password) return
  const copied = await copiarTextoEnPortapapeles(password)
  if (!copied) return
  passwordCopied.value = true
  setTimeout(() => {
    passwordCopied.value = false
  }, 1600)
}
</script>

<template>
  <article class="admin-card user-card-admin">
    <header class="admin-card-header">
      <button class="admin-collapse-btn" type="button" @click="isExpanded = !isExpanded">
        <span class="admin-collapse-icon" :class="{ open: isExpanded }">▾</span>
        <span class="fw-bold">{{ userDisplayName }}</span>
      </button>
      <div class="d-flex align-items-center gap-2">
        <span
          class="badge"
          :class="user.is_admin ? 'text-bg-warning' : 'text-bg-secondary'"
        >
          {{ user.is_admin ? 'Admin' : 'User' }}
        </span>
        <button class="btn btn-sm btn-outline-danger" type="button" @click="emit('remove-user', user.localKey)">
          Eliminar
        </button>
      </div>
    </header>

    <transition name="admin-expand">
      <div v-show="isExpanded" class="admin-card-body">
        <div class="row g-3">
          <div
            v-for="field in userFields"
            :key="field.key"
            class="col-12"
            :class="field.type === 'textarea' ? 'col-xl-12' : 'col-xl-6'"
          >
            <AdminDynamicField
              :field="field"
              :model-value="user[field.key]"
              @update:model-value="(value) => updateUserField(field.key, value)"
            />

            <div v-if="field.key === 'password'" class="d-flex flex-wrap align-items-center gap-2 mt-2">
              <button class="btn btn-sm btn-outline-primary" type="button" @click="onGeneratePassword">
                Generar segura
              </button>
              <button
                class="btn btn-sm btn-outline-secondary"
                type="button"
                :disabled="!String(user.password || '').trim()"
                @click="onCopyPassword"
              >
                {{ passwordCopied ? 'Copiada' : 'Copiar' }}
              </button>
              <span class="small text-muted">Genera 20 caracteres con mayúsculas, minúsculas, números y símbolos.</span>
            </div>
          </div>

          <div class="col-12 col-xl-6">
            <label class="form-label fw-semibold small text-uppercase mb-2">Rol (admin/user)</label>
            <div class="role-toggle">
              <div class="form-check form-switch mb-1">
                <input class="form-check-input" type="checkbox" :checked="user.is_admin" @change="onToggleRole" />
                <label class="form-check-label">Asignar administrador</label>
              </div>
              <p class="small text-muted mb-0">Este rol se guarda al confirmar los cambios.</p>
            </div>
          </div>
        </div>

        <div class="mt-4 d-flex flex-wrap justify-content-between align-items-center gap-2">
          <h4 class="h6 fw-bold mb-0">Tickets asignados</h4>
          <div class="d-flex flex-wrap gap-2">
            <button
              v-if="user.id && !user.assignmentsLoaded"
              class="btn btn-sm btn-outline-primary"
              type="button"
              :disabled="user.assignmentsLoading"
              @click="emit('ensure-assignments', user.localKey)"
            >
              {{ user.assignmentsLoading ? 'Cargando...' : 'Cargar asignaciones' }}
            </button>
            <button
              class="btn btn-sm btn-primary"
              type="button"
              :disabled="!canAddAssignment"
              @click="onAddAssignment"
            >
              {{ canAddAssignment ? '+ Asignar ticket' : 'Sin categorías disponibles' }}
            </button>
          </div>
        </div>

        <div v-if="user.assignments.length" class="d-grid gap-2 mt-2 assignment-list-compact">
          <article v-for="assignment in user.assignments" :key="assignment.localKey" class="assignment-subcard">
            <div class="row g-2 align-items-end">
              <div class="col-12 col-lg-5">
                <label class="form-label fw-semibold small text-uppercase mb-1">Categoría</label>
                <select
                  class="form-select admin-control"
                  :value="assignment.categoria_id || ''"
                  @change="updateAssignment(assignment.localKey, 'categoria_id', $event.target.value ? Number($event.target.value) : null)"
                >
                  <option value="">Seleccionar categoría</option>
                  <option v-for="option in optionsForAssignment(assignment)" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>

              <div class="col-6 col-lg-2">
                <label class="form-label fw-semibold small text-uppercase mb-1">Cantidad</label>
                <input
                  class="form-control admin-control"
                  type="number"
                  min="1"
                  :value="assignment.cantidad"
                  @input="updateAssignment(assignment.localKey, 'cantidad', Number($event.target.value))"
                />
              </div>

              <div class="col-6 col-lg-3">
                <label class="form-label fw-semibold small text-uppercase mb-1">Nota</label>
                <input
                  class="form-control admin-control"
                  type="text"
                  :value="assignment.nota || ''"
                  @input="updateAssignment(assignment.localKey, 'nota', $event.target.value)"
                />
              </div>

              <div class="col-12 col-lg-2">
                <button
                  class="btn btn-outline-danger w-100"
                  type="button"
                  @click="emit('remove-assignment', user.localKey, assignment.localKey)"
                >
                  Quitar
                </button>
              </div>
            </div>
          </article>
        </div>

        <p v-else class="text-muted small mb-0 mt-3">Sin tickets asignados en el borrador actual.</p>
      </div>
    </transition>
  </article>
</template>
