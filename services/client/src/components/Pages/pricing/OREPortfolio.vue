<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useToast } from 'primevue/usetoast'
import PortfolioInputSection from './components/PortfolioInputSection.vue'
import PortfolioResultsSection from './components/PortfolioResultsSection.vue'
import {
  transformSensitivityData,
  validateSensitivityConfig
} from '@/forms/shared/sensitivity-fields'

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
const portfolioData = ref(null)
const portfolioResults = ref(null)
const isUploading = ref(false)
const isCalculating = ref(false)

// Sheet selection and configuration state
const selectedSheets = ref([])
const nettingSetsData = ref(null)
const sensitivityFormData = ref({
  sensitivity_entries: []
})

// Scenario configuration state
const scenarioConfigData = ref(null)

// Computed properties
const hasPortfolioData = computed(() => {
  return portfolioData.value && Object.keys(portfolioData.value).length > 0
})

const hasResults = computed(() => {
  return portfolioResults.value !== null
})

// Event handlers for child component events
const handlePortfolioUploaded = (data) => {
  portfolioData.value = data
}

const handleNettingSetsUpdated = (data) => {
  nettingSetsData.value = data
}

const handleScenarioDataUpdated = (data) => {
  scenarioConfigData.value = data
}

const calculatePortfolio = async () => {
  try {
    isCalculating.value = true
    portfolioResults.value = null

    // Get sheet data helper
    const getSheetData = (sheetName) => {
      if (!portfolioData.value || !portfolioData.value[sheetName]) return []
      return JSON.parse(portfolioData.value[sheetName])
    }

    // Calculate trade count for toast message
    let tradeCount = 0
    selectedSheets.value.forEach((sheetName) => {
      if (sheetName !== 'NettingSets') {
        tradeCount += getSheetData(sheetName).length
      }
    })

    toast.add({
      severity: 'info',
      summary: 'Calculating Portfolio',
      detail: `Pricing ${tradeCount} trades from ${selectedSheets.value.length} sheet(s)...`,
      life: 3000
    })

    // Collect all trades from selected sheets (exclude NettingSets)
    const tradesData = {}
    selectedSheets.value.forEach((sheetName) => {
      if (sheetName !== 'NettingSets') {
        tradesData[sheetName] = getSheetData(sheetName)
      }
    })

    // Get evaluation date from first trade
    let evaluationDate = new Date().toISOString().split('T')[0]
    const firstSheet = selectedSheets.value[0]
    const firstData = getSheetData(firstSheet)
    if (firstData.length > 0) {
      if (firstData[0].EvaluationDate) {
        evaluationDate = firstData[0].EvaluationDate
      } else if (firstData[0].evaluation_date) {
        evaluationDate = firstData[0].evaluation_date
      }
    }

    // Validate sensitivity configuration
    const sensitivityValidation = validateSensitivityConfig(
      sensitivityFormData.value
    )
    if (!sensitivityValidation.valid) {
      toast.add({
        severity: 'error',
        summary: 'Sensitivity Configuration Error',
        detail: sensitivityValidation.errors.join('. '),
        life: 5000
      })
      isCalculating.value = false
      return
    }

    const payload = {
      evaluation_date: evaluationDate,
      trades: tradesData,
      sensitivity_config: transformSensitivityData(sensitivityFormData.value),
      scenario_config: scenarioConfigData.value
    }

    // Include netting_sets if available
    if (nettingSetsData.value && nettingSetsData.value.length > 0) {
      payload.netting_sets = nettingSetsData.value
    }

    const response = await store.dispatch('calculateOREPortfolio', payload)

    portfolioResults.value = response.data

    toast.add({
      severity: 'success',
      summary: 'Calculation Complete',
      detail: `Portfolio calculated successfully with ${response.data.trade_count} trades`,
      life: 3000
    })
  } catch (error) {
    console.error('Calculation error:', error)
    toast.add({
      severity: 'error',
      summary: 'Calculation Failed',
      detail: error.response?.data?.message || 'Failed to calculate portfolio',
      life: 5000
    })
  } finally {
    isCalculating.value = false
  }
}

// Watchers
watch(hasPortfolioData, (newValue) => {
  if (newValue) {
    // Auto-select all sheets when data is loaded
    const portfolioSheets = Object.keys(portfolioData.value)
    selectedSheets.value = [...portfolioSheets]
  }
})
</script>

<template>
  <!-- Portfolio Input Section (includes file upload) -->
  <PortfolioInputSection
    :module="module"
    :submodule="submodule"
    :portfolio-data="portfolioData"
    :netting-sets-data="nettingSetsData"
    :scenario-config-data="scenarioConfigData"
    v-model:selected-sheets="selectedSheets"
    v-model:sensitivity-form-data="sensitivityFormData"
    v-model:is-uploading="isUploading"
    :is-calculating="isCalculating"
    @calculate="calculatePortfolio"
    @portfolio-uploaded="handlePortfolioUploaded"
    @netting-sets-updated="handleNettingSetsUpdated"
    @scenario-data-updated="handleScenarioDataUpdated"
  />

  <!-- Portfolio Results Section -->
  <PortfolioResultsSection
    v-if="hasResults"
    :portfolio-results="portfolioResults"
  />
</template>

<style scoped>
/* Parent component - minimal styles */
</style>
