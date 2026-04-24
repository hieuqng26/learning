<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
import {
  productCategories,
  getProductsByCategory,
  getProductForm
} from '@/forms'
import {
  transformSensitivityData,
  validateSensitivityConfig
} from '@/forms/shared/sensitivity-fields'
import FormNumber from '@/components/Form/FormNumber.vue'
import FormFloat from '@/components/Form/FormFloat.vue'
import FormString from '@/components/Form/FormString.vue'
import FormDate from '@/components/Form/FormDate.vue'
import FormBoolean from '@/components/Form/FormBoolean.vue'
import FormDropdown from '@/components/Form/FormDropdown.vue'
import FormMultiSelect from '@/components/Form/FormMultiSelect.vue'
import FormGroup from '@/components/Form/FormGroup.vue'
import LineChart from '@/components/Charts/LineChart.vue'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import FileUpload from 'primevue/fileupload'
import Message from 'primevue/message'
import Panel from 'primevue/panel'

// Define props
const props = defineProps({
  module: String,
  submodule: {
    type: String,
    required: false
  }
})

// Services
const store = useStore()
const toast = useToast()

// Component state
const selectedCategory = ref(null)
const selectedProduct = ref(null)
const formData = ref({})
const result = ref(null)
const isLoading = ref(false)
const formRefs = ref([])
const groupRefs = ref([])

// Computed properties
const availableProducts = computed(() => {
  if (!selectedCategory.value) return []
  return getProductsByCategory(selectedCategory.value)
})

const currentForm = computed(() => {
  if (!selectedCategory.value || !selectedProduct.value) return null
  return getProductForm(selectedCategory.value, selectedProduct.value)
})

const productOptions = computed(() => {
  return availableProducts.value.map((product) => ({
    label: product.name,
    value: product.name
  }))
})

// Separate trade detail groups from sensitivity groups
const tradeDetailGroups = computed(() => {
  if (!currentForm.value?.groups) return []
  return currentForm.value.groups.filter(
    (group) => group.title !== 'Stress Configuration'
  )
})

const sensitivityGroups = computed(() => {
  if (!currentForm.value?.groups) return []
  return currentForm.value.groups.filter(
    (group) => group.title === 'Stress Configuration'
  )
})

const formattedNPV = computed(() => {
  if (!result.value?.base?.npv) return null
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(result.value.base.npv)
})

const formattedCVA = computed(() => {
  if (!result.value?.base?.cva) return null
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(result.value.base.cva)
})

const formattedDVA = computed(() => {
  if (!result.value?.base?.dva) return null
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(result.value.base.dva)
})

// Exposure chart configuration
const selectedMetricColumns = ref([])
const exposureStartDate = ref(null)
const exposureEndDate = ref(null)

// Stress testing / scenario configuration
const scenarioConfigFile = ref(null)
const scenarioConfigData = ref(null)
const scenarioConfigError = ref(null)

// Exposure type selection (Base, Sensitivity, Stress)
const selectedExposureType = ref('base')
const selectedExposureTypeIndex = ref(0) // For TabView

// Get current exposure data based on selected type (always use 'trade' for single product)
const currentExposureData = computed(() => {
  if (!result.value) return null

  const exposureType = selectedExposureType.value

  // Get the appropriate exposure object
  const exposureObj = result.value[exposureType]?.exposures
  if (!exposureObj) return null

  // Get the JSON string for trade level (single product always uses trade)
  const exposureJson = exposureObj['trade']
  if (!exposureJson) return null

  try {
    return JSON.parse(exposureJson)
  } catch (e) {
    console.error('Failed to parse exposure data:', e)
    return null
  }
})

// Check if scenario config is loaded and valid
const hasFullyParsedScenarioData = computed(() => {
  return (
    scenarioConfigData.value &&
    scenarioConfigData.value.scenarios &&
    Array.isArray(scenarioConfigData.value.scenarios) &&
    scenarioConfigData.value.scenarios.length > 0
  )
})

// Available metric columns based on analysis type
const availableMetricColumns = computed(() => {
  if (!currentExposureData.value?.length) return []

  const exposureType = selectedExposureType.value
  const firstRow = currentExposureData.value[0]

  // For base: Create EE columns (EPE + ENE)
  if (exposureType === 'base') {
    const epeColumns = Object.keys(firstRow).filter((key) =>
      key.startsWith('EPE')
    )

    return epeColumns.map((epeCol) => {
      const suffix = epeCol.replace('EPE', '')
      return {
        label: `EE${suffix}`,
        value: `EE${suffix}`,
        epeColumn: epeCol,
        eneColumn: `ENE${suffix}`
      }
    })
  }

  // For sensitivity: Group by Type|Factor_1
  if (exposureType === 'sensitivity') {
    const uniqueCombos = new Set()
    currentExposureData.value.forEach((row) => {
      if (row.Type && row.Factor_1) {
        uniqueCombos.add(`${row.Type}|${row.Factor_1}`)
      }
    })

    return Array.from(uniqueCombos)
      .sort()
      .map((combo) => {
        const [type, factor] = combo.split('|')
        return {
          label: `EE - ${factor} (${type})`,
          value: combo
        }
      })
  }

  // For stress: Group by Scenario
  if (exposureType === 'stress') {
    const uniqueScenarios = [
      ...new Set(currentExposureData.value.map((row) => row.Scenario))
    ]
      .filter((s) => s)
      .sort()

    return uniqueScenarios.map((scenario) => ({
      label: `EE - ${scenario}`,
      value: scenario
    }))
  }

  return []
})

