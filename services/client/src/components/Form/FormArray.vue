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

    <div class="flex flex-column gap-3">
      <div class="flex flex-column gap-1">
        <div class="flex gap-2 align-items-start">
          <InputText
            :id="id"
            v-model="newItemValue"
            :placeholder="getPlaceholder()"
            :disabled="disabled"
            :invalid="hasInputError"
            class="flex-1"
            @keyup.enter="addItem"
            @blur="validateInput"
          />
          <Button
            type="button"
            label="Add"
            icon="pi pi-plus"
            :disabled="disabled || !canAddItem"
            @click="addItem"
            class="flex-shrink-0"
            size="small"
          />
        </div>
        <small v-if="hasInputError" class="p-error">{{
          inputErrorMessage
        }}</small>
      </div>

      <div v-if="internalValue.length > 0">
        <div class="chips-container">
          <div
            v-for="(item, index) in internalValue"
            :key="index"
            class="array-chip"
          >
            <span class="chip-content">{{ formatDisplayValue(item) }}</span>
            <Button
              type="button"
              icon="pi pi-times"
              :disabled="disabled"
              @click="removeItem(index)"
              class="remove-button"
              text
              rounded
              size="small"
            />
          </div>
        </div>
      </div>

      <!-- <div
        v-if="showJsonPreview && internalValue.length > 0"
        class="json-preview"
      >
        <small class="preview-label">Preview:</small>
        <code class="json-code">{{ jsonPreview }}</code>
      </div> -->
    </div>

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
    type: [Array, String],
    default: () => []
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  arrayType: {
    type: String,
    default: 'string', // 'string' or 'number'
    validator: (value) => ['string', 'number'].includes(value)
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
  },
  showJsonPreview: {
    type: Boolean,
    default: true
  },
  min: {
    type: Number,
    default: null
  },
  max: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'blur'])

const id = ref(`form-array-${Math.random().toString(36).substring(2, 11)}`)
const errorMessage = ref('')
const inputErrorMessage = ref('')
const touched = ref(false)
const newItemValue = ref('')

// Convert modelValue to array if it's a string
const getArrayFromValue = (value) => {
  if (Array.isArray(value)) {
    return [...value]
  }
  if (typeof value === 'string') {
    if (value.trim() === '') {
      return []
    }
    try {
      const parsed = JSON.parse(value)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
}

const internalValue = ref(getArrayFromValue(props.modelValue))
const isSyncing = ref(false)

// Helper function to compare arrays
const arraysEqual = (a, b) => {
  if (a.length !== b.length) return false
  return a.every((val, index) => val === b[index])
}

// Sync internal value with prop
watch(
  () => props.modelValue,
  (newValue) => {
    const arrayValue = getArrayFromValue(newValue)
    if (!arraysEqual(internalValue.value, arrayValue)) {
      isSyncing.value = true
      internalValue.value = arrayValue
      nextTick(() => {
        isSyncing.value = false
      })
    }
  },
  { immediate: true, deep: true }
)

// Emit changes from internal value
watch(
  internalValue,
  (newValue) => {
    if (!isSyncing.value) {
      emit('update:modelValue', [...newValue])
      validate()
    }
  },
  { deep: true }
)

const hasError = computed(() => {
  return touched.value && errorMessage.value !== ''
})

const hasInputError = computed(() => {
  return inputErrorMessage.value !== ''
})

const canAddItem = computed(() => {
  return newItemValue.value.trim() !== '' && !hasInputError.value
})

const jsonPreview = computed(() => {
  return JSON.stringify(internalValue.value)
})

const getPlaceholder = () => {
  if (props.placeholder) return props.placeholder
  return props.arrayType === 'number'
    ? 'Enter number(s), e.g., 100000 or 100000,200000,300000'
    : 'Enter text, e.g., 2Y or 2Y,3Y,5Y'
}

const formatDisplayValue = (value) => {
  return props.arrayType === 'number' ? value.toString() : value
}

const parseValue = (stringValue) => {
  const trimmed = stringValue.trim()
  if (props.arrayType === 'number') {
    const parsed = parseFloat(trimmed)
    if (isNaN(parsed)) {
      throw new Error('Must be a valid number')
    }
    return parsed
  }
  return trimmed
}

const parseCommaSeparatedValues = (stringValue) => {
  const trimmed = stringValue.trim()
  if (!trimmed.includes(',')) {
    return [parseValue(trimmed)]
  }

  // Split by comma and parse each value
  const values = trimmed
    .split(',')
    .map((val) => val.trim())
    .filter((val) => val !== '')
  const parsedValues = []

  for (const val of values) {
    try {
      const parsed = parseValue(val)
      // Check for duplicates (including existing values in array)
      if (
        !internalValue.value.includes(parsed) &&
        !parsedValues.includes(parsed)
      ) {
        parsedValues.push(parsed)
      }
    } catch (error) {
      throw new Error(`Invalid value "${val}": ${error.message}`)
    }
  }

  if (parsedValues.length === 0) {
    throw new Error('No valid values found')
  }

  return parsedValues
}

const validateInput = () => {
  inputErrorMessage.value = ''
  const trimmed = newItemValue.value.trim()

  if (trimmed === '') return true

  try {
    const parsedValues = parseCommaSeparatedValues(trimmed)

    // Check numeric constraints for all values
    if (props.arrayType === 'number') {
      for (const parsed of parsedValues) {
        if (props.min !== null && parsed < props.min) {
          inputErrorMessage.value = `Value ${parsed} must be at least ${props.min}`
          return false
        }
        if (props.max !== null && parsed > props.max) {
          inputErrorMessage.value = `Value ${parsed} must be at most ${props.max}`
          return false
        }
      }
    }

    return true
  } catch (error) {
    inputErrorMessage.value = error.message
    return false
  }
}

const addItem = () => {
  if (!validateInput() || !canAddItem.value) return

  try {
    const parsedValues = parseCommaSeparatedValues(newItemValue.value)
    internalValue.value.push(...parsedValues)
    newItemValue.value = ''
    inputErrorMessage.value = ''
  } catch (error) {
    inputErrorMessage.value = error.message
  }
}

const removeItem = (index) => {
  internalValue.value.splice(index, 1)
}

const validate = () => {
  errorMessage.value = ''

  if (props.required && internalValue.value.length === 0) {
    errorMessage.value = 'This field is required'
    return false
  }

  // Run custom validators
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

.chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid var(--surface-border);
  border-radius: var(--border-radius);
  background: var(--surface-0);
  min-height: 2.5rem;
  align-items: flex-start;
  align-content: flex-start;
}

.array-chip {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: var(--primary-color);
  color: var(--primary-color-text);
  padding: 0.25rem 0.5rem;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  white-space: nowrap;
}

.chip-content {
  font-weight: 500;
}

.remove-button {
  padding: 0.125rem;
  width: 1.25rem;
  height: 1.25rem;
  color: var(--primary-color-text);
}

.remove-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.json-preview {
  padding: 0.5rem;
  background: var(--surface-100);
  border-radius: var(--border-radius);
  border: 1px solid var(--surface-border);
}

.preview-label {
  font-weight: 500;
  color: var(--text-color-secondary);
  display: block;
  margin-bottom: 0.25rem;
}

.json-code {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: var(--text-color);
  background: none;
  word-break: break-all;
}

.p-error {
  color: var(--red-500);
  font-size: 0.875rem;
}
</style>
