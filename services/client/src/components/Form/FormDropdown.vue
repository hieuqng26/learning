<template>
  <div>
    <label
      v-if="label"
      :for="id"
      class="block mb-2 font-medium"
      :class="{ required: required }"
    >
      {{ label }}
    </label>
    <Dropdown
      :id="id"
      v-model="internalValue"
      :options="options"
      :optionLabel="optionLabel"
      :optionValue="optionValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :invalid="hasError"
      :filter="filter"
      :filterPlaceholder="filterPlaceholder"
      :editable="editable"
      :appendTo="'self'"
      class="w-full"
      @blur="handleBlur"
    />
    <small v-if="hasError" class="p-error block mt-1">{{ errorMessage }}</small>
    <small
      v-else-if="helpText"
      class="text-color-secondary block mt-1 text-sm"
      >{{ helpText }}</small
    >
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number, Object],
    default: null
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Select an option'
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  options: {
    type: Array,
    required: true
  },
  optionLabel: {
    type: String,
    default: 'label'
  },
  optionValue: {
    type: String,
    default: 'value'
  },
  filter: {
    type: Boolean,
    default: false
  },
  filterPlaceholder: {
    type: String,
    default: 'Search...'
  },
  editable: {
    type: Boolean,
    default: false
  },
  helpText: {
    type: String,
    default: ''
  },
  validators: {
    type: Array,
    default: () => []
  },
  formData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'blur'])

const id = ref(`form-dropdown-${Math.random().toString(36).substring(2, 11)}`)
const errorMessage = ref('')
const touched = ref(false)
const internalValue = ref(props.modelValue)
const isSyncing = ref(false)

// Sync internal value with prop
watch(
  () => props.modelValue,
  (newValue) => {
    if (internalValue.value !== newValue) {
      isSyncing.value = true
      internalValue.value = newValue
      nextTick(() => {
        isSyncing.value = false
      })
    }
  },
  { immediate: true }
)

// Emit changes from internal value (only when user selects, not when syncing from prop)
watch(internalValue, (newValue) => {
  if (!isSyncing.value) {
    emit('update:modelValue', newValue)
    validate()
  }
})

const hasError = computed(() => {
  return touched.value && errorMessage.value !== ''
})

const validate = () => {
  errorMessage.value = ''

  if (
    props.required &&
    (internalValue.value === null ||
      internalValue.value === undefined ||
      internalValue.value === '')
  ) {
    errorMessage.value = 'This field is required'
    return false
  }

  for (const validator of props.validators) {
    const result = validator(internalValue.value, props.formData)
    if (result !== true) {
      errorMessage.value = result
      return false
    }
  }

  return true
}

const handleBlur = () => {
  touched.value = true
  validate()
  emit('blur')
}

defineExpose({
  validate
})
</script>

<style scoped>
.required::after {
  content: ' *';
  color: var(--red-500);
}

.p-error {
  color: var(--red-500);
  font-size: 0.875rem;
}
</style>
