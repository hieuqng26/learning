<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
import SimpleTable from '@/components/Table/SimpleTable.vue'
import { formatCurrency } from '@/components/Table/utils.js'

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
const selectedFile = ref(null)
const portfolioData = ref(null)
const portfolioResults = ref({})
const isUploading = ref(false)
const isCalculating = ref({})
const activeTab = ref(0)

// Batch calculation state
const selectedSheets = ref([])
const batchCalculating = ref(false)
const calculationProgress = ref({})

// Computed properties
const hasPortfolioData = computed(() => {
  return portfolioData.value && Object.keys(portfolioData.value).length > 0
})

const portfolioSheets = computed(() => {
  if (!portfolioData.value) return []
  return Object.keys(portfolioData.value)
})

const allSheetsSelected = computed(() => {
  return (
    portfolioSheets.value.length > 0 &&
    selectedSheets.value.length === portfolioSheets.value.length
  )
})

const hasSelectedSheets = computed(() => {
  return selectedSheets.value.length > 0
})

const canCalculateBatch = computed(() => {
  return (
    hasSelectedSheets.value && !batchCalculating.value && !isUploading.value
  )
})

const getSheetData = (sheetName) => {
  if (!portfolioData.value || !portfolioData.value[sheetName]) return []
  return JSON.parse(portfolioData.value[sheetName])
}

const getSheetResults = (sheetName) => {
  if (!portfolioResults.value || !portfolioResults.value[sheetName]) return null
  return portfolioResults.value[sheetName]
}

const getSheetSummary = (sheetName) => {
  const results = getSheetResults(sheetName)
  if (!results) return null

  return {
    trade_count: results.trade_count || 0,
    successful_trades: results.successful_trades || 0,
    failed_trades: results.failed_trades || 0,
    portfolio_npv: results.portfolio_npv || 0
  }
}

// Methods
const onFileSelect = async (event) => {
  const files = event.files
  if (!files || files.length === 0) {
    toast.add({
      severity: 'warn',
      summary: 'No File Selected',
      detail: 'Please select an Excel file to upload',
      life: 3000
    })
    return
  }

  const file = files[0]
  selectedFile.value = file

  // Reset previous data
  portfolioData.value = null
  portfolioResults.value = {}
  selectedSheets.value = []
  calculationProgress.value = {}

  // Auto-upload the file immediately after selection
  await uploadPortfolioFile(file)
}

const uploadPortfolioFile = async (file) => {
  try {
    isUploading.value = true

    const formData = new FormData()
    formData.append('file', file)

    toast.add({
      severity: 'info',
      summary: 'Uploading File',
      detail: 'Processing portfolio data...',
      life: 3000
    })

    const response = await store.dispatch('uploadPortfolioData', {
      formData,
      module: props.module || 'pricing',
      submodule: props.submodule || 'portfolio'
    })

    portfolioData.value = response.data

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
    isUploading.value = false
  }
}

const calculatePortfolio = async (sheetName) => {
  const sheetData = getSheetData(sheetName)
  if (!sheetData || sheetData.length === 0) {
    toast.add({
      severity: 'warn',
      summary: 'No Data',
      detail: `No data available in sheet: ${sheetName}`,
      life: 3000
    })
    return
  }

  try {
    isCalculating.value = { ...isCalculating.value, [sheetName]: true }

    toast.add({
      severity: 'info',
      summary: 'Calculating Portfolio',
      detail: `Pricing ${sheetData.length} trades in ${sheetName}...`,
      life: 3000
    })

    const response = await store.dispatch('calculatePortfolio', {
      portfolio_data: sheetData
    })

    const resultData = response.data
    if (resultData?.trade_results) {
      resultData.trade_results = JSON.parse(resultData.trade_results)
    }

    portfolioResults.value = {
      ...portfolioResults.value,
      [sheetName]: resultData
    }

    toast.add({
      severity: 'success',
      summary: 'Calculation Complete',
      detail: `Portfolio ${sheetName} calculated successfully`,
      life: 3000
    })
  } catch (error) {
    console.error('Calculation error:', error)
    toast.add({
      severity: 'error',
      summary: 'Calculation Failed',
      detail:
        error.response?.data?.message ||
        `Failed to calculate portfolio: ${sheetName}`,
      life: 5000
    })
  } finally {
    isCalculating.value = { ...isCalculating.value, [sheetName]: false }
  }
}

