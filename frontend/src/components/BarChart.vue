<template>
  <canvas ref="canvasRef"></canvas>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

// eslint-disable-next-line no-undef
const props = defineProps({
  data: Object,
  options: Object
})

const canvasRef = ref(null)
let chartInstance = null

const renderChart = () => {
  if (!canvasRef.value) return;
  if (chartInstance) chartInstance.destroy()
  chartInstance = new Chart(canvasRef.value, {
    type: 'bar',
    data: props.data,
    options: props.options
  })
}

onMounted(renderChart)
watch(
  () => [props.data, props.options],
  renderChart,
  { immediate: false, deep: false }
)
</script> 