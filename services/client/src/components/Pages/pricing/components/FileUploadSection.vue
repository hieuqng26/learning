<template>
  <div class="upload-section">
    <h4>Upload Portfolio Data</h4>
    <p class="upload-description">
      Each sheet should contain trades with TradeType column (e.g.,
      InterestRateSwap, FxForward, FxOption).
    </p>

    <div class="upload-controls">
      <FileUpload
        mode="basic"
        :name="uploadId"
        :accept="accept"
        :auto="true"
        :custom-upload="true"
        :choose-label="uploadLabel"
        :disabled="isUploading"
        :maxFileSize="maxFileSize"
        @uploader="handleFileUpload"
      />
    </div>

    <div v-if="uploadedFile" class="selected-file-info mt-2">
      <small class="text-color-secondary">
        <span v-if="isUploading">
          <i class="pi pi-spin pi-spinner mr-2"></i>
          Uploading: {{ uploadedFile.name }} ({{
            (uploadedFile.size / 1024 / 1024).toFixed(2)
          }}
          MB)
        </span>
        <span v-else>
          <i
            class="pi pi-check-circle mr-2"
            style="color: var(--green-500)"
          ></i>
          Processed: {{ uploadedFile.name }} ({{
            (uploadedFile.size / 1024 / 1024).toFixed(2)
          }}
          MB)
        </span>
      </small>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import FileUpload from 'primevue/fileupload'

// Props
const props = defineProps({
  uploadId: {
    type: String,
    default: 'portfolio_upload'
  },
  accept: {
    type: String,
    default: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel'
  },
  maxFileSize: {
    type: Number,
    default: 1000000
  },
  isUploading: {
    type: Boolean,
    default: false
  }
})

// Emit events
const emit = defineEmits(['file-select'])

// Local state
const uploadedFile = ref(null)

// Computed
const uploadLabel = computed(() => {
  return uploadedFile.value ? uploadedFile.value.name : 'Select File'
})

// Handle file upload
const handleFileUpload = (event) => {
  const files = event.files
  if (!files || files.length === 0) return

  const file = files[0]
  uploadedFile.value = file

  const formData = new FormData()
  formData.append('file', file)

  // Emit event to parent
  emit('file-select', { file, formData })
}
</script>

<style scoped>
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

/* Responsive Design */
@media (max-width: 768px) {
  .upload-controls {
    justify-content: stretch;
  }
}
</style>