// Sheet selection methods
const toggleSelectAll = () => {
  if (allSheetsSelected.value) {
    selectedSheets.value = []
  } else {
    selectedSheets.value = [...portfolioSheets.value]
  }
}

const toggleSheetSelection = (sheetName) => {
  const index = selectedSheets.value.indexOf(sheetName)
  if (index > -1) {
    selectedSheets.value.splice(index, 1)
  } else {
    selectedSheets.value.push(sheetName)
  }
}

const isSheetSelected = (sheetName) => {
  return selectedSheets.value.includes(sheetName)
}

// Batch calculation method
const calculateSelectedPortfolios = async () => {
  if (!hasSelectedSheets.value) {
    toast.add({
      severity: 'warn',
      summary: 'No Sheets Selected',
      detail: 'Please select at least one sheet to calculate',
      life: 3000
    })
    return
  }

  try {
    batchCalculating.value = true
    calculationProgress.value = {}

    // Initialize progress tracking
    selectedSheets.value.forEach((sheetName) => {
      calculationProgress.value[sheetName] = { status: 'pending' }
    })

    toast.add({
      severity: 'info',
      summary: 'Batch Calculation Started',
      detail: `Calculating ${selectedSheets.value.length} portfolio(s)...`,
      life: 3000
    })

    // Process sheets sequentially
    const results = {}
    let completed = 0
    let failed = 0

    // Process each sheet one by one
    for (let i = 0; i < selectedSheets.value.length; i++) {
      const sheetName = selectedSheets.value[i]

      try {
        calculationProgress.value[sheetName] = {
          status: 'calculating',
          progress: `${i + 1} of ${selectedSheets.value.length}`
        }

        toast.add({
          severity: 'info',
          summary: 'Processing',
          detail: `Calculating ${sheetName} (${i + 1}/${selectedSheets.value.length})...`,
          life: 2000
        })

        const sheetData = getSheetData(sheetName)
        const response = await store.dispatch('calculatePortfolio', {
          portfolio_data: sheetData
        })

        const resultData = response.data
        if (resultData?.trade_results) {
          resultData.trade_results = JSON.parse(resultData.trade_results)
        }

        results[sheetName] = resultData
        calculationProgress.value[sheetName] = {
          status: 'completed',
          progress: `${i + 1} of ${selectedSheets.value.length}`
        }
        completed++
      } catch (error) {
        console.error(`Calculation error for ${sheetName}:`, error)
        calculationProgress.value[sheetName] = {
          status: 'failed',
          error: error.response?.data?.message || 'Calculation failed',
          progress: `${i + 1} of ${selectedSheets.value.length}`
        }
        failed++

        toast.add({
          severity: 'error',
          summary: 'Calculation Failed',
          detail: `Failed to calculate ${sheetName}: ${error.response?.data?.message || 'Unknown error'}`,
          life: 4000
        })
      }
    }

    // Update results
    portfolioResults.value = { ...portfolioResults.value, ...results }

    // Show completion summary
    if (failed === 0) {
      toast.add({
        severity: 'success',
        summary: 'Batch Calculation Complete',
        detail: `Successfully calculated ${completed} portfolio(s)`,
        life: 5000
      })
    } else if (completed > 0) {
      toast.add({
        severity: 'warn',
        summary: 'Batch Calculation Partial Success',
        detail: `${completed} succeeded, ${failed} failed`,
        life: 5000
      })
    } else {
      toast.add({
        severity: 'error',
        summary: 'Batch Calculation Failed',
        detail: `All ${failed} portfolio(s) failed to calculate`,
        life: 5000
      })
    }
  } catch (error) {
    console.error('Batch calculation error:', error)
    toast.add({
      severity: 'error',
      summary: 'Batch Calculation Error',
      detail: 'An unexpected error occurred during batch calculation',
      life: 5000
    })
  } finally {
    batchCalculating.value = false
  }
}

// Watchers
watch(hasPortfolioData, (newValue) => {
  if (newValue) {
    activeTab.value = 0
  }
})
</script>

