<template>
  <div class="app">
    <h1>tekton-dag-vue-fe</h1>
    <p>Sample Vue frontend for Tekton DAG pipelines.</p>
    <pre v-if="report">{{ report }}</pre>
    <p v-else-if="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const report = ref('')
const error = ref('')

onMounted(async () => {
  try {
    const resp = await fetch('/propagation')
    const body = await resp.json()
    report.value = JSON.stringify(body, null, 2)
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
})
</script>

<style scoped>
.app { font-family: system-ui; padding: 2rem; }
pre { background: #f4f4f5; padding: 1rem; overflow: auto; }
</style>
