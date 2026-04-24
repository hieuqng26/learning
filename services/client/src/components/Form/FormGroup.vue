<template>
  <div v-if="asPanel">
    <Panel
      :header="title"
      :toggleable="collapsible"
      :collapsed="initiallyCollapsed"
      class="form-group-panel"
    >
      <div class="form-group-content">
        <slot name="fields" :formData="formData">
          <!-- Dynamic field rendering -->
          <template v-for="field in visibleFields" :key="field.key">
            <component
              :is="getFieldComponent(field.type)"
              :ref="(el) => setFieldRef(field.key, el)"
              :modelValue="getFieldValue(field.key)"
              @update:modelValue="(val) => setFieldValue(field.key, val)"
              v-bind="getFieldProps(field)"
              :formData="modelValue"
            />
          </template>
        </slot>

        <!-- Custom slot content -->
        <slot :formData="formData"></slot>
      </div>
    </Panel>
  </div>
  <div v-else class="form-group-content">
    <slot name="fields" :formData="formData">
      <!-- Dynamic field rendering -->
      <template v-for="field in visibleFields" :key="field.key">
        <component
          :is="getFieldComponent(field.type)"
          :ref="(el) => setFieldRef(field.key, el)"
          :modelValue="getFieldValue(field.key)"
          @update:modelValue="(val) => setFieldValue(field.key, val)"
          v-bind="getFieldProps(field)"
          :formData="modelValue"
        />
      </template>
    </slot>

    <!-- Custom slot content -->
    <slot :formData="formData"></slot>
  </div>
</template>

<script setup>
import { ref, computed, watch, provide, nextTick } from 'vue'
import FormNumber from './FormNumber.vue'
import FormFloat from './FormFloat.vue'
import FormString from './FormString.vue'
import FormDate from './FormDate.vue'
import FormBoolean from './FormBoolean.vue'
import FormDropdown from './FormDropdown.vue'
import FormMultiSelect from './FormMultiSelect.vue'
import FormArray from './FormArray.vue'
import SensitivityConfig from './SensitivityConfig.vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  fields: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: Object,
    default: () => ({})
  },
  collapsible: {
    type: Boolean,
    default: true
  },
  initiallyCollapsed: {
    type: Boolean,
    default: false
  },
  validators: {
    type: Array,
    default: () => []
  },
  asPanel: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'validate'])

// Helper to get nested value from object using dot/bracket notation
const getNestedValue = (obj, path) => {
  const keys = path.replace(/\[(\d+)\]/g, '.$1').split('.')
  let current = obj
  for (const key of keys) {
    if (current == null) return undefined
    current = current[key]
  }
  return current
}

// Helper to set nested value in object using dot/bracket notation
const setNestedValue = (obj, path, value) => {
  const keys = path.replace(/\[(\d+)\]/g, '.$1').split('.')
  let current = obj
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i]
    if (!current[key]) {
      current[key] = /^\d+$/.test(keys[i + 1]) ? [] : {}
    }
    current = current[key]
  }
  current[keys[keys.length - 1]] = value
}

const getDefaultValue = (field) => {
  // Use field-specific default value if provided
  if (field.defaultValue !== undefined) {
    return field.defaultValue
  }

  // Otherwise use type-based defaults
  switch (field.type) {
    case 'number':
    case 'float':
      return null
    case 'boolean':
      return false
    case 'date':
      return null
    case 'multiselect':
    case 'array':
      return []
    default:
      return ''
  }
}

// Deep clone that preserves Date objects (for initialization)
const deepCloneInit = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (Array.isArray(obj)) return obj.map((item) => deepCloneInit(item))

  const cloned = {}
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      cloned[key] = deepCloneInit(obj[key])
    }
  }
  return cloned
}

// Initialize form data with proper defaults for all fields
const initializeFormData = (modelValue) => {
  const data = deepCloneInit(modelValue || {})
  // Ensure all fields have proper default values
  props.fields.forEach((field) => {
    const existingValue = getNestedValue(data, field.key)
    if (existingValue === undefined) {
      setNestedValue(data, field.key, getDefaultValue(field))
    } else {
      // Fix type mismatches - convert string to array for array fields
      if (field.type === 'array' && typeof existingValue === 'string') {
        setNestedValue(data, field.key, getDefaultValue(field))
      }
    }
  })
  return data
}