<template>
  <div class="portfolio-container">
    <Card>
      <template #title>
        <div class="flex align-items-center gap-2">
          <i class="pi pi-briefcase"></i>
          Portfolio Pricing
        </div>
      </template>

      <template #content>
        <!-- File Upload Section -->
        <div class="upload-section">
          <h4>Upload Portfolio Data</h4>
          <p class="upload-description">
            Upload an Excel file containing portfolio data. Each sheet should
            contain trades of the same type (e.g., IRSwap, IRFixedRateBond,
            OISwap, CallableCCS).
          </p>

          <div class="upload-controls">
            <FileUpload
              mode="basic"
              :name="props.module + '_' + props.submodule + '_table'"
              accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
              :auto="true"
              :custom-upload="true"
              :choose-label="
                selectedFile?.name ? selectedFile.name : 'Select File'
              "
              :disabled="isUploading"
              :maxFileSize="1000000"
              @uploader="onFileSelect"
            />
          </div>

          <div v-if="selectedFile" class="selected-file-info mt-2">
            <small class="text-color-secondary">
              <span v-if="isUploading">
                <i class="pi pi-spin pi-spinner mr-2"></i>
                Uploading: {{ selectedFile.name }} ({{
                  (selectedFile.size / 1024 / 1024).toFixed(2)
                }}
                MB)
              </span>
              <span v-else>
                <i
                  class="pi pi-check-circle mr-2"
                  style="color: var(--green-500)"
                ></i>
                Processed: {{ selectedFile.name }} ({{
                  (selectedFile.size / 1024 / 1024).toFixed(2)
                }}
                MB)
              </span>
            </small>
          </div>
        </div>

        <!-- Portfolio Data Display -->
        <div v-if="hasPortfolioData" class="portfolio-data-section">
          <div class="section-header">
            <h4>Portfolio Data</h4>
            <small class="text-color-secondary">
              {{ portfolioSheets.length }} sheet(s) loaded
            </small>
          </div>

          <!-- Batch Selection Controls -->
          <div class="batch-controls">
            <div class="selection-controls">
              <div class="selection-info">
                <Checkbox
                  v-model="allSheetsSelected"
                  :binary="true"
                  @change="toggleSelectAll"
                  :disabled="batchCalculating"
                />
                <label class="ml-2">
                  <span v-if="allSheetsSelected">All sheets selected</span>
                  <span v-else-if="hasSelectedSheets">
                    {{ selectedSheets.length }} of
                    {{ portfolioSheets.length }} sheets selected
                  </span>
                  <span v-else>Select sheets to calculate</span>
                </label>
              </div>

              <Button
                :label="`Calculate Selected (${selectedSheets.length})`"
                icon="pi pi-calculator"
                @click="calculateSelectedPortfolios"
                :disabled="!canCalculateBatch"
                :loading="batchCalculating"
                class="p-button-primary"
              />
            </div>

            <!-- Batch Progress Indicators -->
            <div
              v-if="
                batchCalculating || Object.keys(calculationProgress).length > 0
              "
              class="batch-progress"
            >
              <div class="progress-header">
                <span class="progress-title">
                  <i
                    class="pi pi-cog mr-2"
                    :class="{ 'pi-spin': batchCalculating }"
                  ></i>
                  <span v-if="batchCalculating">Calculation in Progress</span>
                  <span v-else>Batch Calculation Results</span>
                </span>
                <span v-if="batchCalculating" class="overall-progress">
                  {{
                    Object.values(calculationProgress).filter(
                      (p) => p.status === 'completed' || p.status === 'failed'
                    ).length
                  }}
                  of {{ selectedSheets.length }} completed
                </span>
              </div>
              <div class="progress-items">
                <div
                  v-for="(progress, sheetName) in calculationProgress"
                  :key="sheetName"
                  class="progress-item"
                  :class="progress.status"
                >
                  <i
                    class="progress-icon"
                    :class="{
                      'pi pi-clock': progress.status === 'pending',
                      'pi pi-spin pi-spinner':
                        progress.status === 'calculating',
                      'pi pi-check-circle': progress.status === 'completed',
                      'pi pi-times-circle': progress.status === 'failed'
                    }"
                  ></i>
                  <span class="sheet-name">{{ sheetName }}</span>
                  <span class="status-text">
                    <span v-if="progress.status === 'pending'">Waiting</span>
                    <span v-else-if="progress.status === 'calculating'">
                      Calculating... ({{ progress.progress }})
                    </span>
                    <span v-else-if="progress.status === 'completed'">
                      ✓ Completed ({{ progress.progress }})
                    </span>
                    <span v-else-if="progress.status === 'failed'">
                      ✗ Failed ({{ progress.progress }})
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <TabView v-model:activeIndex="activeTab" :scrollable="true">
            <TabPanel v-for="sheetName in portfolioSheets" :key="sheetName">
              <template #header>
                <div class="tab-header">
                  <Checkbox
                    :model-value="isSheetSelected(sheetName)"
                    :binary="true"
                    @change="toggleSheetSelection(sheetName)"
                    :disabled="batchCalculating"
                    class="mr-2"
                  />
                  <span>{{ sheetName }}</span>
                  <i
                    v-if="calculationProgress[sheetName]"
                    class="ml-2 status-icon"
                    :class="{
                      'pi pi-clock text-orange-500':
                        calculationProgress[sheetName].status === 'pending',
                      'pi pi-spin pi-spinner text-blue-500':
                        calculationProgress[sheetName].status === 'calculating',
                      'pi pi-check-circle text-green-500':
                        calculationProgress[sheetName].status === 'completed',
                      'pi pi-times-circle text-red-500':
                        calculationProgress[sheetName].status === 'failed'
                    }"
                  ></i>
                </div>
              </template>
              <div class="sheet-content">
                <!-- Sheet Data -->
                <div class="data-display card">
                  <div class="data-header">
                    <h5>Trade Data</h5>
                    <div class="data-actions">
                      <Button
                        :label="`Calculate Portfolio (${getSheetData(sheetName).length} trades)`"
                        icon="pi pi-calculator"
                        @click="calculatePortfolio(sheetName)"
                        :loading="isCalculating[sheetName]"
                        :disabled="isCalculating[sheetName]"
                        class="p-button-primary"
                      />
                    </div>
                  </div>

                  <SimpleTable
                    :data="getSheetData(sheetName)"
                    :downloadFileName="`${sheetName}_portfolio_data`"
                  />
                </div>

                <!-- Results Display -->
                <div v-if="getSheetResults(sheetName)" class="results-display">
                  <div class="results-header">
                    <h5>Calculation Results</h5>
                  </div>

                  <!-- Summary Metrics -->
                  <div class="grid mb-4">
                    <div class="col-12 md:col-6 lg:col-3">
                      <div class="metric-card">
                        <div class="metric-label">Total Trades</div>
                        <div class="metric-value">
                          {{ getSheetSummary(sheetName).trade_count }}
                        </div>
                      </div>
                    </div>
                    <div class="col-12 md:col-6 lg:col-3">
                      <div class="metric-card success">
                        <div class="metric-label">Successful</div>
                        <div class="metric-value">
                          {{ getSheetSummary(sheetName).successful_trades }}
                        </div>
                      </div>
                    </div>
                    <div class="col-12 md:col-6 lg:col-3">
                      <div
                        class="metric-card"
                        :class="{
                          error: getSheetSummary(sheetName).failed_trades > 0
                        }"
                      >
                        <div class="metric-label">Failed</div>
                        <div class="metric-value">
                          {{ getSheetSummary(sheetName).failed_trades }}
                        </div>
                      </div>
                    </div>
                    <div class="col-12 md:col-6 lg:col-3">
                      <div class="metric-card primary">
                        <div class="metric-label">Portfolio NPV</div>
                        <div class="metric-value">
                          {{
                            formatCurrency(
                              getSheetSummary(sheetName).portfolio_npv
                            )
                          }}
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Detailed Results Table -->
                  <div class="results-table">
                    <h6>Trade-Level Results</h6>
                    <SimpleTable
                      :data="getSheetResults(sheetName).trade_results || []"
                      :downloadFileName="`${sheetName}_portfolio_results`"
                    />
                  </div>
                </div>
              </div>
            </TabPanel>
          </TabView>
        </div>

        <!-- Empty State -->
        <div v-if="!hasPortfolioData && !isUploading" class="empty-state">
          <div class="empty-state-content">
            <i class="pi pi-upload empty-state-icon"></i>
            <h3>Upload Portfolio Data</h3>
            <p>
              Select an Excel file containing your portfolio data to get started
              with portfolio pricing. Each sheet should contain trades of the
              same type.
            </p>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.portfolio-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
}