// Helper: Get line style for chart datasets
const getLineStyle = (index) => {
  // Professional color palette for financial charts
  const colors = [
    '#1f77b4', // Blue
    '#ff7f0e', // Orange
    '#2ca02c', // Green
    '#d62728', // Red
    '#9467bd', // Purple
    '#8c564b', // Brown
    '#e377c2', // Pink
    '#7f7f7f', // Gray
    '#bcbd22', // Olive
    '#17becf' // Cyan
  ]
  const color = colors[index % colors.length]

  return {
    borderColor: color,
    backgroundColor: 'transparent',
    borderWidth: 2.5,
    fill: false,
    tension: 0.1,
    pointRadius: 0,
    pointHoverRadius: 4
  }
}

// Helper: Filter data by date range
const filterByDateRange = (exposures) => {
  const startDate = exposureStartDate.value
  const endDate = exposureEndDate.value

  if (!startDate && !endDate) return exposures

  return exposures.filter((row) => {
    const rowDate = new Date(row.Date)
    if (startDate && rowDate < startDate) return false
    if (endDate && rowDate > endDate) return false
    return true
  })
}

// Helper: Build chart data for base exposures (EE = EPE + ENE)
const buildBaseExposureChart = () => {
  let exposures = currentExposureData.value
  if (!exposures || exposures.length === 0) return null

  // Set default date range if not set
  if (exposureStartDate.value === null && exposureEndDate.value === null) {
    const dates = exposures.map((row) => new Date(row.Date))
    exposureStartDate.value = new Date(Math.min(...dates))
    exposureEndDate.value = new Date(Math.max(...dates))
  }

  // Apply date filtering
  exposures = filterByDateRange(exposures)
  if (exposures.length === 0) return null

  // Use selected columns
  const metricColumns = selectedMetricColumns.value
  if (metricColumns.length === 0) return null

  // Create datasets for EE (EPE + ENE)
  const datasets = metricColumns.map((columnConfig, index) => {
    const eeData = exposures.map((exp) => {
      const epe = exp[columnConfig.epeColumn] || 0
      const ene = exp[columnConfig.eneColumn] || 0
      return epe + ene
    })

    return {
      label: columnConfig.label,
      data: eeData,
      ...getLineStyle(index)
    }
  })

  return {
    labels: exposures.map((exp) => exp.Date),
    datasets: datasets
  }
}

// Helper: Build chart data for sensitivity exposures
const buildSensitivityExposureChart = () => {
  let data = currentExposureData.value
  if (!data || data.length === 0) return null

  // Apply date filtering
  data = filterByDateRange(data)
  if (data.length === 0) return null

  // Use selected factor/type combinations
  const selectedCombos = selectedMetricColumns.value
  if (selectedCombos.length === 0) return null

  // Group data by date
  const dateMap = new Map()
  data.forEach((row) => {
    const date = row.Date
    if (!dateMap.has(date)) {
      dateMap.set(date, [])
    }
    dateMap.get(date).push(row)
  })

  // Sort dates
  const sortedDates = Array.from(dateMap.keys()).sort()

  // Set default date range if not set
  if (exposureStartDate.value === null && exposureEndDate.value === null) {
    const dates = sortedDates.map((d) => new Date(d))
    exposureStartDate.value = new Date(Math.min(...dates))
    exposureEndDate.value = new Date(Math.max(...dates))
  }

  // Create one dataset per selected combo
  const datasets = selectedCombos.map((comboConfig, index) => {
    const [type, factor] = comboConfig.value.split('|')

    const dataPoints = sortedDates.map((date) => {
      const rows = dateMap.get(date)
      const matchingRow = rows.find(
        (r) => r.Type === type && r.Factor_1 === factor
      )
      if (!matchingRow) return null

      const epe = matchingRow.EPE || 0
      const ene = matchingRow.ENE || 0
      return epe + ene
    })

    return {
      label: comboConfig.label,
      data: dataPoints,
      ...getLineStyle(index)
    }
  })

  return {
    labels: sortedDates,
    datasets: datasets
  }
}

// Helper: Build chart data for stress exposures
const buildStressExposureChart = () => {
  let data = currentExposureData.value
  if (!data || data.length === 0) return null

  // Apply date filtering
  data = filterByDateRange(data)
  if (data.length === 0) return null

  // Use selected scenarios
  const selectedScenarios = selectedMetricColumns.value
  if (selectedScenarios.length === 0) return null

  // Group data by date
  const dateMap = new Map()
  data.forEach((row) => {
    const date = row.Date
    if (!dateMap.has(date)) {
      dateMap.set(date, [])
    }
    dateMap.get(date).push(row)
  })

  // Sort dates
  const sortedDates = Array.from(dateMap.keys()).sort()

  // Set default date range if not set
  if (exposureStartDate.value === null && exposureEndDate.value === null) {
    const dates = sortedDates.map((d) => new Date(d))
    exposureStartDate.value = new Date(Math.min(...dates))
    exposureEndDate.value = new Date(Math.max(...dates))
  }

  // Create one dataset per scenario
  const datasets = selectedScenarios.map((scenarioConfig, index) => {
    const scenario = scenarioConfig.value

    const dataPoints = sortedDates.map((date) => {
      const rows = dateMap.get(date)
      const matchingRow = rows.find((r) => r.Scenario === scenario)
      if (!matchingRow) return null

      const epe = matchingRow.EPE || 0
      const ene = matchingRow.ENE || 0
      return epe + ene
    })

    return {
      label: scenarioConfig.label,
      data: dataPoints,
      ...getLineStyle(index)
    }
  })

  return {
    labels: sortedDates,
    datasets: datasets
  }
}