const formData = ref(initializeFormData(props.modelValue))
const fieldRefs = ref({})
const isSyncing = ref(false)

// Computed property for visible fields (handles showWhen)
const visibleFields = computed(() => {
  return props.fields.filter((field) => {
    if (!field.showWhen) return true
    return field.showWhen(props.modelValue)
  })
})

// Get field value using nested path
const getFieldValue = (key) => {
  return getNestedValue(props.modelValue, key)
}

// Set field value using nested path and emit update
const setFieldValue = (key, value) => {
  const newData = deepCloneInit(props.modelValue)
  setNestedValue(newData, key, value)
  emit('update:modelValue', newData)
}

// Sync form data with prop changes
watch(
  () => props.modelValue,
  (newValue) => {
    isSyncing.value = true
    formData.value = initializeFormData(newValue)
    nextTick(() => {
      isSyncing.value = false
    })
  },
  { deep: true }
)

// Emit form data changes (only when fields change, not when syncing from prop)
watch(
  formData,
  (newValue) => {
    if (!isSyncing.value) {
      emit('update:modelValue', newValue)
    }
  },
  { deep: true }
)

// Component mapping for dynamic rendering
const componentMap = {
  number: FormNumber,
  float: FormFloat,
  string: FormString,
  text: FormString,
  date: FormDate,
  boolean: FormBoolean,
  dropdown: FormDropdown,
  multiselect: FormMultiSelect,
  array: FormArray,
  sensitivity: SensitivityConfig
}

const getFieldComponent = (type) => {
  return componentMap[type] || FormString
}

const getFieldProps = (field) => {
  const { key, type, ...props } = field
  return props
}

const setFieldRef = (fieldKey, ref) => {
  if (ref) {
    fieldRefs.value[fieldKey] = ref
  }
}

// Validation methods
const validate = async () => {
  let isValid = true
  const errors = []

  // Validate individual fields
  for (const field of props.fields) {
    const fieldRef = fieldRefs.value[field.key]
    if (fieldRef && typeof fieldRef.validate === 'function') {
      const fieldValid = fieldRef.validate()
      if (!fieldValid) {
        isValid = false
        errors.push(`${field.label || field.key} is invalid`)
      }
    }
  }

  // Run group-level validators
  for (const validator of props.validators) {
    const result = validator(formData.value)
    if (result !== true) {
      isValid = false
      errors.push(result)
    }
  }

  emit('validate', { isValid, errors })
  return isValid
}

const getFormData = () => {
  return { ...formData.value }
}

const resetForm = () => {
  // Reset each field to its default value
  props.fields.forEach((field) => {
    const defaultValue = getDefaultValue(field)
    formData.value[field.key] = defaultValue
  })
}

// Provide form context for nested components
provide('formGroup', {
  formData,
  validate,
  getFormData
})

// Expose methods to parent components
defineExpose({
  validate,
  getFormData,
  resetForm
})
</script>

<style scoped>
.form-group-panel {
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
}

.form-group-panel :deep(.p-panel-header) {
  background: var(--surface-100);
  border-bottom: 1px solid var(--surface-border);
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--text-color);
}

.form-group-panel :deep(.p-panel-content) {
  padding: 1.5rem;
  background: var(--surface-0);
}

.form-group-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Responsive design */
@media (min-width: 768px) {
  .form-group-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    align-items: start;
  }
}

/* Override panel styles for better integration */
.form-group-panel :deep(.p-panel-header-icon) {
  color: var(--primary-color);
}

.form-group-panel :deep(.p-panel-toggler) {
  border: none;
  background: transparent;
}

.form-group-panel :deep(.p-panel-toggler:hover) {
  background: var(--surface-200);
}

/* Animation for collapsible panels */
.form-group-panel :deep(.p-toggleable-content) {
  overflow: hidden;
  transition: max-height 0.3s ease;
}
</style>