.upload-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  background: var(--surface-ground);
}

.upload-section h4 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  color: var(--primary-color);
  font-weight: 600;
}

.upload-description {
  margin-bottom: 1rem;
  color: var(--text-color-secondary);
  line-height: 1.5;
}

.upload-controls {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.selected-file-info {
  padding: 0.5rem;
  background: var(--surface-50);
  border-radius: 4px;
  border-left: 3px solid var(--primary-color);
}

.portfolio-data-section {
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--surface-border);
}

.section-header h4 {
  margin: 0;
  color: var(--primary-color);
  font-weight: 600;
}

.sheet-content {
  padding: 1rem 0;
}

.data-display {
  margin-bottom: 2rem;
}

.data-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.data-header h5 {
  margin: 0;
  color: var(--text-color);
  font-weight: 600;
}

.results-display {
  margin-top: 2rem;
  padding: 1.5rem;
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  background: var(--surface-0);
}

.results-header {
  margin-bottom: 1.5rem;
}

.results-header h5 {
  margin: 0;
  color: var(--text-color);
  font-weight: 600;
  font-size: 1.25rem;
}

.metric-card {
  padding: 1.5rem;
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  background: var(--surface-50);
  text-align: center;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
  height: 100%;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-card.primary {
  background: linear-gradient(
    135deg,
    var(--primary-50) 0%,
    var(--primary-100) 100%
  );
  border-color: var(--primary-200);
}

.metric-card.success {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  border-color: #86efac;
}

.metric-card.error {
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  border-color: #fca5a5;
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
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-color);
  line-height: 1.2;
}

