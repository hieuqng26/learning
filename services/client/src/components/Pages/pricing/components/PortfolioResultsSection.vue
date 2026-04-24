<template>
  <div class="results-section">
    <div class="results-header">
      <h4>Portfolio Results</h4>
    </div>

    <!-- Analysis Tabs: Base, Sensitivity, Stress -->
    <TabView v-model:activeIndex="activeTabIndex">
      <!-- Base Analysis Tab -->
      <TabPanel>
        <template #header>
          <div class="flex align-items-center gap-2">
            <i class="pi pi-chart-line"></i>
            <span>Base Analysis</span>
          </div>
        </template>

        <div class="analysis-tab-content">
          <!-- NPV Section -->
          <div class="mb-2">
            <h5 class="section-title">Net Present Value (NPV)</h5>
            <div
              v-if="currentNPVData && currentNPVData.length > 0"
              class="npv-table"
            >
              <SimpleTable
                :data="currentNPVData"
                :downloadFileName="`ore_portfolio_base_npv`"
              />
            </div>
            <div v-else class="empty-state-message">
              <i class="pi pi-info-circle"></i>
              <span>No NPV data available</span>
            </div>
          </div>

          <!-- Exposure Section -->
          <div class="mt-2">
            <div class="flex justify-content-between align-items-center mb-3">
              <h5 class="section-title">Expected Exposure (EE)</h5>
              <div class="flex gap-2">
                <FormDropdown
                  v-model="selectedExposureLevel"
                  :options="exposureLevelOptions"
                  option-label="label"
                  option-value="value"
                  placeholder="Select Level"
                  class="w-auto"
                  style="min-width: 180px"
                />
                <FormDropdown
                  v-if="
                    selectedExposureLevel !== 'portfolio' &&
                    availableEntityIds.length > 0
                  "
                  v-model="selectedEntityId"
                  :options="availableEntityIds"
                  option-label="label"
                  option-value="value"
                  :placeholder="
                    selectedExposureLevel === 'trade'
                      ? 'Select Trade'
                      : 'Select Netting Set'
                  "
                  class="w-auto"
                  style="min-width: 200px"
                />
              </div>
            </div>

            <div class="mt-1">
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
                        dateFormat="yy-mm-dd"
                        showIcon
                        showButtonBar
                      />
                    </div>
                    <div class="flex align-items-center gap-2 w-5">
                      <label class="text-sm font-medium">To:</label>
                      <Calendar
                        v-model="exposureEndDate"
                        dateFormat="yy-mm-dd"
                        showIcon
                        showButtonBar
                      />
                    </div>
                  </div>
                </div>
              </Panel>

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
              <div
                v-else-if="
                  !currentExposureData || currentExposureData.length === 0
                "
                class="chart-empty-state"
              >
                <i class="pi pi-info-circle"></i>
                <span
                  >No exposure data available for
                  {{ selectedExposureLevel }} level</span
                >
              </div>
              <div v-else class="chart-empty-state">
                <i class="pi pi-chart-line"></i>
                <span>Select at least one series to display the chart</span>
              </div>
            </div>
          </div>
        </div>
      </TabPanel>

      <!-- Stress Analysis Tab -->
      <TabPanel>
        <template #header>
          <div class="flex align-items-center gap-2">
            <i class="pi pi-sliders-h"></i>
            <span>Stress Analysis</span>
          </div>
        </template>

        <div class="analysis-tab-content">
          <!-- NPV Section -->
          <div class="mb-2">
            <h5 class="section-title">Net Present Value (NPV)</h5>
            <div
              v-if="currentNPVData && currentNPVData.length > 0"
              class="npv-table"
            >
              <SimpleTable
                :data="currentNPVData"
                :downloadFileName="`ore_portfolio_sensitivity_npv`"
              />
            </div>
            <div v-else class="empty-state-message">
              <i class="pi pi-info-circle"></i>
              <span>No sensitivity NPV data available</span>
            </div>
          </div>

          <!-- Exposure Section -->
          <div class="mt-2">
            <div class="flex justify-content-between align-items-center mb-3">
              <h5 class="section-title">Expected Exposure (EE)</h5>
              <div class="flex gap-2">
                <FormDropdown
                  v-model="selectedExposureLevel"
                  :options="exposureLevelOptions"
                  option-label="label"
                  option-value="value"
                  placeholder="Select Level"
                  class="w-auto"
                  style="min-width: 180px"
                />
                <FormDropdown
                  v-if="
                    selectedExposureLevel !== 'portfolio' &&
                    availableEntityIds.length > 0
                  "
                  v-model="selectedEntityId"
                  :options="availableEntityIds"
                  option-label="label"
                  option-value="value"
                  :placeholder="
                    selectedExposureLevel === 'trade'
                      ? 'Select Trade'
                      : 'Select Netting Set'
                  "
                  class="w-auto"
                  style="min-width: 200px"
                />
              </div>
            </div>

            <div class="mt-1">
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
                        dateFormat="yy-mm-dd"
                        showIcon
                        showButtonBar
                      />
                    </div>
                    <div class="flex align-items-center gap-2 w-5">
                      <label class="text-sm font-medium">To:</label>
                      <Calendar
                        v-model="exposureEndDate"
                        dateFormat="yy-mm-dd"
                        showIcon
                        showButtonBar
                      />
                    </div>
                  </div>
                </div>
              </Panel>

              <div
                v-if="currentExposureData && exposureChartData"
                class="chart-container"
              >
                <LineChart
                  :data="exposureChartData"
                  title="Expected Exposure"
                  x-title="Date"
                  y-title="Mark-to-Market"
                  y-label="$"
                />
              </div>
              <div
                v-else-if="
                  !currentExposureData || currentExposureData.length === 0
                "
                class="chart-empty-state"
              >
                <i class="pi pi-info-circle"></i>
                <span
                  >No sensitivity exposure data available for
                  {{ selectedExposureLevel }} level</span
                >
              </div>
              <div v-else class="chart-empty-state">
                <i class="pi pi-chart-line"></i>
                <span
                  >Select at least one risk factor to display the chart</span
                >
              </div>
            </div>
          </div>
        </div>
      </TabPanel>

      <!-- Scenario Analysis Tab -->
      <TabPanel>
        <template #header>
          <div class="flex align-items-center gap-2">
            <i class="pi pi-bolt"></i>
            <span>Scenario Analysis</span>
          </div>
        </template>

        <div class="analysis-tab-content">
          <!-- NPV Section -->
          <div class="mb-2">
            <h5 class="section-title">Net Present Value (NPV)</h5>
            <div
              v-if="currentNPVData && currentNPVData.length > 0"
              class="npv-table"
            >
              <SimpleTable
                :data="currentNPVData"
                :downloadFileName="`ore_portfolio_stress_npv`"
              />
            </div>
            <div v-else class="empty-state-message">
              <i class="pi pi-info-circle"></i>
              <span>No stress NPV data available</span>
            </div>
          </div>

          <!-- Exposure Section -->
          <div class="mt-2">
            <div class="flex justify-content-between align-items-center mb-3">
              <h5 class="section-title">Expected Exposure (EE)</h5>
              <div class="flex gap-2">
                <FormDropdown
                  v-model="selectedExposureLevel"
                  :options="exposureLevelOptions"
                  option-label="label"
                  option-value="value"
                  placeholder="Select Level"
                  class="w-auto"
                  style="min-width: 180px"
                />
                <FormDropdown
                  v-if="
                    selectedExposureLevel !== 'portfolio' &&
                    availableEntityIds.length > 0
                  "
                  v-model="selectedEntityId"
                  :options="availableEntityIds"
                  option-label="label"
                  option-value="value"
                  :placeholder="
                    selectedExposureLevel === 'trade'
                      ? 'Select Trade'
                      : 'Select Netting Set'
                  "
                  class="w-auto"
                  style="min-width: 200px"
                />
              </div>
            </div>

            <div class="mt-1">
              <Panel header="Filters" toggleable collapsed class="mb-3">
                <div
                  class="flex align-items-center justify-content-between gap-2 mb-3"
                >
                  <MultiSelect
                    v-model="selectedMetricColumns"
                    :options="availableMetricColumns"
                    option-label="label"
                    placeholder="Select stress scenarios to display"
                    class="w-3"
                  />
                  <div class="flex justify-content-end gap-2">
                    <div class="flex align-items-center gap-2 w-5">
                      <label class="text-sm font-medium">From:</label>
                      <Calendar
                        v-model="exposureStartDate"
                        dateFormat="yy-mm-dd"
                        showIcon
                        showButtonBar
                      />
                    </div>
                    <div class="flex align-items-center gap-2 w-5">
                      <label class="text-sm font-medium">To:</label>
                      <Calendar
                        v-model="exposureEndDate"
                        dateFormat="yy-mm-dd"
                        showIcon
                        showButtonBar
                      />
                    </div>
                  </div>
                </div>
              </Panel>

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
              <div
                v-else-if="
                  !currentExposureData || currentExposureData.length === 0
                "
                class="chart-empty-state"
              >
                <i class="pi pi-info-circle"></i>
                <span
                  >No stress exposure data available for
                  {{ selectedExposureLevel }} level</span
                >
              </div>
              <div v-else class="chart-empty-state">
                <i class="pi pi-chart-line"></i>
                <span
                  >Select at least one stress scenario to display the chart</span
                >
              </div>
            </div>
          </div>

          <!-- NPV Comparison Dot Plot Section -->
          <div class="npv-dotplot-section mt-4">
            <div class="flex justify-content-between align-items-center mb-3">
              <h5 class="section-title">Mark-to-Market (MtM)</h5>
              <div class="flex gap-2">
                <FormDropdown
                  v-if="availableStressScenarios.length > 0"
                  v-model="selectedStressScenario"
                  :options="availableStressScenarios"
                  option-label="label"
                  option-value="value"
                  placeholder="Select Stress Scenario"
                  class="w-auto"
                  style="min-width: 250px"
                />
              </div>
            </div>

            <div class="npv-dotplot-view">
              <div
                v-if="npvDotPlotData && selectedStressScenario"
                class="chart-container"
              >
                <ScatterChart
                  :data="npvDotPlotData"
                  title="MtM: Base vs Stress Scenario"
                  x-title="Maturity Date"
                  y-title="MtM (EUR)"
                  y-label="€"
                />
              </div>
              <div
                v-else-if="!selectedStressScenario"
                class="chart-empty-state"
              >
                <i class="pi pi-info-circle"></i>
                <span>Select a stress scenario to compare NPV</span>
              </div>
              <div v-else class="chart-empty-state">
                <i class="pi pi-chart-scatter"></i>
                <span>No NPV data available for comparison</span>
              </div>
            </div>
          </div>
        </div>
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import SimpleTable from '@/components/Table/SimpleTable.vue'
import LineChart from '@/components/Charts/LineChart.vue'
import ScatterChart from '@/components/Charts/ScatterChart.vue'
import FormDropdown from '@/components/Form/FormDropdown.vue'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Panel from 'primevue/panel'
import MultiSelect from 'primevue/multiselect'
import Calendar from 'primevue/calendar'

