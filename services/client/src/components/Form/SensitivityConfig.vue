<template>
  <div class="sensitivity-config">
    <div class="sensitivity-header">
      <span class="sensitivity-title">Risk Factors</span>
      <Button
        icon="pi pi-plus"
        label="Add Risk Factor"
        class="p-button-sm p-button-outlined"
        @click="addEntry"
      />
    </div>

    <div v-if="entries.length === 0" class="sensitivity-empty">
      <i class="pi pi-info-circle"></i>
      <span
        >No risk factors configured. Click "Add Risk Factor" to enable
        sensitivity analysis.</span
      >
    </div>

    <div
      v-for="(entry, index) in entries"
      :key="index"
      class="sensitivity-entry"
    >
      <div class="entry-header">
        <span class="entry-number">Risk Factor {{ index + 1 }}</span>
        <Button
          icon="pi pi-trash"
          class="p-button-sm p-button-danger p-button-text"
          @click="removeEntry(index)"
        />
      </div>

      <div class="entry-fields">
        <!-- Risk Factor Type -->
        <div class="field-row">
          <label>Risk Factor Type</label>
          <Dropdown
            v-model="entry.type"
            :options="riskFactorTypes"
            optionLabel="label"
            optionValue="value"
            placeholder="Select risk factor type"
            class="w-full"
            @change="onTypeChange(index)"
          />
        </div>

        <!-- Discount Curve Fields -->
        <template v-if="entry.type === 'discount_curve'">
          <div class="field-row">
            <label>Currency</label>
            <Dropdown
              v-model="entry.currency"
              :options="currencyOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select currency"
              class="w-full"
              :filter="true"
            />
          </div>
          <div class="field-row">
            <label>Shift Type</label>
            <Dropdown
              v-model="entry.shift_type"
              :options="shiftTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift type"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Size</label>
            <InputNumber
              v-model="entry.shift_size"
              :minFractionDigits="4"
              :maxFractionDigits="6"
              placeholder="e.g., 0.0001 for 1bp"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Scheme</label>
            <Dropdown
              v-model="entry.shift_scheme"
              :options="shiftSchemeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift scheme"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Tenors</label>
            <InputText
              v-model="entry.shift_tenors"
              placeholder="e.g., 6M,1Y,2Y,5Y,10Y"
              class="w-full"
            />
            <small class="field-help">Comma-separated tenor values</small>
          </div>
        </template>

        <!-- Index Curve Fields -->
        <template v-if="entry.type === 'index_curve'">
          <div class="field-row">
            <label>Index</label>
            <Dropdown
              v-model="entry.index"
              :options="indexOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select index"
              class="w-full"
              :filter="true"
            />
          </div>
          <div class="field-row">
            <label>Shift Type</label>
            <Dropdown
              v-model="entry.shift_type"
              :options="shiftTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift type"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Size</label>
            <InputNumber
              v-model="entry.shift_size"
              :minFractionDigits="4"
              :maxFractionDigits="6"
              placeholder="e.g., 0.0001 for 1bp"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Scheme</label>
            <Dropdown
              v-model="entry.shift_scheme"
              :options="shiftSchemeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift scheme"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Tenors</label>
            <InputText
              v-model="entry.shift_tenors"
              placeholder="e.g., 6M,1Y,2Y,5Y,10Y"
              class="w-full"
            />
            <small class="field-help">Comma-separated tenor values</small>
          </div>
        </template>

        <!-- FX Spot Fields -->
        <template v-if="entry.type === 'fx_spot'">
          <div class="field-row">
            <label>Currency Pair</label>
            <Dropdown
              v-model="entry.pair"
              :options="fxPairOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select currency pair"
              class="w-full"
              :filter="true"
            />
          </div>
          <div class="field-row">
            <label>Shift Type</label>
            <Dropdown
              v-model="entry.shift_type"
              :options="shiftTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift type"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Size</label>
            <InputNumber
              v-model="entry.shift_size"
              :minFractionDigits="3"
              :maxFractionDigits="5"
              placeholder="e.g., 0.01 for 1%"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Scheme</label>
            <Dropdown
              v-model="entry.shift_scheme"
              :options="shiftSchemeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift scheme"
              class="w-full"
            />
          </div>
        </template>

        <!-- FX Volatility Fields -->
        <template v-if="entry.type === 'fx_volatility'">
          <div class="field-row">
            <label>Currency Pair</label>
            <Dropdown
              v-model="entry.pair"
              :options="fxVolPairOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select currency pair"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Type</label>
            <Dropdown
              v-model="entry.shift_type"
              :options="shiftTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift type"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Size</label>
            <InputNumber
              v-model="entry.shift_size"
              :minFractionDigits="3"
              :maxFractionDigits="5"
              placeholder="e.g., 0.01 for 1%"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Scheme</label>
            <Dropdown
              v-model="entry.shift_scheme"
              :options="shiftSchemeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift scheme"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Expiries</label>
            <MultiSelect
              v-model="entry.shift_expiries"
              :options="fxVolExpiryOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select expiries"
              class="w-full"
              :filter="true"
              :maxSelectedLabels="3"
              display="chip"
            />
            <small class="field-help">Select volatility surface expiries</small>
          </div>
          <div class="field-row">
            <label>Shift Strikes</label>
            <MultiSelect
              v-model="entry.shift_strikes"
              :options="fxVolStrikeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select strikes"
              class="w-full"
              :filter="true"
              :maxSelectedLabels="3"
              display="chip"
            />
            <small class="field-help"
              >Select strikes (0 = ATM, negative = OTM put, positive = OTM
              call)</small
            >
          </div>
        </template>

        <!-- Swaption Volatility Fields -->
        <template v-if="entry.type === 'swaption_volatility'">
          <div class="field-row">
            <label>Currency</label>
            <Dropdown
              v-model="entry.currency"
              :options="currencyOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select currency"
              class="w-full"
              :filter="true"
            />
          </div>
          <div class="field-row">
            <label>Shift Type</label>
            <Dropdown
              v-model="entry.shift_type"
              :options="shiftTypeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift type"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Size</label>
            <InputNumber
              v-model="entry.shift_size"
              :minFractionDigits="3"
              :maxFractionDigits="5"
              placeholder="e.g., 0.01 for 1%"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Scheme</label>
            <Dropdown
              v-model="entry.shift_scheme"
              :options="shiftSchemeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select shift scheme"
              class="w-full"
            />
          </div>
          <div class="field-row">
            <label>Shift Expiries</label>
            <MultiSelect
              v-model="entry.shift_expiries"
              :options="swaptionVolExpiryOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select expiries"
              class="w-full"
              :filter="true"
              :maxSelectedLabels="3"
              display="chip"
            />
            <small class="field-help">Select swaption expiry tenors</small>
          </div>
          <div class="field-row">
            <label>Shift Terms</label>
            <MultiSelect
              v-model="entry.shift_terms"
              :options="swaptionVolTermOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select terms"
              class="w-full"
              :filter="true"
              :maxSelectedLabels="3"
              display="chip"
            />
            <small class="field-help">Select underlying swap terms</small>
          </div>
          <div class="field-row">
            <label>Shift Strikes (Optional)</label>
            <MultiSelect
              v-model="entry.shift_strikes"
              :options="swaptionVolStrikeOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select strikes (optional)"
              class="w-full"
              :filter="true"
              :maxSelectedLabels="3"
              display="chip"
            />
            <small class="field-help"
              >Strike spreads for smile/skew analysis (0 = ATM, leave empty for
              ATM only)</small
            >
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const entries = ref([...props.modelValue])