const exposureChartData = computed(() => {
  if (!currentExposureData.value || currentExposureData.value.length === 0) {
    return null
  }

  const exposureType = selectedExposureType.value

  // Base exposures: use existing logic
  if (exposureType === 'base') {
    return buildBaseExposureChart()
  }

  // Sensitivity exposures: one line per factor/type combo
  if (exposureType === 'sensitivity') {
    return buildSensitivityExposureChart()
  }

  // Stress exposures: one line per scenario
  if (exposureType === 'stress') {
    return buildStressExposureChart()
  }

  return null
})

// Watchers
watch(selectedCategory, (newCategory) => {
  selectedProduct.value = null
  formData.value = {}
  result.value = null
})

watch(selectedProduct, (newProduct) => {
  formData.value = {}
  result.value = null
  clearScenarioConfig()
  initializeFormData()
})

// Reset date range and selected columns when results change
watch(
  () => result.value?.base?.exposures,
  () => {
    exposureStartDate.value = null
    exposureEndDate.value = null
    selectedMetricColumns.value = []
    selectedExposureType.value = 'base'
    selectedExposureTypeIndex.value = 0
  }
)

// Reset selections when exposure type changes
watch(selectedExposureType, () => {
  selectedMetricColumns.value = []
  exposureStartDate.value = null
  exposureEndDate.value = null

  // Auto-select first column if available
  if (availableMetricColumns.value.length > 0) {
    selectedMetricColumns.value = [availableMetricColumns.value[0]]
  }
})

// Sync tab index with exposure type
watch(selectedExposureTypeIndex, (newIndex) => {
  const types = ['base', 'sensitivity', 'stress']
  selectedExposureType.value = types[newIndex]
})

// Auto-select first column when available columns change
watch(availableMetricColumns, (newColumns) => {
  if (newColumns.length > 0 && selectedMetricColumns.value.length === 0) {
    // Auto-select the first column
    selectedMetricColumns.value = [newColumns[0]]
  }
})

// Helper to set nested value in object using dot/bracket notation
const setNestedValue = (obj, path, value) => {
  const keys = path.replace(/\[(\d+)\]/g, '.$1').split('.')
  let current = obj
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i]
    if (!current[key]) {
      // Create array if next key is numeric
      current[key] = /^\d+$/.test(keys[i + 1]) ? [] : {}
    }
    current = current[key]
  }
  current[keys[keys.length - 1]] = value
}

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

// Methods
const initializeFormData = () => {
  if (!currentForm.value) return

  const data = {}

  // Handle grouped forms
  if (currentForm.value.groups) {
    currentForm.value.groups.forEach((group) => {
      group.fields.forEach((field) => {
        setNestedValue(data, field.key, getDefaultFieldValue(field))
      })
    })
  }
  // Handle flat field forms (backward compatibility)
  else if (currentForm.value.fields) {
    currentForm.value.fields.forEach((field) => {
      setNestedValue(data, field.key, getDefaultFieldValue(field))
    })
  }

  formData.value = data
}

const getDefaultFieldValue = (field) => {
  // Use field-specific default value if provided
  if (field.defaultValue !== undefined) {
    return field.defaultValue
  }

  // Otherwise use type-based defaults
  switch (field.type) {
    case 'boolean':
      return false
    case 'number':
    case 'float':
      return null
    case 'date':
      return null
    case 'multiselect':
    case 'array':
      return []
    default:
      return ''
  }
}

// Timezone-safe date formatting function
const formatDateForAPI = (date) => {
  if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
    return null
  }

  // Use local date components to avoid timezone offset issues
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0') // getMonth() is 0-indexed
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

const validateForm = () => {
  let isValid = true

  // Validate individual form fields (for flat forms)
  formRefs.value.forEach((ref) => {
    if (ref && ref.validate && !ref.validate()) {
      isValid = false
    }
  })

  // Validate grouped forms
  groupRefs.value.forEach((ref) => {
    if (ref && ref.validate && !ref.validate()) {
      isValid = false
    }
  })

  return isValid
}

// Scenario config file upload handlers
const onScenarioConfigSelect = async (event) => {
  const file = event.files[0]
  if (!file) return

  scenarioConfigFile.value = file
  scenarioConfigError.value = null
  scenarioConfigData.value = null

  try {
    const fileExt = file.name.split('.').pop().toLowerCase()

    if (fileExt === 'json') {
      // Parse JSON directly in frontend
      const fileContent = await readFileContent(file)
      scenarioConfigData.value = JSON.parse(fileContent)

      // Validate JSON structure
      validateScenarioConfig(scenarioConfigData.value)
    } else if (fileExt === 'xlsx') {
      // For Excel, upload immediately to backend for parsing
      const formData = new FormData()
      formData.append('file', file)

      toast.add({
        severity: 'info',
        summary: 'Uploading',
        detail: 'Parsing Excel file...',
        life: 2000
      })

      const uploadResponse = await store.dispatch('uploadScenarioConfig', {
        formData
      })

      scenarioConfigData.value = uploadResponse.data

      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: `Loaded ${uploadResponse.data.scenarios?.length || 0} scenario(s)`,
        life: 3000
      })
    } else {
      throw new Error('Unsupported file format. Use .json or .xlsx')
    }
  } catch (error) {
    scenarioConfigError.value = error.message
    scenarioConfigData.value = null

    toast.add({
      severity: 'error',
      summary: 'Upload Error',
      detail: error.message || 'Failed to parse scenario configuration',
      life: 5000
    })
  }
}

