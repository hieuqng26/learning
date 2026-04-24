<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'
import Button from 'primevue/button'
import SimpleTable from '@/components/Table/SimpleTable.vue'
import * as Plotly from 'plotly.js-dist'

const toast = useToast()

const props = defineProps({
  selectedFilters: {
    type: Object,
    required: true
  },
  tableData: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update-filters', 'apply-filters', 'clear-filters'])

const plotContainer = ref(null)

// FXVOL specific filters
const filters = {
  Name: {
    values: ['EURUSD.FXVOLSURFACE', 'USDZAR.FXVOLSURFACE'],
    type: 'dropdown'
  },
  Date: {
    values: ['2024-12-31'],
    type: 'dropdown'
  }
}

// Computed property to check if any filters are selected
const hasActiveFilters = computed(() => {
  return Object.keys(props.selectedFilters).length > 0
})

// Computed property to determine if 3D plot should be shown
const showPlot = computed(() => {
  return (
    props.selectedFilters.Name &&
    props.selectedFilters.Date &&
    props.tableData.length > 0 &&
    !props.error
  )
})

// Function to parse tenor string to months (based on Python implementation)
const parseTenorToMonths = (tenorStr) => {
  const tenorMap = {
    '1D': 1 / 30,
    '1W': 1 / 4,
    '2W': 0.5,
    '3W': 0.75,
    '1M': 1,
    '2M': 2,
    '3M': 3,
    '4M': 4,
    '5M': 5,
    '6M': 6,
    '9M': 9,
    '1Y': 12,
    '18M': 18,
    '2Y': 24,
    '3Y': 36,
    '4Y': 48,
    '5Y': 60,
    '7Y': 84,
    '10Y': 120
  }
  return tenorMap[tenorStr] || 0
}

// Function to generate 3D volatility surface plot
const generateVolatilitySurface = async () => {
  if (!plotContainer.value) return
  try {
    // Define strikes and their delta values (based on Python implementation)
    const strikes = ['Put10', 'Put25', 'ATM', 'Call25', 'Call10']
    const strikeValues = [-0.1, -0.25, 0.0, 0.25, 0.1]

    // Process table data to extract volatility information
    const processedData = props.tableData
      .map((row) => {
        const tenorMonths = parseTenorToMonths(
          row.FXVOLSURFACE || row.Tenor || ''
        )
        return {
          ...row,
          months: tenorMonths
        }
      })
      .filter((row) => row.months > 0)

    // Get unique tenors and sort them
    const tenors = [...new Set(processedData.map((row) => row.months))].sort(
      (a, b) => a - b
    )

    // Create meshgrid
    const X = []
    const Y = []
    const Z = []

    for (let j = 0; j < tenors.length; j++) {
      const xRow = []
      const yRow = []
      const zRow = []

      for (let k = 0; k < strikes.length; k++) {
        xRow.push(strikeValues[k])
        yRow.push(tenors[j])

        // Find volatility value for this tenor and strike
        const dataPoint = processedData.find((row) => row.months === tenors[j])
        let volValue = 0

        if (dataPoint && dataPoint[strikes[k]] !== undefined) {
          volValue = parseFloat(dataPoint[strikes[k]]) || 0
        }

        zRow.push(volValue)
      }

      X.push(xRow)
      Y.push(yRow)
      Z.push(zRow)
    }

    // Create the 3D surface plot
    const trace = {
      type: 'surface',
      x: X,
      y: Y,
      z: Z,
      colorscale: 'Viridis',
      showscale: true,
      hovertemplate:
        '<b>Strike:</b> %{x}<br>' +
        '<b>Months:</b> %{y}<br>' +
        '<b>Volatility:</b> %{z:.4f}<extra></extra>',
      name: `${props.selectedFilters.Name} Volatility Surface`
    }

    const layout = {
      title: {
        text: `${props.selectedFilters.Name}`,
        font: { size: 16 }
      },
      scene: {
        xaxis: {
          title: {
            text: 'Delta Strike',
            font: { size: 14 }
          }
        },
        yaxis: {
          title: {
            text: 'Months to Maturity',
            font: { size: 14 }
          }
        },
        zaxis: {
          title: {
            text: 'Implied Volatility',
            font: { size: 14 }
          }
        },
        camera: {
          eye: { x: 1.5, y: 1.5, z: 1.5 }
        }
      },
      autosize: true,
      height: 600,
      margin: { l: 0, r: 0, t: 50, b: 0 }
    }

    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
      toImageButtonOptions: {
        format: 'png',
        filename: `${props.selectedFilters.Name}_volsurface`,
        height: 600,
        width: 1000,
        scale: 2
      }
    }

    await Plotly.newPlot(plotContainer.value, [trace], layout, config)
  } catch (err) {
    toast.add({
      severity: 'info',
      summary: 'Error',
      detail: 'Failed to generate plot: ' + err,
      life: 3000
    })
  }
}

// Update filters handler
const updateFilter = (filterName, value) => {
  const updatedFilters = { ...props.selectedFilters }
  updatedFilters[filterName] = value
  emit('update-filters', updatedFilters)
}

// Clear filters handler
const clearFilters = () => {
  emit('clear-filters')
}

// Apply filters handler
const applyFilters = () => {
  emit('apply-filters')
}

// Watch for data changes to regenerate plot
watch(() => [showPlot.value, props.tableData], async () => {
  if (showPlot.value) {
    await nextTick()
    await generateVolatilitySurface()
  }
}, { deep: true })
</script>

<template>
  <!-- FX Volatility Filters Section -->
  <div class="card">
    <div class="flex justify-content-between align-items-center mb-3 pb-2 border-bottom-1 surface-border">
      <h5 class="m-0 text-color">FX Volatility Filters</h5>
      <div class="flex gap-2">
        <Button
          v-if="hasActiveFilters"
          label="Clear Filters"
          icon="pi pi-times"
          severity="secondary"
          size="small"
          @click="clearFilters"
        />
        <Button
          label="Apply Filters"
          icon="pi pi-check"
          size="small"
          :loading="loading"
          @click="applyFilters"
        />
      </div>
    </div>

    <div class="grid mb-3">
      <div
        v-for="(filterOptions, filterName) in filters"
        :key="filterName"
        class="col-12 md:col-3"
      >
        <label :for="filterName.toLowerCase()" class="block mb-2 font-semibold">{{ filterName }}</label>

        <!-- Multi-select for filters with multiple options -->
        <MultiSelect
          v-if="filterOptions.type === 'multiselect'"
          :id="filterName.toLowerCase()"
          :modelValue="selectedFilters[filterName]"
          :options="filterOptions.values"
          :placeholder="`Select ${filterName}`"
          :maxSelectedLabels="2"
          class="w-full"
          @update:modelValue="updateFilter(filterName, $event)"
        />

        <!-- Single select dropdown for filters with few options -->
        <Dropdown
          v-else
          :id="filterName.toLowerCase()"
          :modelValue="selectedFilters[filterName]"
          :options="filterOptions.values.map((opt) => ({ label: opt, value: opt }))"
          optionLabel="label"
          optionValue="value"
          :placeholder="`Select ${filterName}`"
          :showClear="true"
          class="w-full"
          @update:modelValue="updateFilter(filterName, $event)"
        />
      </div>
    </div>
  </div>

  <!-- Data Table -->
  <div class="card">
    <div v-if="loading" class="flex flex-column align-items-center justify-content-center p-4 text-center text-color-secondary">
      <i class="pi pi-spin pi-spinner text-4xl"></i>
      <p class="mt-3 mb-3">Loading FX volatility data...</p>
    </div>

    <div v-else-if="error" class="flex flex-column align-items-center justify-content-center p-4 text-center text-red-500">
      <i class="pi pi-exclamation-triangle text-4xl"></i>
      <p class="mt-3 mb-3">{{ error }}</p>
      <Button
        label="Retry"
        icon="pi pi-refresh"
        severity="secondary"
        size="small"
        @click="applyFilters"
      />
    </div>

    <SimpleTable
      v-else
      :data="tableData"
      downloadFileName="fx_volatility_data"
    />
  </div>

  <!-- 3D Volatility Surface Plot -->
  <div v-if="showPlot" class="card">
    <div class="flex justify-content-between align-items-center mb-3 pb-2 border-bottom-1 surface-border">
      <h5 class="m-0 text-color">3D Volatility Surface</h5>
    </div>
    <div ref="plotContainer" class="volatility-plot-container"></div>
  </div>
</template>

<style scoped>
.volatility-plot-container {
  width: 100%;
  height: 600px;
  min-height: 400px;
}
</style>