<script setup>
import { computed } from 'vue'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'
import Button from 'primevue/button'
import SimpleTable from '@/components/Table/SimpleTable.vue'

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

// Yield Curve specific filters
const filters = {
  Name: {
    values: [
      'EUR.CREDIT.FUNDING',
      'EUR.ESTR.CSA_EUR',
      'GBP.CREDIT.FUNDING',
      'GBP.SONIA.CSA_GBP',
      'IDR.CREDIT.USDFUNDING',
      'IDR.JIBOR.3M',
      'IDR.JIBOR.CSA_USD',
      'PLN.CREDIT.FUNDING',
      'PLN.WIBOR.CSA_USD',
      'PLN.WIRON.CSA_PLN',
      'USD.CREDIT.FUNDING',
      'USD.LIBOR.3M',
      'USD.SOFR.CSA_USD'
    ],
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
</script>

<template>
  <!-- Yield Curve Filters Section -->
  <div class="card">
    <div class="flex justify-content-between align-items-center mb-3 pb-2 border-bottom-1 surface-border">
      <h5 class="m-0 text-color">Yield Curve Filters</h5>
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
      <p class="mt-3 mb-3">Loading yield curve data...</p>
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
      downloadFileName="yield_curve_data"
    />
  </div>

  <!-- Future: Yield Curve Visualization -->
  <!-- This section can be expanded to include yield curve line charts -->
  <!--
  <div v-if="tableData.length > 0 && selectedFilters.Name" class="card">
    <div class="plot-header">
      <h5>Yield Curve Visualization</h5>
    </div>
    <div class="yield-curve-container">
      // Future: Add yield curve line chart here
    </div>
  </div>
  -->
</template>

<style scoped>
</style>