// Props
const props = defineProps({
  portfolioResults: {
    type: Object,
    required: true
  }
})

// State
const activeTabIndex = ref(0)
const selectedAnalysisType = ref('base') // 'base', 'sensitivity', 'stress'

const selectedExposureLevel = ref('trade')
const exposureLevelOptions = [
  { label: 'Trade Level', value: 'trade' },
  { label: 'Netting Set Level', value: 'nettingset' },
  { label: 'Portfolio Level', value: 'portfolio' }
]

const selectedEntityId = ref(null)
const selectedMetricColumns = ref([])
const exposureStartDate = ref(null)
const exposureEndDate = ref(null)
const selectedStressScenario = ref(null)

// Computed - Get current analysis section
const currentAnalysisData = computed(() => {
  if (!props.portfolioResults) return null
  return props.portfolioResults[selectedAnalysisType.value]
})

// Get NPV data
const currentNPVData = computed(() => {
  if (!currentAnalysisData.value?.npv) return []

  const npvData = currentAnalysisData.value.npv

  try {
    return typeof npvData === 'string' ? JSON.parse(npvData) : npvData
  } catch (e) {
    console.error('Failed to parse NPV data:', e)
    return []
  }
})

// Base NPV data (for comparison in stress tab)
const baseNPVData = computed(() => {
  if (!props.portfolioResults?.base?.npv) return []

  const npvData = props.portfolioResults.base.npv
  try {
    return typeof npvData === 'string' ? JSON.parse(npvData) : npvData
  } catch (e) {
    console.error('Failed to parse base NPV data:', e)
    return []
  }
})