const readFileContent = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

const validateScenarioConfig = (config) => {
  if (!config) {
    throw new Error('Config is empty')
  }

  // Validate basic structure
  if (!config.scenarios || !Array.isArray(config.scenarios)) {
    throw new Error('Config must contain "scenarios" array')
  }

  if (config.scenarios.length === 0) {
    throw new Error('At least one scenario is required')
  }

  // Validate each scenario has required fields
  config.scenarios.forEach((scenario, index) => {
    if (!scenario.id) {
      throw new Error(`Scenario ${index + 1} missing "id" field`)
    }
  })
}

const clearScenarioConfig = () => {
  scenarioConfigFile.value = null
  scenarioConfigData.value = null
  scenarioConfigError.value = null
}

const handleSubmit = async () => {
  if (!currentForm.value) {
    toast.add({
      severity: 'warn',
      summary: 'Warning',
      detail: 'Please select a product first',
      life: 3000
    })
    return
  }

  if (!validateForm()) {
    toast.add({
      severity: 'error',
      summary: 'Validation Error',
      detail: 'Please fix the form errors before submitting',
      life: 3000
    })
    return
  }

  // Validate sensitivity configuration
  const sensitivityValidation = validateSensitivityConfig(formData.value)
  if (!sensitivityValidation.valid) {
    toast.add({
      severity: 'error',
      summary: 'Sensitivity Configuration Error',
      detail: sensitivityValidation.errors.join('. '),
      life: 5000
    })
    return
  }

  try {
    isLoading.value = true

    // Prepare data for API call - flatten nested sensitivity data
    const payload = {}
    const allFields = currentForm.value.groups
      ? currentForm.value.groups.flatMap((group) => group.fields)
      : currentForm.value.fields || []

    // Copy non-sensitivity fields
    allFields.forEach((field) => {
      if (field.type === 'sensitivity') {
        // Skip sensitivity field - handled separately
        return
      }
      const value = getNestedValue(formData.value, field.key)
      if (field.type === 'date' && value) {
        payload[field.key] = formatDateForAPI(value)
      } else {
        payload[field.key] = value
      }
    })

    // Transform and add sensitivity config
    const sensitivityConfig = transformSensitivityData(formData.value)
    if (sensitivityConfig) {
      payload.sensitivity = sensitivityConfig
    }

    // Add scenario config if uploaded
    if (scenarioConfigData.value) {
      payload.scenario = scenarioConfigData.value
    }

    toast.add({
      severity: 'info',
      summary: 'Calculation submitted',
      detail: 'Please wait for a few seconds ...',
      life: 3000
    })

    const response = await store.dispatch(currentForm.value.api, {
      data: payload
    })
    result.value = response.data

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Calculation completed successfully',
      life: 3000
    })
  } catch (error) {
    console.error('Calculation error:', error)
    toast.add({
      severity: 'error',
      summary: 'Calculation Error',
      detail:
        error.response?.data?.message || 'An error occurred during calculation',
      life: 5000
    })
  } finally {
    isLoading.value = false
  }
}

const resetForm = () => {
  selectedCategory.value = null
  selectedProduct.value = null
  formData.value = {}
  result.value = null
}
</script>