// Options
const riskFactorTypes = [
  { label: 'Discount Curve', value: 'discount_curve' },
  { label: 'Index Curve', value: 'index_curve' },
  { label: 'FX Spot', value: 'fx_spot' },
  { label: 'FX Volatility', value: 'fx_volatility' },
  { label: 'Swaption Volatility', value: 'swaption_volatility' }
]

const currencyOptions = [
  { label: 'EUR - Euro', value: 'EUR' },
  { label: 'USD - US Dollar', value: 'USD' },
  { label: 'GBP - British Pound', value: 'GBP' },
  { label: 'JPY - Japanese Yen', value: 'JPY' }
]

const indexOptions = [
  { label: 'EUR-EURIBOR-1M', value: 'EUR-EURIBOR-1M' },
  { label: 'EUR-EURIBOR-3M', value: 'EUR-EURIBOR-3M' },
  { label: 'EUR-EURIBOR-6M', value: 'EUR-EURIBOR-6M' },
  { label: 'EUR-EONIA', value: 'EUR-EONIA' },
  { label: 'USD-LIBOR-3M', value: 'USD-LIBOR-3M' },
  { label: 'USD-LIBOR-6M', value: 'USD-LIBOR-6M' },
  { label: 'USD-FedFunds', value: 'USD-FedFunds' },
  { label: 'GBP-LIBOR-3M', value: 'GBP-LIBOR-3M' },
  { label: 'GBP-LIBOR-6M', value: 'GBP-LIBOR-6M' },
  { label: 'GBP-SONIA', value: 'GBP-SONIA' },
  { label: 'JPY-LIBOR-3M', value: 'JPY-LIBOR-3M' },
  { label: 'JPY-LIBOR-6M', value: 'JPY-LIBOR-6M' }
]

