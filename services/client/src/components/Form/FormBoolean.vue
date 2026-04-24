<template>
  <div>
    <div class="flex align-items-center gap-2">
      <Checkbox
        :id="id"
        v-model="internalValue"
        :disabled="disabled"
        :invalid="hasError"
        @blur="handleBlur"
        :binary="true"
      />
      <label
        v-if="label"
        :for="id"
        class="font-medium cursor-pointer"
        :class="{ required: required }"
      >
        {{ label }}
      </label>
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
    type: Boolean,
    default: false,
    validator(value) {
      if (typeof value !== 'boolean') {
        console.error(
          `FormBoolean received invalid modelValue:`,
          value,
          typeof value
        )
        return false
      }
      return true
    }
  },
  label: {
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

const id = ref(`form-boolean-${Math.random().toString(36).substring(2, 11)}`)
const errorMessage = ref('')
const touched = ref(false)
// Ensure we always have a boolean value
const internalValue = ref(
  typeof props.modelValue === 'boolean' ? props.modelValue : false
)
const isSyncing = ref(false)

// Sync internal value with prop
watch(
  () => props.modelValue,
  (newValue) => {
    // Ensure we only accept boolean values
    const booleanValue = typeof newValue === 'boolean' ? newValue : false
    if (internalValue.value !== booleanValue) {
      isSyncing.value = true
      internalValue.value = booleanValue
      nextTick(() => {
        isSyncing.value = false
      })
    }
  },
  { immediate: true }
)

// Emit changes from internal value (only when user clicks, not when syncing from prop)
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

  if (props.required && !internalValue.value) {
    errorMessage.value = 'This field must be checked'
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
