<template>
  <div>
    <!-- File Upload Section -->
    <FileUploadSection
      :is-uploading="isUploading"
      @file-select="handlePortfolioUpload"
    />

    <!-- Empty State -->
    <Card v-if="!hasPortfolioData && !isUploading" class="empty-state">
      <template #content>
        <div class="empty-state-content">
          <i class="pi pi-upload empty-state-icon"></i>
          <h3>Upload Portfolio Data</h3>
          <p>Each sheet should contain trades with TradeType column.</p>
        </div>
      </template>
    </Card>

    <!-- Portfolio Configuration (shown after upload) -->
    <div v-if="hasPortfolioData" class="mb-2">
      <!-- Selection Controls -->
      <div class="batch-controls">
      <div class="selection-controls">
        <div class="selection-info">
          <Checkbox
            v-model="allSheetsSelected"
            :binary="true"
            @change="toggleSelectAll"
            :disabled="isCalculating"
          />
          <label class="ml-2">
            <span v-if="allSheetsSelected">All sheets selected</span>
            <span v-else-if="hasSelectedSheets">
              {{ localSelectedSheets.length }} of
              {{ portfolioSheets.length }} sheets selected ({{
                selectedTradeCount
              }}
              trades)
              <span
                v-if="nettingSetsData && nettingSetsData.length > 0"
                class="text-primary ml-2"
              >
                • {{ nettingSetsData.length }} netting set(s)
              </span>
            </span>
            <span v-else>Select sheets to calculate</span>
          </label>
        </div>

        <Button
          :label="`Calculate Portfolio (${selectedTradeCount} trades)`"
          icon="pi pi-calculator"
          @click="handleCalculate"
          :disabled="!canCalculate"
          :loading="isCalculating"
          class="p-button-primary"
        />
      </div>
    </div>

    <!-- Sheet Selection List -->
    <div class="sheet-selection-list">
      <div
        v-for="sheetName in portfolioSheets"
        :key="sheetName"
        class="sheet-item"
        :class="{ selected: isSheetSelected(sheetName) }"
      >
        <Checkbox
          :model-value="isSheetSelected(sheetName)"
          :binary="true"
          @change="toggleSheetSelection(sheetName)"
          :disabled="isCalculating"
        />
        <span class="sheet-name">{{ sheetName }}</span>
        <span class="trade-count">
          {{ getSheetData(sheetName).length }} trades
        </span>
      </div>
    </div>

    <!-- Data and Configuration Tabs -->
    <div class="card mt-3">
      <div class="results-header">
        <h4>Portfolio Data</h4>
      </div>

      <TabView>
        <TabPanel>
          <template #header>
            <div class="flex align-items-center gap-2">
              <i class="pi pi-table"></i>
              <span>Portfolio Data</span>
            </div>
          </template>
          <!-- Nested TabView for each sheet -->
          <TabView :scrollable="true">
            <TabPanel v-for="sheetName in portfolioSheets" :key="sheetName">
              <template #header>
                <span>{{ sheetName }}</span>
              </template>
              <div class="sheet-content">
                <SimpleTable
                  :data="getSheetData(sheetName)"
                  :downloadFileName="`${sheetName}_data`"
                />
              </div>
            </TabPanel>
          </TabView>
        </TabPanel>

        <TabPanel>
          <template #header>
            <div class="flex align-items-center gap-2">
              <i class="pi pi-sliders-h"></i>
              <span>Stress Configuration</span>
            </div>
          </template>
          <!-- Sensitivity Configuration using FormGroup -->
          <div class="stress-config-content">
            <FormGroup
              :title="sensitivityGroup.title"
              :fields="sensitivityGroup.fields"
              v-model="localSensitivityFormData"
              :collapsible="false"
              :initially-collapsed="false"
              :as-panel="false"
            />
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

          <div class="stress-config-content">
            <!-- Scenario Config Upload -->
            <div class="mb-3">
              <label class="block mb-2 font-semibold"
                >Upload Scenario Configuration
              </label>
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
                :disabled="isCalculating"
                class="mb-2"
              />

              <!-- Scenario Config Status -->
              <div
                v-if="scenarioConfigFile"
                class="scenario-config-status mt-3"
              >
                <div
                  class="flex align-items-center gap-2 p-2 bg-primary-50 border-round"
                >
                  <i class="pi pi-file text-primary"></i>
                  <span class="text-sm">{{ scenarioConfigFile.name }}</span>
                  <Button
                    icon="pi pi-times"
                    class="p-button-text p-button-sm p-button-danger ml-auto"
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
                  {{ scenarioConfigData.scenarios?.length || 0 }} scenario(s)
                </Message>

                <!-- Editable Scenario Data Table -->
                <div
                  v-if="hasFullyParsedScenarioData"
                  class="scenario-table-container mt-3"
                >
                  <div
                    class="flex justify-content-between align-items-center mb-2"
                  >
                    <h5 class="m-0">Scenario Configuration Data</h5>
                    <Button
                      label="Save Changes"
                      icon="pi pi-save"
                      class="p-button-sm"
                      @click="saveScenarioChanges"
                      :disabled="!hasScenarioChanges"
                    />
                  </div>
                  <DataTable
                    v-model:editingRows="editingRows"
                    :value="flattenedScenarioData"
                    editMode="cell"
                    @cell-edit-complete="onCellEditComplete"
                    :paginator="true"
                    :rows="10"
                    :rowsPerPageOptions="[10, 25, 50]"
                    responsiveLayout="scroll"
                    class="p-datatable-sm"
                  >
                    <Column
                      field="scenario_id"
                      header="Scenario ID"
                      :sortable="true"
                      style="min-width: 120px"
                    >
                      <template #editor="{ data, field }">
                        <InputText v-model="data[field]" autofocus />
                      </template>
                    </Column>
                    <Column
                      field="type"
                      header="Type"
                      :sortable="true"
                      style="min-width: 150px"
                    >
                      <template #editor="{ data, field }">
                        <Dropdown
                          v-model="data[field]"
                          :options="RISK_FACTOR_TYPES"
                          placeholder="Select Type"
                        />
                      </template>
                    </Column>
                    <Column
                      field="ccy"
                      header="Currency / CCY Pair"
                      :sortable="true"
                      style="min-width: 150px"
                    >
                      <template #editor="{ data, field }">
                        <InputText v-model="data[field]" />
                      </template>
                    </Column>
                    <Column
                      field="shift_type"
                      header="Shift Type"
                      :sortable="true"
                      style="min-width: 120px"
                    >
                      <template #editor="{ data, field }">
                        <Dropdown
                          v-model="data[field]"
                          :options="SHIFT_TYPES"
                          placeholder="Select Type"
                        />
                      </template>
                    </Column>
                    <Column
                      field="shift_size"
                      header="Shift Size"
                      :sortable="true"
                      style="min-width: 120px"
                    >
                      <template #editor="{ data, field }">
                        <InputNumber
                          v-model="data[field]"
                          mode="decimal"
                          :minFractionDigits="0"
                          :maxFractionDigits="10"
                          :useGrouping="false"
                        />
                      </template>
                    </Column>
                    <Column
                      field="shift_tenors"
                      header="Tenors / Expiries"
                      :sortable="false"
                      style="min-width: 200px"
                    >
                      <template #editor="{ data, field }">
                        <InputText
                          v-model="data[field]"
                          placeholder="Comma-separated"
                        />
                      </template>
                    </Column>
                    <Column
                      field="shift_terms"
                      header="Terms (Swaption)"
                      :sortable="false"
                      style="min-width: 150px"
                    >
                      <template #body="{ data }">
                        <span v-if="data.type === 'swaption_volatility'">
                          {{ data.shift_terms || '-' }}
                        </span>
                        <span v-else class="text-color-secondary">-</span>
                      </template>
                      <template #editor="{ data, field }">
                        <InputText
                          v-if="data.type === 'swaption_volatility'"
                          v-model="data[field]"
                          placeholder="Comma-separated"
                        />
                        <span v-else class="text-color-secondary">N/A</span>
                      </template>
                    </Column>
                    <Column
                      field="shifts"
                      header="Shifts"
                      :sortable="false"
                      style="min-width: 200px"
                    >
                      <template #editor="{ data, field }">
                        <InputText
                          v-model="data[field]"
                          placeholder="Comma-separated"
                        />
                      </template>
                    </Column>
                    <Column header="Actions" style="min-width: 100px">
                      <template #body="slotProps">
                        <Button
                          icon="pi pi-trash"
                          class="p-button-text p-button-danger p-button-sm"
                          @click="deleteScenarioRow(slotProps.index)"
                        />
                      </template>
                    </Column>
                  </DataTable>
                  <Button
                    label="Add Row"
                    icon="pi pi-plus"
                    class="p-button-sm mt-2"
                    @click="addScenarioRow"
                  />
                </div>
              </div>
            </div>
          </div>
        </TabPanel>
      </TabView>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import SimpleTable from '@/components/Table/SimpleTable.vue'
