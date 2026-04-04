<script setup>
const props = defineProps({
  field: {
    type: Object,
    required: true,
  },
  modelValue: {
    type: [String, Number, Boolean, null],
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

function onInput(event) {
  const { type, value, checked } = event.target

  if (type === 'checkbox') {
    emit('update:modelValue', checked)
    return
  }

  if (props.field.type === 'number') {
    emit('update:modelValue', value === '' ? '' : Number(value))
    return
  }

  emit('update:modelValue', value)
}
</script>

<template>
  <div class="admin-field" :class="{ 'admin-field-switch': field.type === 'switch' }">
    <label class="form-label fw-semibold small text-uppercase mb-2">{{ field.label }}</label>

    <textarea
      v-if="field.type === 'textarea'"
      class="form-control admin-control"
      :rows="field.rows || 3"
      :value="modelValue ?? ''"
      :placeholder="field.placeholder || ''"
      :disabled="disabled"
      @input="onInput"
    />

    <input
      v-else-if="field.type !== 'switch'"
      class="form-control admin-control"
      :type="field.type"
      :value="modelValue ?? ''"
      :required="field.required"
      :placeholder="field.placeholder || ''"
      :min="field.min"
      :max="field.max"
      :step="field.step"
      :disabled="disabled"
      @input="onInput"
    />

    <div v-else class="form-check form-switch">
      <input
        class="form-check-input"
        type="checkbox"
        :checked="Boolean(modelValue)"
        :disabled="disabled"
        @change="onInput"
      />
    </div>
  </div>
</template>