const shiftTypeOptions = [
  { label: 'Absolute', value: 'Absolute' },
  { label: 'Relative', value: 'Relative' }
]

const shiftSchemeOptions = [
  { label: 'Forward', value: 'Forward' },
  { label: 'Backward', value: 'Backward' },
  { label: 'Central', value: 'Central' }
]

const fxPairOptions = [
  { label: 'EUR/USD', value: 'USDEUR' },
  { label: 'EUR/GBP', value: 'GBPEUR' },
  { label: 'EUR/JPY', value: 'JPYEUR' }
]

const fxVolPairOptions = [
  { label: 'EUR/USD', value: 'USDEUR' },
  { label: 'EUR/GBP', value: 'GBPEUR' },
  { label: 'EUR/JPY', value: 'JPYEUR' }
]

const fxVolExpiryOptions = [
  { label: '2 Weeks', value: '2W' },
  { label: '1 Month', value: '1M' },
  { label: '3 Months', value: '3M' },
  { label: '6 Months', value: '6M' },
  { label: '1 Year', value: '1Y' },
  { label: '2 Years', value: '2Y' },
  { label: '3 Years', value: '3Y' },
  { label: '5 Years', value: '5Y' },
  { label: '10 Years', value: '10Y' },
  { label: '15 Years', value: '15Y' },
  { label: '20 Years', value: '20Y' },
  { label: '30 Years', value: '30Y' }
]

const fxVolStrikeOptions = [
  { label: '-7 (Far OTM Put)', value: -7 },
  { label: '-6', value: -6 },
  { label: '-5', value: -5 },
  { label: '-4', value: -4 },
  { label: '-3', value: -3 },
  { label: '-2', value: -2 },
  { label: '-1', value: -1 },
  { label: '-0.5', value: -0.5 },
  { label: '-0.25', value: -0.25 },
  { label: '-0.1', value: -0.1 },
  { label: '-0.05', value: -0.05 },
  { label: '0 (ATM)', value: 0 },
  { label: '0.05', value: 0.05 },
  { label: '0.1', value: 0.1 },
  { label: '0.25', value: 0.25 },
  { label: '0.5', value: 0.5 },
  { label: '1', value: 1 },
  { label: '2', value: 2 },
  { label: '3', value: 3 },
  { label: '4', value: 4 },
  { label: '5', value: 5 },
  { label: '6', value: 6 },
  { label: '7 (Far OTM Call)', value: 7 }
]

const swaptionVolExpiryOptions = [
  { label: '1 Month', value: '1M' },
  { label: '3 Months', value: '3M' },
  { label: '6 Months', value: '6M' },
  { label: '1 Year', value: '1Y' },
  { label: '2 Years', value: '2Y' },
  { label: '3 Years', value: '3Y' },
  { label: '5 Years', value: '5Y' },
  { label: '7 Years', value: '7Y' },
  { label: '10 Years', value: '10Y' },
  { label: '15 Years', value: '15Y' },
  { label: '20 Years', value: '20Y' },
  { label: '25 Years', value: '25Y' },
  { label: '30 Years', value: '30Y' }
]

const swaptionVolTermOptions = [
  { label: '1 Year', value: '1Y' },
  { label: '2 Years', value: '2Y' },
  { label: '3 Years', value: '3Y' },
  { label: '5 Years', value: '5Y' },
  { label: '7 Years', value: '7Y' },
  { label: '10 Years', value: '10Y' },
  { label: '15 Years', value: '15Y' },
  { label: '20 Years', value: '20Y' },
  { label: '25 Years', value: '25Y' },
  { label: '30 Years', value: '30Y' }
]

