<template>
  <div class="documentation-content">
    <ScrollPanel style="width: 100%; height: 70vh">
      <transition name="fade" mode="out-in">
        <component
          v-if="currentComponent"
          :is="currentComponent"
          :key="selectedKey"
        />
        <div v-else class="no-content">
          <Message severity="info">
            <p>Select a topic from the sidebar to view documentation.</p>
          </Message>
        </div>
      </transition>
    </ScrollPanel>
  </div>
</template>

<script setup>
import ScrollPanel from 'primevue/scrollpanel'
import Message from 'primevue/message'

const props = defineProps({
  currentComponent: {
    type: Object,
    default: null
  },
  selectedKey: {
    type: String,
    default: ''
  }
})
</script>

<style lang="scss" scoped>
.documentation-content {
  padding-left: 1rem;

  .no-content {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 300px;
  }
}

// Fade transition for smooth content changes
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