// Get exposure data for current level
const currentExposureData = computed(() => {
  if (!currentAnalysisData.value?.exposures) return []

  const exposureLevel =
    currentAnalysisData.value.exposures[selectedExposureLevel.value]
  if (!exposureLevel) return []

  try {
    let data =
      typeof exposureLevel === 'string'
        ? JSON.parse(exposureLevel)
        : exposureLevel

    // Filter by selected entity ID if at trade or nettingset level
    if (selectedEntityId.value && data && data.length > 0) {
      if (selectedExposureLevel.value === 'trade') {
        data = data.filter((row) => row.TradeId === selectedEntityId.value)
      } else if (selectedExposureLevel.value === 'nettingset') {
        data = data.filter((row) => row.NettingSet === selectedEntityId.value)
      }
    }

    return data
  } catch (e) {
    console.error('Failed to parse exposure data:', e)
    return []
  }
})

// Get available entity IDs
const availableEntityIds = computed(() => {
  if (!currentAnalysisData.value?.exposures) return []

  const exposureLevel =
    currentAnalysisData.value.exposures[selectedExposureLevel.value]
  if (!exposureLevel) return []

  try {
    const data =
      typeof exposureLevel === 'string'
        ? JSON.parse(exposureLevel)
        : exposureLevel

    if (!data || data.length === 0) return []

    let ids = []
    if (selectedExposureLevel.value === 'trade') {
      ids = [...new Set(data.map((row) => row.TradeId).filter((id) => id))]
    } else if (selectedExposureLevel.value === 'nettingset') {
      ids = [...new Set(data.map((row) => row.NettingSet).filter((id) => id))]
    }

    return ids.sort().map((id) => ({ label: id, value: id }))
  } catch (e) {
    console.error('Failed to parse exposure data for entity IDs:', e)
    return []
  }
})