.primary .metric-value {
  color: var(--primary-700);
}

.success .metric-value {
  color: #16a34a;
}

.error .metric-value {
  color: #dc2626;
}

.results-table {
  margin-top: 1.5rem;
}

.results-table h6 {
  margin: 0 0 1rem 0;
  color: var(--text-color);
  font-weight: 600;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  padding: 2rem;
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

/* Responsive Design */
@media (max-width: 768px) {
  .upload-controls {
    justify-content: stretch;
  }

  .data-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .data-actions .p-button {
    width: 100%;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .portfolio-container {
    padding: 0.5rem;
  }

  .metric-value {
    font-size: 1.25rem;
  }

  .selection-controls {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .selection-controls .p-button {
    width: 100%;
  }

  .progress-items {
    grid-template-columns: 1fr;
  }

  .batch-controls {
    padding: 0.75rem;
  }

  .tab-header {
    font-size: 0.875rem;
  }
}

/* Batch Controls Styles */
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
  margin-bottom: 1rem;
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

.batch-progress {
  margin-top: 1rem;
  padding: 1rem;
  border: 1px solid var(--surface-border);
  border-radius: 4px;
  background: var(--surface-0);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--surface-border);
}

.progress-title {
  font-weight: 600;
  color: var(--text-color);
}

.overall-progress {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
  font-weight: 500;
}

.progress-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 0.5rem;
}

.progress-item {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border-radius: 4px;
  background: var(--surface-50);
  transition: background-color 0.2s ease;
}

.progress-item.pending {
  background: var(--orange-50);
  color: var(--orange-700);
}

.progress-item.calculating {
  background: var(--blue-50);
  color: var(--blue-700);
}

.progress-item.completed {
  background: var(--green-50);
  color: var(--green-700);
}

.progress-item.failed {
  background: var(--red-50);
  color: var(--red-700);
}

.progress-icon {
  margin-right: 0.5rem;
  font-size: 0.875rem;
}

.sheet-name {
  font-weight: 500;
  margin-right: 0.5rem;
}

.status-text {
  font-size: 0.875rem;
  opacity: 0.8;
  margin-left: auto;
}

/* Tab Header Styles */
.tab-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-icon {
  font-size: 0.875rem;
}

/* Loading States */
.p-fileupload-basic {
  display: inline-block;
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
</style>
