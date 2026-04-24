<template>
  <div class="documentation-container">
    <Card>
      <template #title>
        <div class="flex align-items-center gap-2">
          <span>Documentation</span>
        </div>
      </template>
      <template #content>
        <div class="grid">
          <!-- Sidebar -->
          <div class="col-12 md:col-3">
            <DocumentationSidebar
              :docTree="docTree"
              :selectedKey="selectedKey"
              @select-section="handleSectionSelect"
            />
          </div>

          <!-- Content Area -->
          <div class="col-12 md:col-9">
            <!-- Breadcrumb -->
            <Breadcrumb
              :home="breadcrumbHome"
              :model="breadcrumbItems"
              class="mb-3"
            />

            <!-- Content -->
            <DocumentationContent
              :currentComponent="currentComponent"
              :selectedKey="selectedKey"
            />
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Card from 'primevue/card'
import Breadcrumb from 'primevue/breadcrumb'
import DocumentationSidebar from '@/components/Pages/Documentation/DocumentationSidebar.vue'
import DocumentationContent from '@/components/Pages/Documentation/DocumentationContent.vue'

// Import section components - Products
import ProductsOverview from '@/components/Pages/Documentation/sections/products/ProductsOverview.vue'
import FxOption from '@/components/Pages/Documentation/sections/products/FxOption.vue'
import FxForward from '@/components/Pages/Documentation/sections/products/FxForward.vue'
import CrossCurrencySwap from '@/components/Pages/Documentation/sections/products/CrossCurrencySwap.vue'
import OIS from '@/components/Pages/Documentation/sections/products/OIS.vue'
import IRS from '@/components/Pages/Documentation/sections/products/IRS.vue'

// Import section components - Market
import MarketOverview from '@/components/Pages/Documentation/sections/market/MarketOverview.vue'
import YieldCurves from '@/components/Pages/Documentation/sections/market/YieldCurves.vue'
import FxVolatility from '@/components/Pages/Documentation/sections/market/FxVolatility.vue'
import PricingMethods from '@/components/Pages/Documentation/sections/market/PricingMethods.vue'

// Import section components - Analytics
import AnalyticsOverview from '@/components/Pages/Documentation/sections/analytics/AnalyticsOverview.vue'
import RiskSensitivity from '@/components/Pages/Documentation/sections/analytics/RiskSensitivity.vue'
import SACCR from '@/components/Pages/Documentation/sections/analytics/SACCR.vue'

const props = defineProps({
  module: String
})

// Navigation tree structure
const docTree = ref([
  {
    key: 'products',
    label: 'Products',
    children: [
      {
        key: 'products-overview',
        label: 'Overview',
        component: 'ProductsOverview'
      },
      { key: 'fx-option', label: 'FX Option', component: 'FxOption' },
      { key: 'fx-forward', label: 'FX Forward', component: 'FxForward' },
      {
        key: 'cross-currency-swap',
        label: 'Cross Currency Swap',
        component: 'CrossCurrencySwap'
      },
      { key: 'ois', label: 'OIS', component: 'OIS' },
      { key: 'irs', label: 'Interest Rate Swap', component: 'IRS' }
    ]
  },
  {
    key: 'market',
    label: 'Market',
    children: [
      {
        key: 'market-overview',
        label: 'Overview',
        component: 'MarketOverview'
      },
      { key: 'yield-curves', label: 'Yield Curves', component: 'YieldCurves' },
      {
        key: 'fx-volatility',
        label: 'FX Volatility',
        component: 'FxVolatility'
      },
      {
        key: 'pricing-methods',
        label: 'Pricing Methods',
        component: 'PricingMethods'
      }
    ]
  },
  {
    key: 'analytics',
    label: 'Analytics',
    children: [
      {
        key: 'analytics-overview',
        label: 'Overview',
        component: 'AnalyticsOverview'
      },
      {
        key: 'risk-sensitivity',
        label: 'Risk Sensitivity',
        component: 'RiskSensitivity'
      },
      { key: 'saccr', label: 'SACCR', component: 'SACCR' }
    ]
  }
])

// Component mapping
const componentMap = {
  ProductsOverview,
  FxOption,
  FxForward,
  CrossCurrencySwap,
  OIS,
  IRS,
  MarketOverview,
  YieldCurves,
  FxVolatility,
  PricingMethods,
  AnalyticsOverview,
  RiskSensitivity,
  SACCR
}

// Selected section state - default to products overview
const selectedKey = ref('products-overview')

// Current component computed
const currentComponent = computed(() => {
  const selectedNode = findNodeByKey(docTree.value, selectedKey.value)
  if (selectedNode && selectedNode.component) {
    return componentMap[selectedNode.component]
  }
  return null
})

// Breadcrumb configuration
const breadcrumbHome = ref({
  icon: 'pi pi-home',
  to: '/'
})

const breadcrumbItems = computed(() => {
  const items = []
  const selectedNode = findNodeByKey(docTree.value, selectedKey.value)

  if (selectedNode) {
    // Find parent category
    const parent = findParentNode(docTree.value, selectedKey.value)
    if (parent) {
      items.push({ label: parent.label })
    }
    items.push({ label: selectedNode.label })
  }

  return items
})

// Handle section selection
const handleSectionSelect = (key) => {
  selectedKey.value = key
}

// Helper function to find node by key
const findNodeByKey = (nodes, key) => {
  for (const node of nodes) {
    if (node.key === key) {
      return node
    }
    if (node.children) {
      const found = findNodeByKey(node.children, key)
      if (found) return found
    }
  }
  return null
}

// Helper function to find parent node
const findParentNode = (nodes, childKey) => {
  for (const node of nodes) {
    if (node.children) {
      const hasChild = node.children.some((child) => child.key === childKey)
      if (hasChild) {
        return node
      }
    }
  }
  return null
}
</script>

<style lang="scss" scoped>
.documentation-container {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