import FormGroup from '@/components/Form/FormGroup.vue'
import FileUploadSection from './FileUploadSection.vue'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import FileUpload from 'primevue/fileupload'
import Message from 'primevue/message'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import { sensitivityGroup } from '@/forms/shared/sensitivity-fields'

// Services
const store = useStore()
const toast = useToast()

// Constants
const RISK_FACTOR_TYPES = [
  'discount_curve',
  'fx_spot',
  'fx_volatility',
  'swaption_volatility'
]

const SHIFT_TYPES = ['Absolute', 'Relative']

// Props
const props = defineProps({
  module: {
    type: String,
    default: 'pricing'
  },
  submodule: {
    type: String,
    default: 'ore_portfolio'
  },
  portfolioData: {
    type: Object,
    default: null
  },
  nettingSetsData: {
    type: Array,
    default: null
  },
  scenarioConfigData: {
    type: Object,
    default: null
  },
  selectedSheets: {
    type: Array,
    default: () => []
  },
  sensitivityFormData: {
    type: Object,
    default: () => ({ sensitivity_entries: [] })
  },
  isCalculating: {
    type: Boolean,
    default: false
  },
  isUploading: {
    type: Boolean,
    default: false
  }
})

// Emit events
const emit = defineEmits([
  'update:selectedSheets',
  'update:sensitivityFormData',
  'update:isUploading',
  'calculate',
  'portfolio-uploaded',
  'scenario-data-updated',
  'netting-sets-updated'
])