// Get available stress scenarios
const availableStressScenarios = computed(() => {
  if (!props.portfolioResults?.stress?.npv) return []

  const stressNPVData = props.portfolioResults.stress.npv
  try {
    const parsed =
      typeof stressNPVData === 'string'
        ? JSON.parse(stressNPVData)
        : stressNPVData
    if (!parsed || parsed.length === 0) return []

    const scenarios = [...new Set(parsed.map((row) => row.Scenario))]
      .filter((s) => s)
      .sort()

    return scenarios.map((scenario) => ({ label: scenario, value: scenario }))
  } catch (e) {
    console.error('Failed to parse stress scenarios:', e)
    return []
  }
})

// Available metric columns
const availableMetricColumns = computed(() => {
  if (!currentExposureData.value || currentExposureData.value.length === 0)
    return []

  const firstRow = currentExposureData.value[0]

  // For base: Create EE columns (EPE + ENE)
  if (selectedAnalysisType.value === 'base') {
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
  if (selectedAnalysisType.value === 'sensitivity') {
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
  if (selectedAnalysisType.value === 'stress') {
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

// Build chart for Base exposures
const buildBaseExposureChart = () => {
  let exposures = currentExposureData.value
  if (!exposures || exposures.length === 0) return null

  // Apply date filtering
  const startDate = exposureStartDate.value
  const endDate = exposureEndDate.value
  if (startDate || endDate) {
    exposures = exposures.filter((row) => {
      const rowDate = new Date(row.Date)
      if (startDate && rowDate < startDate) return false
      if (endDate && rowDate > endDate) return false
      return true
    })
  }

  if (exposures.length === 0) return null

  const metricColumns = selectedMetricColumns.value
  if (metricColumns.length === 0) return null

  // Create datasets for EE (EPE + ENE)
  const datasets = metricColumns.map((columnConfig, index) => {
    const colors = [
      '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    const color = colors[index % colors.length]

    const eeData = exposures.map((exp) => {
      const epe = exp[columnConfig.epeColumn] || 0
      const ene = exp[columnConfig.eneColumn] || 0
      return epe + ene
    })

    return {
      label: columnConfig.label,
      data: eeData,
      borderColor: color,
      backgroundColor: 'transparent',
      borderWidth: 2.5,
      fill: false,
      tension: 0.1,
      pointRadius: 0,
      pointHoverRadius: 4
    }
  })

  return {
    labels: exposures.map((exp) => exp.Date),
    datasets: datasets
  }
}

// Build chart for Sensitivity exposures
const buildSensitivityExposureChart = () => {
  let data = currentExposureData.value
  if (!data || data.length === 0) return null

  // Apply date filtering
  const startDate = exposureStartDate.value
  const endDate = exposureEndDate.value
  if (startDate || endDate) {
    data = data.filter((row) => {
      const rowDate = new Date(row.Date)
      if (startDate && rowDate < startDate) return false
      if (endDate && rowDate > endDate) return false
      return true
    })
  }

  if (data.length === 0) return null

  const selectedCombos = selectedMetricColumns.value
  if (selectedCombos.length === 0) return null

  // Group by date
  const dateMap = new Map()
  data.forEach((row) => {
    if (!dateMap.has(row.Date)) dateMap.set(row.Date, [])
    dateMap.get(row.Date).push(row)
  })

  const sortedDates = Array.from(dateMap.keys()).sort()

  // Create datasets
  const datasets = selectedCombos.map((combo, index) => {
    const [type, factor] = combo.value.split('|')
    const colors = [
      '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    const color = colors[index % colors.length]

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
      label: combo.label,
      data: dataPoints,
      borderColor: color,
      backgroundColor: 'transparent',
      borderWidth: 2.5,
      fill: false,
      tension: 0.1,
      pointRadius: 0,
      pointHoverRadius: 4
    }
  })

  return { labels: sortedDates, datasets }
}

// Build chart for Stress exposures
const buildStressExposureChart = () => {
  let data = currentExposureData.value
  if (!data || data.length === 0) return null

  // Apply date filtering
  const startDate = exposureStartDate.value
  const endDate = exposureEndDate.value
  if (startDate || endDate) {
    data = data.filter((row) => {
      const rowDate = new Date(row.Date)
      if (startDate && rowDate < startDate) return false
      if (endDate && rowDate > endDate) return false
      return true
    })
  }

  if (data.length === 0) return null

  const selectedScenarios = selectedMetricColumns.value
  if (selectedScenarios.length === 0) return null

  // Group by date
  const dateMap = new Map()
  data.forEach((row) => {
    if (!dateMap.has(row.Date)) dateMap.set(row.Date, [])
    dateMap.get(row.Date).push(row)
  })

  const sortedDates = Array.from(dateMap.keys()).sort()

  // Create datasets
  const datasets = selectedScenarios.map((scenarioConfig, index) => {
    const scenario = scenarioConfig.value
    const colors = [
      '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    const color = colors[index % colors.length]

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
      borderColor: color,
      backgroundColor: 'transparent',
      borderWidth: 2.5,
      fill: false,
      tension: 0.1,
      pointRadius: 0,
      pointHoverRadius: 4
    }
  })

  return { labels: sortedDates, datasets }
}

// Main chart data
const exposureChartData = computed(() => {
  if (!currentExposureData.value || currentExposureData.value.length === 0)
    return null

  if (selectedAnalysisType.value === 'base') return buildBaseExposureChart()
  if (selectedAnalysisType.value === 'sensitivity')
    return buildSensitivityExposureChart()
  if (selectedAnalysisType.value === 'stress') return buildStressExposureChart()

  return null
})

// Aggregated NPV data by maturity for dot plot
const npvDotPlotData = computed(() => {
  if (selectedAnalysisType.value !== 'stress') return null
  if (!baseNPVData.value || baseNPVData.value.length === 0) return null
  if (!currentNPVData.value || currentNPVData.value.length === 0) return null
  if (!selectedStressScenario.value) return null

  // Create map of TradeId -> Maturity and NettingSet
  const tradeMaturityMap = new Map()
  const tradeNettingSetMap = new Map()
  baseNPVData.value.forEach((row) => {
    if (row.TradeId && row.Maturity) {
      tradeMaturityMap.set(row.TradeId, row.Maturity)
    }
    if (row.TradeId && row.NettingSet) {
      tradeNettingSetMap.set(row.TradeId, row.NettingSet)
    }
  })

  // Filter stress data by selected scenario
  let stressData = currentNPVData.value.filter(
    (row) => row.Scenario === selectedStressScenario.value
  )

  // Apply level filtering
  if (selectedExposureLevel.value === 'trade' && selectedEntityId.value) {
    stressData = stressData.filter(
      (row) => row.TradeId === selectedEntityId.value
    )
  } else if (
    selectedExposureLevel.value === 'nettingset' &&
    selectedEntityId.value
  ) {
    stressData = stressData.filter((row) => {
      const nettingSet = tradeNettingSetMap.get(row.TradeId)
      return nettingSet === selectedEntityId.value
    })
  }

  // Aggregate by maturity date
  const baseMaturityMap = new Map()
  const stressMaturityMap = new Map()

  stressData.forEach((row) => {
    const maturity = tradeMaturityMap.get(row.TradeId)
    if (!maturity) return

    const baseNPV = parseFloat(row['Base NPV']) || 0
    const scenarioNPV = parseFloat(row['Scenario NPV']) || 0

    if (!baseMaturityMap.has(maturity)) {
      baseMaturityMap.set(maturity, 0)
    }
    if (!stressMaturityMap.has(maturity)) {
      stressMaturityMap.set(maturity, 0)
    }

    baseMaturityMap.set(maturity, baseMaturityMap.get(maturity) + baseNPV)
    stressMaturityMap.set(
      maturity,
      stressMaturityMap.get(maturity) + scenarioNPV
    )
  })

  const basePoints = Array.from(baseMaturityMap.entries())
    .sort(([a], [b]) => new Date(a) - new Date(b))
    .map(([maturity, totalNPV]) => ({
      x: maturity,
      y: totalNPV
    }))

  const stressPoints = Array.from(stressMaturityMap.entries())
    .sort(([a], [b]) => new Date(a) - new Date(b))
    .map(([maturity, totalNPV]) => ({
      x: maturity,
      y: totalNPV
    }))

  return {
    datasets: [
      {
        label: 'Base NPV',
        data: basePoints,
        backgroundColor: 'rgba(31, 119, 180, 0.6)',
        borderColor: '#1f77b4',
        borderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointStyle: 'circle'
      },
      {
        label: `Stress NPV - ${selectedStressScenario.value}`,
        data: stressPoints,
        backgroundColor: 'rgba(214, 39, 40, 0.6)',
        borderColor: '#d62728',
        borderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        pointStyle: 'circle'
      }
    ]
  }
})

// Watchers
watch(activeTabIndex, (newIndex) => {
  const types = ['base', 'sensitivity', 'stress']
  selectedAnalysisType.value = types[newIndex]
})

watch(selectedAnalysisType, () => {
  selectedMetricColumns.value = []
  exposureStartDate.value = null
  exposureEndDate.value = null

  if (availableMetricColumns.value.length > 0) {
    selectedMetricColumns.value = [availableMetricColumns.value[0]]
  }

  // Auto-select first stress scenario when switching to stress tab
  if (
    selectedAnalysisType.value === 'stress' &&
    availableStressScenarios.value.length > 0 &&
    !selectedStressScenario.value
  ) {
    selectedStressScenario.value = availableStressScenarios.value[0].value
  }
})

watch(selectedExposureLevel, () => {
  selectedMetricColumns.value = []
  selectedEntityId.value = null

  if (availableMetricColumns.value.length > 0) {
    selectedMetricColumns.value = [availableMetricColumns.value[0]]
  }
})

watch(availableEntityIds, (newIds) => {
  if (newIds.length > 0 && !selectedEntityId.value) {
    selectedEntityId.value = newIds[0].value
  }
})

watch(availableMetricColumns, (newColumns) => {
  if (newColumns.length > 0 && selectedMetricColumns.value.length === 0) {
    selectedMetricColumns.value = [newColumns[0]]
  }
})

watch(availableStressScenarios, (newScenarios) => {
  if (newScenarios.length > 0 && !selectedStressScenario.value) {
    selectedStressScenario.value = newScenarios[0].value
  }
})
</script>

<style scoped>
.results-section {
  margin-top: 2rem;
  padding: 1.5rem;
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  background: var(--surface-0);
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

.analysis-tab-content {
  padding: 1rem 0;
}

.section-title {
  margin: 0 0 1rem 0;
  color: var(--text-color);
  font-weight: 600;
}

.npv-dotplot-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid var(--surface-border);
}

.npv-dotplot-view {
  margin-top: 1rem;
}

.npv-table {
  background: var(--surface-0);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 1rem;
}

.empty-state-message {
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

.empty-state-message i {
  font-size: 2rem;
  opacity: 0.5;
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

.chart-container {
  background: var(--surface-0);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

/* Responsive Design */
@media (max-width: 768px) {
  .chart-container {
    padding: 1rem;
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
</style>
