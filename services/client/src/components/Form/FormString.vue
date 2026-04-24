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
    <InputText
      :id="id"
      v-model="internalValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :maxlength="maxLength"
      :invalid="hasError"
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
    type: String,
    default: ''
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
  maxLength: {
    type: Number,
    default: null
  },
  minLength: {
    type: Number,
    default: null
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

const id = ref(`form-string-${Math.random().toString(36).substring(2, 11)}`)
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

// Emit changes from internal value (only when user types, not when syncing from prop)
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
    (!internalValue.value || internalValue.value.trim() === '')
  ) {
    errorMessage.value = 'This field is required'
    return false
  }

  if (props.minLength && internalValue.value.length < props.minLength) {
    errorMessage.value = `Minimum length is ${props.minLength} characters`
    return false
  }

  if (props.maxLength && internalValue.value.length > props.maxLength) {
    errorMessage.value = `Maximum length is ${props.maxLength} characters`
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