const swaptionVolStrikeOptions = [
  { label: '-0.02 (-200bp)', value: -0.02 },
  { label: '-0.015 (-150bp)', value: -0.015 },
  { label: '-0.01 (-100bp)', value: -0.01 },
  { label: '-0.005 (-50bp)', value: -0.005 },
  { label: '0 (ATM)', value: 0 },
  { label: '0.005 (+50bp)', value: 0.005 },
  { label: '0.01 (+100bp)', value: 0.01 },
  { label: '0.015 (+150bp)', value: 0.015 },
  { label: '0.02 (+200bp)', value: 0.02 }
]

// Methods
const addEntry = () => {
  entries.value.push({
    type: null,
    currency: null,
    index: null,
    pair: null,
    shift_type: 'Absolute',
    shift_size: null,
    shift_scheme: 'Forward',
    shift_tenors: '',
    shift_expiries: [],
    shift_terms: [],
    shift_strikes: []
  })
  emitUpdate()
}

const removeEntry = (index) => {
  entries.value.splice(index, 1)
  emitUpdate()
}

const onTypeChange = (index) => {
  // Reset type-specific fields when type changes
  const entry = entries.value[index]
  entry.currency = null
  entry.index = null
  entry.pair = null
  entry.shift_size = null
  entry.shift_tenors = ''
  entry.shift_expiries = []
  entry.shift_terms = []
  entry.shift_strikes = []

  // Set defaults based on type
  if (entry.type === 'discount_curve') {
    entry.shift_type = 'Absolute'
    entry.shift_size = 0.0001
    entry.shift_scheme = 'Forward'
    entry.currency = 'EUR'
    entry.shift_tenors = '6M,1Y,2Y,5Y,10Y'
  } else if (entry.type === 'index_curve') {
    entry.shift_type = 'Absolute'
    entry.shift_size = 0.0001
    entry.shift_scheme = 'Forward'
    entry.index = 'EUR-EURIBOR-3M'
    entry.shift_tenors = '6M,1Y,2Y,5Y,10Y'
  } else if (entry.type === 'fx_spot') {
    entry.shift_type = 'Relative'
    entry.shift_size = 0.01
    entry.shift_scheme = 'Forward'
    entry.pair = 'USDEUR'
  } else if (entry.type === 'fx_volatility') {
    entry.shift_type = 'Relative'
    entry.shift_size = 0.01
    entry.shift_scheme = 'Forward'
    entry.pair = 'USDEUR'
    entry.shift_expiries = ['5Y']
    entry.shift_strikes = [0]
  } else if (entry.type === 'swaption_volatility') {
    entry.shift_type = 'Relative'
    entry.shift_size = 0.01
    entry.shift_scheme = 'Forward'
    entry.currency = 'EUR'
    entry.shift_expiries = ['2Y']
    entry.shift_terms = ['10Y']
    entry.shift_strikes = [0]
  }

  emitUpdate()
}

const emitUpdate = () => {
  emit('update:modelValue', [...entries.value])
}

// Watch for changes and emit
watch(
  entries,
  () => {
    emitUpdate()
  },
  { deep: true }
)

// Sync with parent
watch(
  () => props.modelValue,
  (newValue) => {
    if (JSON.stringify(newValue) !== JSON.stringify(entries.value)) {
      entries.value = [...newValue]
    }
  },
  { deep: true }
)
</script>

<style scoped>
.sensitivity-config {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sensitivity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--surface-border);
}

.sensitivity-title {
  font-weight: 600;
  color: var(--text-color);
}

.sensitivity-empty {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 6px;
  color: var(--text-color-secondary);
  font-size: 0.875rem;
}

.sensitivity-entry {
  border: 1px solid var(--surface-border);
  border-radius: 6px;
  padding: 1rem;
  background: var(--surface-0);
}

.entry-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--surface-100);
}

.entry-number {
  font-weight: 500;
  color: var(--primary-color);
}

.entry-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.field-row label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-color-secondary);
}

.field-help {
  font-size: 0.75rem;
  color: var(--text-color-secondary);
}

.w-full {
  width: 100%;
}
</style>