<template>
  <Card>
    <template #title>
      <div class="flex align-items-center gap-2">
        <i class="pi pi-calculator"></i>
        Single Product Pricing
      </div>
    </template>

    <template #content>
      <!-- Category Selection -->
      <div class="form-section">
        <h4 class="mt-0 mb-3 text-primary font-semibold">Select Product</h4>
        <div class="grid">
          <div class="col-12 md:col-6">
            <FormDropdown
              v-model="selectedCategory"
              label="Category"
              :options="productCategories"
              placeholder="Choose a category..."
              required
            />
          </div>
          <div class="col-12 md:col-6">
            <FormDropdown
              v-model="selectedProduct"
              label="Product"
              :options="productOptions"
              :filter="true"
              placeholder="Choose a product..."
              required
            />
          </div>
        </div>
      </div>

      <!-- Input Tabs -->
      <div v-if="currentForm" class="mt-4">
        <TabView>
          <!-- Tab 1: Trade Details -->
          <TabPanel>
            <template #header>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-file-edit"></i>
                <span>Trade Details</span>
              </div>
            </template>

            <!-- Grouped Form Layout -->
            <div v-if="tradeDetailGroups.length > 0" class="grouped-form">
              <FormGroup
                v-for="(group, groupIndex) in tradeDetailGroups"
                :key="`group-${groupIndex}`"
                :ref="(el) => (groupRefs[groupIndex] = el)"
                :title="group.title"
                :fields="group.fields"
                v-model="formData"
                :collapsible="group.collapsible !== false"
                :initially-collapsed="group.initiallyCollapsed || false"
                :validators="group.validators || []"
              />
            </div>

            <!-- Flat Form Layout (backward compatibility) -->
            <div v-else-if="currentForm.fields" class="form-grid">
              <template
                v-for="(field, index) in currentForm.fields"
                :key="field.key"
              >
                <FormNumber
                  v-if="field.type === 'number'"
                  :ref="(el) => (formRefs[index] = el)"
                  v-model="formData[field.key]"
                  :label="field.label"
                  :placeholder="field.placeholder"
                  :required="field.required"
                  :disabled="field.disabled"
                  :min="field.min"
                  :max="field.max"
                  :help-text="field.helpText"
                  :validators="field.validators || []"
                  :form-data="formData"
                />

                <FormFloat
                  v-else-if="field.type === 'float'"
                  :ref="(el) => (formRefs[index] = el)"
                  v-model="formData[field.key]"
                  :label="field.label"
                  :placeholder="field.placeholder"
                  :required="field.required"
                  :disabled="field.disabled"
                  :min="field.min"
                  :max="field.max"
                  :step="field.step"
                  :min-fraction-digits="field.minFractionDigits"
                  :max-fraction-digits="field.maxFractionDigits"
                  :help-text="field.helpText"
                  :validators="field.validators || []"
                  :form-data="formData"
                />

                <FormString
                  v-else-if="field.type === 'string'"
                  :ref="(el) => (formRefs[index] = el)"
                  v-model="formData[field.key]"
                  :label="field.label"
                  :placeholder="field.placeholder"
                  :required="field.required"
                  :disabled="field.disabled"
                  :max-length="field.maxLength"
                  :min-length="field.minLength"
                  :help-text="field.helpText"
                  :validators="field.validators || []"
                  :form-data="formData"
                />

                <FormDate
                  v-else-if="field.type === 'date'"
                  :ref="(el) => (formRefs[index] = el)"
                  v-model="formData[field.key]"
                  :label="field.label"
                  :placeholder="field.placeholder"
                  :required="field.required"
                  :disabled="field.disabled"
                  :min-date="field.minDate"
                  :max-date="field.maxDate"
                  :date-format="field.dateFormat"
                  :help-text="field.helpText"
                  :validators="field.validators || []"
                  :form-data="formData"
                />

                <FormBoolean
                  v-else-if="field.type === 'boolean'"
                  :ref="(el) => (formRefs[index] = el)"
                  v-model="formData[field.key]"
                  :label="field.label"
                  :required="field.required"
                  :disabled="field.disabled"
                  :help-text="field.helpText"
                  :validators="field.validators || []"
                  :form-data="formData"
                />

                <FormDropdown
                  v-else-if="field.type === 'dropdown'"
                  :ref="(el) => (formRefs[index] = el)"
                  v-model="formData[field.key]"
                  :label="field.label"
                  :placeholder="field.placeholder"
                  :required="field.required"
                  :disabled="field.disabled"
                  :options="field.options"
                  :option-label="field.optionLabel || 'label'"
                  :option-value="field.optionValue || 'value'"
                  :filter="field.filter"
                  :filter-placeholder="field.filterPlaceholder"
                  :editable="field.editable"
                  :help-text="field.helpText"
                  :validators="field.validators || []"
                  :form-data="formData"
                />

                <FormMultiSelect
                  v-else-if="field.type === 'multiselect'"
                  :ref="(el) => (formRefs[index] = el)"
                  v-model="formData[field.key]"
                  :label="field.label"
                  :placeholder="field.placeholder"
                  :required="field.required"
                  :disabled="field.disabled"
                  :options="field.options"
                  :option-label="field.optionLabel || 'label'"
                  :option-value="field.optionValue || 'value'"
                  :filter="field.filter"
                  :filter-placeholder="field.filterPlaceholder"
                  :max-selected-labels="field.maxSelectedLabels"
                  :selected-items-label="field.selectedItemsLabel"
                  :selection-limit="field.selectionLimit"
                  :help-text="field.helpText"
                  :validators="field.validators || []"
                  :form-data="formData"
                />
              </template>
            </div>
          </TabPanel>

          <!-- Tab 2: Stress Configuration -->
          <TabPanel>
            <template #header>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-sliders-h"></i>
                <span>Stress Configuration</span>
              </div>
            </template>

            <div v-if="sensitivityGroups.length > 0" class="grouped-form">
              <FormGroup
                v-for="(group, groupIndex) in sensitivityGroups"
                :key="`sensitivity-group-${groupIndex}`"
                :ref="
                  (el) =>
                    (groupRefs[tradeDetailGroups.length + groupIndex] = el)
                "
                :title="group.title"
                :fields="group.fields"
                v-model="formData"
                :collapsible="group.collapsible !== false"
                :initially-collapsed="group.initiallyCollapsed || false"
                :validators="group.validators || []"
              />
            </div>
            <div v-else class="p-3 text-center text-color-secondary">
              <p>No stress configuration available for this product.</p>
            </div>
          </TabPanel>

          <!-- Tab 3: Scenario Configuration -->
          <TabPanel>
            <template #header>
              <div class="flex align-items-center gap-2">
                <i class="pi pi-cog"></i>
                <span>Scenario Configuration</span>
              </div>
            </template>

            <FormGroup
              title="Scenario Configuration"
              :collapsible="true"
              :initially-collapsed="false"
              class="mt-3"
            >
              <div class="scenario-config-upload">
                <div class="mb-3">
                  <label class="block mb-2 font-semibold"
                    >Upload Scenario Configuration</label
                  >
                  <p class="text-sm text-color-secondary mb-2">
                    Upload a JSON or Excel (.xlsx) file containing stress test
                    scenario definitions.
                  </p>

                  <FileUpload
                    mode="basic"
                    accept=".json,.xlsx"
                    :maxFileSize="1000000"
                    :auto="false"
                    chooseLabel="Choose Scenario Config File (JSON or Excel)"
                    @select="onScenarioConfigSelect"
                    :disabled="isLoading"
                    class="mb-2"
                  />

                  <div v-if="scenarioConfigFile" class="scenario-config-status">
                    <div
                      class="flex align-items-center gap-2 p-2 bg-primary-50 border-round"
                    >
                      <i class="pi pi-file text-primary"></i>
                      <span class="text-sm">{{ scenarioConfigFile.name }}</span>
                      <Button
                        icon="pi pi-times"
                        class="p-button-text p-button-sm p-button-danger"
                        @click="clearScenarioConfig"
                      />
                    </div>

                    <Message
                      v-if="scenarioConfigError"
                      severity="error"
                      :closable="false"
                      class="mt-2"
                    >
                      {{ scenarioConfigError }}
                    </Message>

                    <Message
                      v-else-if="scenarioConfigData"
                      severity="success"
                      :closable="false"
                      class="mt-2"
                    >
                      Scenario config loaded:
                      {{ scenarioConfigData.scenarios?.length || 0 }}
                      scenario(s)
                    </Message>

                    <!-- Detailed Scenario Information Panel -->
                    <Panel
                      v-if="hasFullyParsedScenarioData"
                      header="Scenario Details"
                      :toggleable="true"
                      :collapsed="false"
                      class="mt-3"
                    >
                      <div class="scenario-details">
                        <div
                          v-for="(
                            scenario, idx
                          ) in scenarioConfigData.scenarios"
                          :key="idx"
                          class="scenario-item mb-4 pb-3"
                          :class="{
                            'border-bottom-1 surface-border':
                              idx < scenarioConfigData.scenarios.length - 1
                          }"
                        >
                          <!-- Scenario Header -->
                          <div class="mb-3">
                            <h4 class="m-0 mb-1 text-primary">
                              {{ scenario.id }}
                            </h4>
                            <p
                              v-if="scenario.description"
                              class="text-sm text-color-secondary m-0"
                            >
                              {{ scenario.description }}
                            </p>
                          </div>

                          <!-- Discount Curves -->
                          <div
                            v-if="
                              scenario.discount_curves &&
                              scenario.discount_curves.length > 0
                            "
                            class="mb-3"
                          >
                            <h5 class="text-sm font-semibold mb-2">
                              Discount Curves
                            </h5>
                            <div
                              v-for="(
                                curve, curveIdx
                              ) in scenario.discount_curves"
                              :key="curveIdx"
                              class="ml-3 mb-2 p-2 surface-50 border-round"
                            >
                              <div class="flex gap-3 flex-wrap text-sm">
                                <span
                                  ><strong>Currency:</strong>
                                  {{ curve.ccy }}</span
                                >
                                <span
                                  ><strong>Shift Type:</strong>
                                  {{ curve.shift_type }}</span
                                >
                              </div>
                              <div class="mt-2 text-sm">
                                <strong>Tenors:</strong>
                                {{ curve.shift_tenors?.join(', ') || 'N/A' }}
                              </div>
                              <div class="mt-1 text-sm">
                                <strong>Shifts:</strong>
                                {{ curve.shifts?.join(', ') || 'N/A' }}
                              </div>
                            </div>
                          </div>

                          <!-- FX Spots -->
                          <div
                            v-if="
                              scenario.fx_spots && scenario.fx_spots.length > 0
                            "
                            class="mb-3"
                          >
                            <h5 class="text-sm font-semibold mb-2">
                              FX Spot Shocks
                            </h5>
                            <div
                              v-for="(fx, fxIdx) in scenario.fx_spots"
                              :key="fxIdx"
                              class="ml-3 mb-2 p-2 surface-50 border-round"
                            >
                              <div class="flex gap-3 flex-wrap text-sm">
                                <span
                                  ><strong>Currency Pair:</strong>
                                  {{ fx.ccypair }}</span
                                >
                                <span
                                  ><strong>Shift Type:</strong>
                                  {{ fx.shift_type }}</span
                                >
                                <span
                                  ><strong>Shift Size:</strong>
                                  {{ fx.shift_size }}</span
                                >
                              </div>
                            </div>
                          </div>

                          <!-- FX Volatilities -->
                          <div
                            v-if="
                              scenario.fx_volatilities &&
                              scenario.fx_volatilities.length > 0
                            "
                            class="mb-3"
                          >
                            <h5 class="text-sm font-semibold mb-2">
                              FX Volatility Shocks
                            </h5>
                            <div
                              v-for="(vol, volIdx) in scenario.fx_volatilities"
                              :key="volIdx"
                              class="ml-3 mb-2 p-2 surface-50 border-round"
                            >
                              <div class="flex gap-3 flex-wrap text-sm">
                                <span
                                  ><strong>Currency Pair:</strong>
                                  {{ vol.ccypair }}</span
                                >
                                <span
                                  ><strong>Shift Type:</strong>
                                  {{ vol.shift_type }}</span
                                >
                              </div>
                              <div class="mt-2 text-sm">
                                <strong>Expiries:</strong>
                                {{ vol.shift_expiries?.join(', ') || 'N/A' }}
                              </div>
                              <div class="mt-1 text-sm">
                                <strong>Shifts:</strong>
                                {{ vol.shifts?.join(', ') || 'N/A' }}
                              </div>
                            </div>
                          </div>

                          <!-- No Risk Factors Message -->
                          <div
                            v-if="
                              (!scenario.discount_curves ||
                                scenario.discount_curves.length === 0) &&
                              (!scenario.fx_spots ||
                                scenario.fx_spots.length === 0) &&
                              (!scenario.fx_volatilities ||
                                scenario.fx_volatilities.length === 0)
                            "
                            class="text-sm text-color-secondary italic"
                          >
                            No risk factors defined for this scenario
                          </div>
                        </div>
                      </div>
                    </Panel>
                  </div>
                </div>
              </div>
            </FormGroup>
          </TabPanel>
        </TabView>
      </div>

      <!-- Actions -->
      <div
        v-if="currentForm"
        class="flex gap-3 justify-content-end mt-4 pt-3 border-top-1 surface-border"
      >
        <Button
          label="Calculate"
          icon="pi pi-play"
          :loading="isLoading"
          @click="handleSubmit"
          class="p-button-primary"
        />
        <Button
          label="Reset"
          icon="pi pi-refresh"
          @click="resetForm"
          class="p-button-secondary"
          :disabled="isLoading"
        />
      </div>

      <!-- Results -->
      <div v-if="result" class="results-section">
        <div
          class="flex justify-content-between align-items-center mb-4 pb-3 border-bottom-1 surface-border"
        >
          <h4 class="m-0 text-color font-semibold text-xl">
            Calculation Results
          </h4>
        </div>

        <!-- Key Metrics -->
        <div class="grid mb-4">
          <div class="col-12 md:col-4">
            <div class="metric-card primary-metric">
              <div class="metric-label">Net Present Value (NPV)</div>
              <div class="metric-value">{{ formattedNPV }}</div>
            </div>
          </div>
          <div class="col-12 md:col-4">
            <div class="metric-card">
              <div class="metric-label">Credit Valuation Adjustment (CVA)</div>
              <div class="metric-value">{{ formattedCVA }}</div>
            </div>
          </div>
          <div class="col-12 md:col-4">
            <div class="metric-card">
              <div class="metric-label">Debit Valuation Adjustment (DVA)</div>
              <div class="metric-value">{{ formattedDVA }}</div>
            </div>
          </div>
        </div>

        <!-- Exposure Analysis Tabs -->
        <div class="exposure-analysis-section">
          <h5 class="mb-3 text-color font-semibold text-lg">
            Exposure Analysis
          </h5>

          <TabView v-model:activeIndex="selectedExposureTypeIndex">
            <!-- Base Exposures Tab -->
            <TabPanel>
              <template #header>
                <div class="flex align-items-center gap-2">
                  <i class="pi pi-chart-line"></i>
                  <span>Base Exposures</span>
                </div>
              </template>

              <div class="exposure-tab-content">
                <!-- Filters Panel -->
                <Panel header="Filters" toggleable collapsed class="mb-3">
                  <div
                    class="flex align-items-center justify-content-end gap-2 mb-3"
                  >
                    <div class="flex justify-content-end gap-2">
                      <div class="flex align-items-center gap-2 w-5">
                        <label class="text-sm font-medium">From:</label>
                        <Calendar
                          v-model="exposureStartDate"
                          :manualInput="false"
                          dateFormat="yy-mm-dd"
                          showIcon
                          showButtonBar
                        />
                      </div>
                      <div class="flex align-items-center gap-2 w-5">
                        <label class="text-sm font-medium">To:</label>
                        <Calendar
                          v-model="exposureEndDate"
                          :manualInput="false"
                          dateFormat="yy-mm-dd"
                          showIcon
                          showButtonBar
                        />
                      </div>
                    </div>
                  </div>
                </Panel>

                <!-- Chart Display -->
                <div
                  v-if="currentExposureData && exposureChartData"
                  class="chart-container"
                >
                  <LineChart
                    :data="exposureChartData"
                    title="Expected Exposure"
                    x-title="Date"
                    y-title="EE"
                    y-label="$"
                  />
                </div>
                <div v-else-if="!currentExposureData" class="chart-empty-state">
                  <i class="pi pi-info-circle"></i>
                  <span>No base exposure data available</span>
                </div>
                <div v-else class="chart-empty-state">
                  <i class="pi pi-chart-line"></i>
                  <span>Select at least one series to display the chart</span>
                </div>
              </div>
            </TabPanel>

            <!-- Stress Exposures Tab -->
            <TabPanel>
              <template #header>
                <div class="flex align-items-center gap-2">
                  <i class="pi pi-sliders-h"></i>
                  <span>Stress Exposures</span>
                </div>
              </template>

              <div class="exposure-tab-content">
                <!-- Filters Panel -->
                <Panel header="Filters" toggleable collapsed class="mb-3">
                  <div
                    class="flex align-items-center justify-content-between gap-2 mb-3"
                  >
                    <MultiSelect
                      v-model="selectedMetricColumns"
                      :options="availableMetricColumns"
                      option-label="label"
                      placeholder="Select risk factors to display"
                      class="w-3"
                    />
                    <div class="flex justify-content-end gap-2">
                      <div class="flex align-items-center gap-2 w-5">
                        <label class="text-sm font-medium">From:</label>
                        <Calendar
                          v-model="exposureStartDate"
                          :manualInput="false"
                          dateFormat="yy-mm-dd"
                          showIcon
                          showButtonBar
                        />
                      </div>
                      <div class="flex align-items-center gap-2 w-5">
                        <label class="text-sm font-medium">To:</label>
                        <Calendar
                          v-model="exposureEndDate"
                          :manualInput="false"
                          dateFormat="yy-mm-dd"
                          showIcon
                          showButtonBar
                        />
                      </div>
                    </div>
                  </div>
                </Panel>

                <!-- Chart Display -->
                <div
                  v-if="currentExposureData && exposureChartData"
                  class="chart-container"
                >
                  <LineChart
                    :data="exposureChartData"
                    title="Expected Exposure"
                    x-title="Date"
                    y-title="EE"
                    y-label="$"
                  />
                </div>
                <div v-else-if="!currentExposureData" class="chart-empty-state">
                  <i class="pi pi-info-circle"></i>
                  <span>No sensitivity exposure data available</span>
                </div>
                <div v-else class="chart-empty-state">
                  <i class="pi pi-chart-line"></i>
                  <span
                    >Select at least one risk factor to display the chart</span
                  >
                </div>
              </div>
            </TabPanel>

            <!-- Scenario Exposures Tab -->
            <TabPanel>
              <template #header>
                <div class="flex align-items-center gap-2">
                  <i class="pi pi-bolt"></i>
                  <span>Scenario Exposures</span>
                </div>
              </template>

              <div class="exposure-tab-content">
                <!-- Filters Panel -->
                <Panel header="Filters" toggleable collapsed class="mb-3">
                  <div
                    class="flex align-items-center justify-content-between gap-2 mb-3"
                  >
                    <MultiSelect
                      v-model="selectedMetricColumns"
                      :options="availableMetricColumns"
                      option-label="label"
                      placeholder="Select series to display"
                      class="w-3"
                    />
                    <div class="flex justify-content-end gap-2">
                      <div class="flex align-items-center gap-2 w-5">
                        <label class="text-sm font-medium">From:</label>
                        <Calendar
                          v-model="exposureStartDate"
                          :manualInput="false"
                          dateFormat="yy-mm-dd"
                          showIcon
                          showButtonBar
                        />
                      </div>
                      <div class="flex align-items-center gap-2 w-5">
                        <label class="text-sm font-medium">To:</label>
                        <Calendar
                          v-model="exposureEndDate"
                          :manualInput="false"
                          dateFormat="yy-mm-dd"
                          showIcon
                          showButtonBar
                        />
                      </div>
                    </div>
                  </div>
                </Panel>

                <!-- Chart Display -->
                <div
                  v-if="currentExposureData && exposureChartData"
                  class="chart-container"
                >
                  <LineChart
                    :data="exposureChartData"
                    title="Expected Exposure"
                    x-title="Date"
                    y-title="EE"
                    y-label="$"
                  />
                </div>
                <div v-else-if="!currentExposureData" class="chart-empty-state">
                  <i class="pi pi-info-circle"></i>
                  <span>No stress exposure data available</span>
                </div>
                <div v-else class="chart-empty-state">
                  <i class="pi pi-chart-line"></i>
                  <span
                    >Select at least one stress scenario to display the
                    chart</span
                  >
                </div>
              </div>
            </TabPanel>
          </TabView>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.form-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  background: var(--surface-ground);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.results-section {
  margin-top: 2rem;
  padding: 2rem;
  border: 1px solid var(--surface-border);
  border-radius: 12px;
  background: var(--surface-0);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.metric-card {
  padding: 2rem;
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  background: var(--surface-50);
  text-align: center;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
  height: 100%;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.primary-metric {
  background: linear-gradient(
    135deg,
    var(--primary-50) 0%,
    var(--primary-100) 100%
  );
  border-color: var(--primary-200);
}

.metric-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-color-secondary);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-color);
  margin-bottom: 0.25rem;
  line-height: 1.2;
}

.primary-metric .metric-value {
  color: var(--primary-700);
}

.metric-detail {
  font-size: 0.75rem;
  color: var(--text-color-secondary);
  font-style: italic;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.chart-section {
  margin-bottom: 0;
}

.chart-section h6 {
  margin: 0 0 1rem 0;
  color: var(--text-color);
  font-weight: 500;
  font-size: 1rem;
  text-align: center;
}

.chart-container {
  background: var(--surface-0);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.chart-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  background: var(--surface-50);
  border: 1px dashed var(--surface-border);
  border-radius: 8px;
  color: var(--text-color-secondary);
  gap: 0.5rem;
}

.chart-empty-state i {
  font-size: 2rem;
  opacity: 0.5;
}

.result-display {
  background: var(--surface-0);
  border: 1px solid var(--surface-border);
  border-radius: 4px;
  padding: 1rem;
  overflow-x: auto;
}

.result-display pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: var(--text-color);
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.875rem;
  line-height: 1.4;
}

.grouped-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .results-section {
    padding: 1rem;
  }

  .chart-container {
    padding: 1rem;
  }

  .metric-value {
    font-size: 1.5rem;
  }
}
</style>