// Local state
const allSheetsSelected = ref(true)

// Scenario config state
const scenarioConfigFile = ref(null)
const scenarioConfigError = ref(null)

// Editable scenario table state
const editingRows = ref([])
const flattenedScenarioData = ref([])
const originalScenarioData = ref(null)
const hasScenarioChanges = ref(false)

// Computed properties with getters/setters for v-model
const localSelectedSheets = computed({
  get: () => props.selectedSheets,
  set: (value) => emit('update:selectedSheets', value)
})

const localSensitivityFormData = computed({
  get: () => props.sensitivityFormData,
  set: (value) => emit('update:sensitivityFormData', value)
})

const hasFullyParsedScenarioData = computed(() => {
  return (
    props.scenarioConfigData &&
    props.scenarioConfigData.scenarios &&
    Array.isArray(props.scenarioConfigData.scenarios) &&
    props.scenarioConfigData.scenarios.length > 0
  )
})

const hasPortfolioData = computed(() => {
  return props.portfolioData && Object.keys(props.portfolioData).length > 0
})

const portfolioSheets = computed(() => {
  if (!props.portfolioData) return []
  return Object.keys(props.portfolioData)
})

const hasSelectedSheets = computed(() => {
  return localSelectedSheets.value.length > 0
})

const canCalculate = computed(() => {
  return hasSelectedSheets.value && !props.isCalculating
})

const selectedTradeCount = computed(() => {
  let count = 0
  localSelectedSheets.value.forEach((sheetName) => {
    // Skip NettingSets sheet as it's not a trade type
    if (sheetName !== 'NettingSets') {
      const data = getSheetData(sheetName)
      count += data.length
    }
  })
  return count
})

// Methods
const getSheetData = (sheetName) => {
  if (!props.portfolioData || !props.portfolioData[sheetName]) return []
  return JSON.parse(props.portfolioData[sheetName])
}

const toggleSelectAll = () => {
  if (!allSheetsSelected.value) {
    localSelectedSheets.value = []
  } else {
    localSelectedSheets.value = [...portfolioSheets.value]
  }
}

const toggleSheetSelection = (sheetName) => {
  const currentSheets = [...localSelectedSheets.value]
  const index = currentSheets.indexOf(sheetName)

  if (index > -1) {
    currentSheets.splice(index, 1)
  } else {
    currentSheets.push(sheetName)
  }

  // Update allSheetsSelected flag
  allSheetsSelected.value =
    currentSheets.length === portfolioSheets.value.length

  localSelectedSheets.value = currentSheets
}

