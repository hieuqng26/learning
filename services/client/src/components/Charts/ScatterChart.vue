<script setup>
import { onMounted, ref, watch } from 'vue'
import { useLayout } from '@/layout/composables/layout'
import { formatNumber, formatLargeNumber } from '../Table/utils'

const { isDarkTheme } = useLayout()

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  title: {
    type: String,
    default: ''
  },
  xTitle: {
    type: String,
    default: ''
  },
  yTitle: {
    type: String,
    default: ''
  },
  yLabel: {
    type: String,
    default: ''
  }
})

const title = ref(props.title)
const xTitle = ref(props.xTitle)
const yTitle = ref(props.yTitle)

// Watch for title, xTitle, yTitle changes
watch(
  () => [props.title, props.xTitle, props.yTitle],
  ([newTitle, newXTitle, newYTitle]) => {
    scatterOptions.value.plugins.title.display = newTitle ? true : false
    scatterOptions.value.plugins.title.text = newTitle
    scatterOptions.value.scales.x.title.display = newXTitle ? true : false
    scatterOptions.value.scales.x.title.text = newXTitle
    scatterOptions.value.scales.y.title.display = newYTitle ? true : false
    scatterOptions.value.scales.y.title.text = newYTitle
  }
)

// Chart Options
const scatterOptions = ref(null)
const genericOptions = {
  maintainAspectRatio: false,
  aspectRatio: 0.6,
  interaction: {
    intersect: true,
    mode: 'point'
  }
}

const applyTheme = (textColor, gridColor) => {
  return {
    ...genericOptions,
    plugins: {
      title: {
        display: title.value ? true : false,
        text: title.value,
        color: textColor,
        fontSize: 20
      },
      legend: {
        labels: {
          color: textColor,
          usePointStyle: true,
          pointStyle: 'circle',
          padding: 15
        }
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            let label = context.dataset.label || ''
            if (label) {
              label += ': '
            }
            if (context.parsed.y !== null) {
              label += formatNumber(context.parsed.y, 2)
            }
            return label
          }
        }
      }
    },
    scales: {
      x: {
        type: 'category',
        title: {
          display: xTitle.value ? true : false,
          text: xTitle.value,
          color: textColor
        },
        ticks: {
          color: textColor,
          autoSkip: true,
          maxRotation: 45,
          minRotation: 45
        },
        grid: {
          color: gridColor
        }
      },
      y: {
        title: {
          display: yTitle.value ? true : false,
          text: yTitle.value,
          color: textColor
        },
        ticks: {
          color: textColor,
          callback: function (value, index, ticks) {
            let v = formatLargeNumber(value, 2)
            return props.yLabel ? props.yLabel + ' ' + v : v
          }
        },
        grid: {
          color: gridColor
        }
      }
    }
  }
}

onMounted(() => {
  const val = isDarkTheme.value
  const textColor = val ? '#ebedef' : '#495057'
  const gridColor = val ? 'rgba(160, 167, 181, .3)' : '#ebedef'
  scatterOptions.value = applyTheme(textColor, gridColor)
})

watch(
  isDarkTheme,
  (darkTheme) => {
    const textColor = darkTheme ? '#ebedef' : '#495057'
    const gridColor = darkTheme ? 'rgba(160, 167, 181, .1)' : '#ebedef'
    scatterOptions.value = applyTheme(textColor, gridColor)
  },
  { immediate: true }
)
</script>

<template>
  <Chart type="scatter" :data="props.data" :options="scatterOptions" class="h-30rem" />
</template>
