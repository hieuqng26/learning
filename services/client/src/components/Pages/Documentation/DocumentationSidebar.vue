<template>
  <div class="documentation-sidebar">
    <ScrollPanel style="width: 100%; height: 70vh">
      <Tree
        :value="docTree"
        selectionMode="single"
        v-model:selectionKeys="selection"
        @nodeSelect="onNodeSelect"
        :expandedKeys="expandedKeys"
        @nodeExpand="onNodeExpand"
        @nodeCollapse="onNodeCollapse"
        class="w-full"
      >
        <template #default="slotProps">
          <div class="flex align-items-center gap-2">
            <i v-if="slotProps.node.icon" :class="slotProps.node.icon"></i>
            <span>{{ slotProps.node.label }}</span>
          </div>
        </template>
      </Tree>
    </ScrollPanel>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import Tree from 'primevue/tree'
import ScrollPanel from 'primevue/scrollpanel'

const props = defineProps({
  docTree: {
    type: Array,
    required: true
  },
  selectedKey: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['select-section'])

// Selection state
const selection = ref({})

// Expanded nodes state
const expandedKeys = ref({})

// Initialize selection based on selectedKey prop
watch(
  () => props.selectedKey,
  (newKey) => {
    selection.value = { [newKey]: true }
  },
  { immediate: true }
)

// Handle node selection
const onNodeSelect = (node) => {
  if (node.component) {
    emit('select-section', node.key)
  } else if (node.children && node.children.length > 0) {
    // If parent node clicked, select first child
    emit('select-section', node.children[0].key)
  }
}

// Handle node expand
const onNodeExpand = (node) => {
  expandedKeys.value[node.key] = true
  saveExpandedState()
}

// Handle node collapse
const onNodeCollapse = (node) => {
  delete expandedKeys.value[node.key]
  saveExpandedState()
}

// Save expanded state to localStorage
const saveExpandedState = () => {
  localStorage.setItem('doc-expanded-nodes', JSON.stringify(expandedKeys.value))
}

// Load expanded state from localStorage
const loadExpandedState = () => {
  const saved = localStorage.getItem('doc-expanded-nodes')
  if (saved) {
    try {
      expandedKeys.value = JSON.parse(saved)
    } catch (e) {
      console.error('Failed to parse saved expanded state:', e)
      expandedKeys.value = {}
    }
  } else {
    // Default: expand all top-level nodes
    expandedKeys.value = {
      products: true,
      market: true,
      analytics: true
    }
  }
}

// Initialize on mount
onMounted(() => {
  loadExpandedState()
})
</script>

<style lang="scss" scoped>
.documentation-sidebar {
  border-right: 1px solid var(--surface-border);
  padding-right: 1rem;

  :deep(.p-tree) {
    border: none;
    padding: 0;

    .p-tree-node-content {
      padding: 0.5rem;
      border-radius: 4px;
      transition: all 0.2s;

      &:hover {
        background: var(--surface-hover);
      }

      &.p-highlight {
        background: var(--primary-color);
        color: var(--primary-color-text);

        .p-tree-node-icon,
        i {
          color: var(--primary-color-text);
        }
      }
    }

    .p-tree-node-label {
      width: 100%;
    }
  }
}
</style>