const isSheetSelected = (sheetName) => {
  return localSelectedSheets.value.includes(sheetName)
}

const handleCalculate = () => {
  emit('calculate')
}

// Portfolio upload handler
const handlePortfolioUpload = async ({ file, formData }) => {
  try {
    emit('update:isUploading', true)

    toast.add({
      severity: 'info',
      summary: 'Uploading File',
      detail: 'Processing portfolio data...',
      life: 3000
    })

    const response = await store.dispatch('uploadPortfolioData', {
      formData,
      module: props.module,
      submodule: props.submodule
    })

    // Extract NettingSets sheet if present
    let nettingSets = null
    if (response.data.NettingSets) {
      try {
        nettingSets = JSON.parse(response.data.NettingSets)
      } catch (e) {
        console.warn('Failed to parse NettingSets sheet:', e)
      }
    }

    // Emit the uploaded data to parent
    emit('portfolio-uploaded', response.data)
    emit('netting-sets-updated', nettingSets)

    toast.add({
      severity: 'success',
      summary: 'Upload Successful',
      detail: `Portfolio data loaded with ${Object.keys(response.data).length} sheet(s)`,
      life: 3000
    })
  } catch (error) {
    console.error('Upload error:', error)
    toast.add({
      severity: 'error',
      summary: 'Upload Failed',
      detail:
        error.response?.data?.message || 'Failed to upload portfolio file',
      life: 5000
    })
  } finally {
    emit('update:isUploading', false)
  }
}

// Scenario config upload handler
const onScenarioConfigSelect = async (event) => {
  const file = event.files[0]
  if (!file) return

  scenarioConfigFile.value = file
  scenarioConfigError.value = null

  await handleScenarioUpload(file)
}

// Handle scenario upload (file or data)
const handleScenarioUpload = async (fileOrData) => {
  try {
    // Check if it's a file upload or direct data update (from table save)
    if (fileOrData && typeof fileOrData === 'object' && fileOrData.scenarios) {
      // Direct data update from table save
      emit('scenario-data-updated', fileOrData)

      toast.add({
        severity: 'success',
        summary: 'Changes Saved',
        detail: `Updated ${fileOrData.scenarios?.length || 0} scenario(s)`,
        life: 3000
      })
      return
    }

    // File upload handling
    const file = fileOrData
    const fileExt = file.name.split('.').pop().toLowerCase()

    if (fileExt === 'json') {
      // Parse JSON directly in frontend
      const fileContent = await readFileContent(file)
      const parsedData = JSON.parse(fileContent)

      // Validate JSON structure
      validateScenarioConfigStructure(parsedData)

      emit('scenario-data-updated', parsedData)

      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: `Loaded ${parsedData.scenarios?.length || 0} scenario(s)`,
        life: 3000
      })
    } else if (fileExt === 'xlsx') {
      // For Excel, upload to backend for parsing
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

      emit('scenario-data-updated', uploadResponse.data)

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
    emit('scenario-data-updated', null)

    toast.add({
      severity: 'error',
      summary: 'Upload Error',
      detail: error.message || 'Failed to parse scenario configuration',
      life: 5000
    })
  }
}

// Helper: Read file content
const readFileContent = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

// Helper: Validate scenario config structure
const validateScenarioConfigStructure = (config) => {
  if (!config) {
    throw new Error('Config is empty')
  }

  if (!config.scenarios || !Array.isArray(config.scenarios)) {
    throw new Error('Config must contain "scenarios" array')
  }

  if (config.scenarios.length === 0) {
    throw new Error('At least one scenario is required')
  }

  config.scenarios.forEach((scenario, index) => {
    if (!scenario.id) {
      throw new Error(`Scenario ${index + 1} missing "id" field`)
    }
  })
}

// Clear scenario config
const clearScenarioConfig = () => {
  scenarioConfigFile.value = null
  scenarioConfigError.value = null
  flattenedScenarioData.value = []
  originalScenarioData.value = null
  hasScenarioChanges.value = false
  emit('scenario-data-updated', null)
}

