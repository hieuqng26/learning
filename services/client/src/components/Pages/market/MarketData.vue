<script setup>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import Dropdown from 'primevue/dropdown'
import FXVolatilityComponent from './category/FXVolatilityComponent.vue'
import YieldCurveComponent from './category/YieldCurveComponent.vue'
import IRVolatilityComponent from './category/IRVolatilityComponent.vue'

const store = useStore()

const selectedCategory = ref('')
const selectedFilters = ref({})
const tableData = ref([])
const columns = ref([])
const totalRecords = ref(0)
const loading = ref(false)
const error = ref('')

// Computed property to get the current component based on selected category
const currentComponent = computed(() => {
  const componentMap = {
    FXVOL: FXVolatilityComponent,
    YIELDCURVE: YieldCurveComponent,
    IRVOL: IRVolatilityComponent
  }
  return componentMap[selectedCategory.value] || null
})

const categoryOptions = [
  { label: 'FX Volatility', value: 'FXVOL' },
  { label: 'IR Volatility', value: 'IRVOL' },
  { label: 'Yield Curve', value: 'YIELDCURVE' }
]

const onCategoryChange = () => {
  // Clear filters and error when category changes
  selectedFilters.value = {}
  error.value = ''
  tableData.value = []
  columns.value = []
  totalRecords.value = 0
}

// Handle filter updates from child components
const updateFilters = (filters) => {
  selectedFilters.value = filters
}

// Handle clear filters from child components
const clearFilters = () => {
  selectedFilters.value = {}
  tableData.value = []
  columns.value = []
  totalRecords.value = 0
  error.value = ''
}

// Handle apply filters from child components
const applyFilters = () => {
  loadData()
}

const loadData = async () => {
  if (!selectedCategory.value) return

  loading.value = true
  error.value = ''

  try {
    // Prepare filter data for API
    const filterColumns = []
    const filterValues = []

    // Convert selectedFilters to the format expected by the API
    for (const [filterName, filterValue] of Object.entries(
      selectedFilters.value
    )) {
      if (
        filterValue !== null &&
        filterValue !== undefined &&
        filterValue !== ''
      ) {
        filterColumns.push(filterName)

        // Handle both single values and arrays (from MultiSelect)
        if (Array.isArray(filterValue)) {
          filterValues.push(filterValue.join('\x1e'))
        } else {
          filterValues.push([filterValue].join('\x1e'))
        }
      }
    }

    const response = await store.dispatch('getMarketData', {
      category: selectedCategory.value,
      filter_columns: filterColumns.join('\x1e'),
      filter_values: filterValues.join('\x1f')
    })

    if (response.data) {
      tableData.value = JSON.parse(response.data.data) || []
      totalRecords.value = response.data.total_size || 0
      columns.value = response.data.columns || []
    } else {
      tableData.value = []
      totalRecords.value = 0
      columns.value = []
    }
  } catch (err) {
    console.error('Error loading market data:', err)
    error.value =
      err.response?.data?.message || err.message || 'Failed to load market data'
    tableData.value = []
    totalRecords.value = 0
    columns.value = []
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="card">
    <div class="grid mb-3">
      <div class="col-12 md:col-4">
        <label for="category" class="block mb-2 font-semibold">Category</label>
        <Dropdown
          id="category"
          v-model="selectedCategory"
          :options="categoryOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select Data Type"
          class="w-full"
          @change="onCategoryChange"
        />
      </div>
    </div>

    <!-- Dynamic Category Component -->
    <div v-if="!selectedCategory" class="card">
      <div
        class="flex flex-column align-items-center justify-content-center p-4 text-center text-color-secondary"
      >
        <i class="pi pi-info-circle text-4xl text-color-secondary"></i>
        <p class="mt-3 mb-3">Please select a category to view market data</p>
      </div>
    </div>

    <!-- Render category-specific component -->
    <component
      v-else-if="currentComponent"
      :is="currentComponent"
      :selectedFilters="selectedFilters"
      :tableData="tableData"
      :loading="loading"
      :error="error"
      @update-filters="updateFilters"
      @apply-filters="applyFilters"
      @clear-filters="clearFilters"
    />
  </div>
</template>

<style scoped></style>