// Flatten scenario data for table display
const flattenScenarioData = (scenarioData) => {
  if (!scenarioData || !scenarioData.scenarios) return []

  const flattened = []

  scenarioData.scenarios.forEach((scenario) => {
    // Add discount curves
    if (scenario.discount_curves && scenario.discount_curves.length > 0) {
      scenario.discount_curves.forEach((curve) => {
        flattened.push({
          scenario_id: scenario.id,
          type: 'discount_curve',
          ccy: curve.ccy || '',
          shift_type: curve.shift_type || '',
          shift_size: null,
          shift_tenors: Array.isArray(curve.shift_tenors)
            ? curve.shift_tenors.join(', ')
            : '',
          shift_terms: '',
          shifts: Array.isArray(curve.shifts) ? curve.shifts.join(', ') : ''
        })
      })
    }

    // Add FX spots
    if (scenario.fx_spots && scenario.fx_spots.length > 0) {
      scenario.fx_spots.forEach((fx) => {
        flattened.push({
          scenario_id: scenario.id,
          type: 'fx_spot',
          ccy: fx.ccypair || '',
          shift_type: fx.shift_type || '',
          shift_size: fx.shift_size || null,
          shift_tenors: '',
          shift_terms: '',
          shifts: ''
        })
      })
    }

    // Add FX volatilities
    if (scenario.fx_volatilities && scenario.fx_volatilities.length > 0) {
      scenario.fx_volatilities.forEach((vol) => {
        flattened.push({
          scenario_id: scenario.id,
          type: 'fx_volatility',
          ccy: vol.ccypair || '',
          shift_type: vol.shift_type || '',
          shift_size: null,
          shift_tenors: Array.isArray(vol.shift_expiries)
            ? vol.shift_expiries.join(', ')
            : '',
          shift_terms: '',
          shifts: Array.isArray(vol.shifts) ? vol.shifts.join(', ') : ''
        })
      })
    }

    // Add Swaption volatilities
    if (scenario.swaption_volatilities && scenario.swaption_volatilities.length > 0) {
      scenario.swaption_volatilities.forEach((vol) => {
        flattened.push({
          scenario_id: scenario.id,
          type: 'swaption_volatility',
          ccy: vol.ccy || '',
          shift_type: vol.shift_type || '',
          shift_size: null,
          shift_tenors: Array.isArray(vol.shift_expiries)
            ? vol.shift_expiries.join(', ')
            : '',
          shift_terms: Array.isArray(vol.shift_terms)
            ? vol.shift_terms.join(', ')
            : '',
          shifts: Array.isArray(vol.shifts) ? vol.shifts.join(', ') : ''
        })
      })
    }
  })

  return flattened
}

// Unflatten scenario data from table to original structure
const unflattenScenarioData = (flattenedData) => {
  const scenariosMap = new Map()

  flattenedData.forEach((row) => {
    if (!scenariosMap.has(row.scenario_id)) {
      scenariosMap.set(row.scenario_id, {
        id: row.scenario_id,
        discount_curves: [],
        fx_spots: [],
        fx_volatilities: [],
        swaption_volatilities: []
      })
    }

    const scenario = scenariosMap.get(row.scenario_id)

    if (row.type === 'discount_curve') {
      scenario.discount_curves.push({
        ccy: row.ccy,
        shift_type: row.shift_type,
        shift_tenors: row.shift_tenors
          ? row.shift_tenors.split(',').map((t) => t.trim())
          : [],
        shifts: row.shifts
          ? row.shifts.split(',').map((s) => parseFloat(s.trim()))
          : []
      })
    } else if (row.type === 'fx_spot') {
      scenario.fx_spots.push({
        ccypair: row.ccy,
        shift_type: row.shift_type,
        shift_size: row.shift_size
      })
    } else if (row.type === 'fx_volatility') {
      scenario.fx_volatilities.push({
        ccypair: row.ccy,
        shift_type: row.shift_type,
        shift_expiries: row.shift_tenors
          ? row.shift_tenors.split(',').map((t) => t.trim())
          : [],
        shifts: row.shifts
          ? row.shifts.split(',').map((s) => parseFloat(s.trim()))
          : []
      })
    } else if (row.type === 'swaption_volatility') {
      scenario.swaption_volatilities.push({
        ccy: row.ccy,
        shift_type: row.shift_type,
        shift_expiries: row.shift_tenors
          ? row.shift_tenors.split(',').map((t) => t.trim())
          : [],
        shift_terms: row.shift_terms
          ? row.shift_terms.split(',').map((t) => t.trim())
          : [],
        shifts: row.shifts
          ? row.shifts.split(',').map((s) => parseFloat(s.trim()))
          : []
      })
    }
  })

  return {
    scenarios: Array.from(scenariosMap.values())
  }
}

// Handle cell edit completion
const onCellEditComplete = (event) => {
  const { data, newValue, field } = event
  data[field] = newValue
  hasScenarioChanges.value = true
}

// Save scenario changes
const saveScenarioChanges = () => {
  const unflattenedData = unflattenScenarioData(flattenedScenarioData.value)
  emit('scenario-upload', unflattenedData)
  originalScenarioData.value = JSON.parse(JSON.stringify(unflattenedData))
  hasScenarioChanges.value = false
}

// Add new scenario row
const addScenarioRow = () => {
  flattenedScenarioData.value.push({
    scenario_id: 'New_Scenario',
    type: 'discount_curve',
    ccy: '',
    shift_type: 'Absolute',
    shift_size: null,
    shift_tenors: '',
    shift_terms: '',
    shifts: ''
  })
  hasScenarioChanges.value = true
}

// Delete scenario row
const deleteScenarioRow = (index) => {
  flattenedScenarioData.value.splice(index, 1)
  hasScenarioChanges.value = true
}

// Watch for changes to selectedSheets to update allSheetsSelected flag
watch(
  () => props.selectedSheets,
  (newValue) => {
    allSheetsSelected.value = newValue.length === portfolioSheets.value.length
  }
)

// Watch for scenario config data changes and flatten for table
watch(
  () => props.scenarioConfigData,
  (newValue) => {
    if (newValue) {
      flattenedScenarioData.value = flattenScenarioData(newValue)
      originalScenarioData.value = JSON.parse(JSON.stringify(newValue))
      hasScenarioChanges.value = false
    } else {
      flattenedScenarioData.value = []
      originalScenarioData.value = null
      hasScenarioChanges.value = false
    }
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
.batch-controls {
  margin-bottom: 1.5rem;
  padding: 1rem;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  background: var(--surface-50);
}

.selection-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selection-info {
  display: flex;
  align-items: center;
}

.selection-info label {
  color: var(--text-color-secondary);
  font-weight: 500;
  cursor: pointer;
}

.sheet-selection-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 0.5rem;
  margin-top: 1rem;
}

.sheet-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid var(--surface-border);
  border-radius: 4px;
  background: var(--surface-0);
  transition: all 0.2s ease;
}

.sheet-item.selected {
  background: var(--primary-50);
  border-color: var(--primary-200);
}

.sheet-item .sheet-name {
  margin-left: 0.5rem;
  font-weight: 500;
  flex: 1;
}

.sheet-item .trade-count {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.sheet-content {
  padding: 1rem 0;
}

.stress-config-content {
  padding: 1rem 0;
}

.results-header {
  margin-bottom: 1.5rem;
}

.results-header h4 {
  margin: 0;
  color: var(--primary-color);
  font-weight: 600;
  font-size: 1.25rem;
}

.scenario-info {
  padding: 1.5rem;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  background: var(--surface-50);
}

.scenario-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  background: var(--surface-50);
  border: 1px dashed var(--surface-border);
  border-radius: 8px;
  color: var(--text-color-secondary);
  text-align: center;
}

.scenario-table-container {
  padding: 1rem;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  background: var(--surface-0);
}

.scenario-table-container h5 {
  color: var(--text-color);
  font-weight: 600;
}

/* Responsive Design */
@media (max-width: 768px) {
  .selection-controls {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .selection-controls .p-button {
    width: 100%;
  }

  .sheet-selection-list {
    grid-template-columns: 1fr;
  }
}

:deep(.p-tabview-nav-link) {
  padding: 1rem 1.5rem;
}

:deep(.p-tabview-panels) {
  padding: 0;
}

:deep(.p-tabview-panel) {
  padding: 1rem 0;
}

/* Empty State */
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  padding: 2rem;
  margin-top: 1rem;
}

.empty-state-content {
  text-align: center;
  max-width: 400px;
}

.empty-state-icon {
  font-size: 4rem;
  color: var(--primary-color);
  margin-bottom: 1rem;
  opacity: 0.6;
}

.empty-state h3 {
  margin: 0 0 1rem 0;
  color: var(--text-color);
  font-weight: 600;
}

.empty-state p {
  margin: 0;
  color: var(--text-color-secondary);
  line-height: 1.5;
}
</style>
