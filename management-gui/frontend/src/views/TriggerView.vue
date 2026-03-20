<template>
  <div>
    <h1>Trigger jobs</h1>
    <p>Start a pipeline run (PR test, bootstrap, or merge).</p>

    <form @submit.prevent="submit" class="trigger-form">
      <div class="field">
        <label>Pipeline type</label>
        <select v-model="form.pipelineType" required>
          <option value="pr">PR test</option>
          <option value="bootstrap">Bootstrap</option>
          <option value="merge">Merge</option>
        </select>
      </div>

      <div class="field">
        <label>Stack file</label>
        <select v-model="form.stack" required>
          <option value="">— select —</option>
          <option v-for="s in stackOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div class="field">
        <label>Changed app</label>
        <select v-model="form.app" required>
          <option value="">— select —</option>
          <option v-for="a in appOptions" :key="a" :value="a">{{ a }}</option>
        </select>
      </div>

      <div class="field" v-if="form.pipelineType === 'pr'">
        <label>PR number</label>
        <input v-model.number="form.prNumber" type="number" min="1" required placeholder="e.g. 1" />
      </div>

      <div class="field">
        <label>Git URL</label>
        <input v-model="form.gitUrl" type="text" placeholder="https://github.com/jmjava/tekton-dag.git" />
      </div>

      <div class="field">
        <label>Git revision</label>
        <input v-model="form.gitRevision" type="text" placeholder="main" />
      </div>

      <div class="field">
        <label>Image registry</label>
        <input v-model="form.imageRegistry" type="text" placeholder="localhost:5000" />
      </div>

      <div class="field">
        <label>Version overrides (JSON)</label>
        <input v-model="form.versionOverrides" type="text" placeholder="{}" />
      </div>

      <div class="form-actions">
        <button type="submit" :disabled="submitting">Create PipelineRun</button>
      </div>
    </form>

    <div v-if="message" :class="messageError ? 'msg-error' : 'msg-success'">{{ message }}</div>
    <p v-if="createdRun">
      <router-link :to="'/monitor/' + createdRun">View run: {{ createdRun }}</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useStacksStore } from '../stores/stacks'
import { useTeamsStore } from '../stores/teams'
import { useApi } from '../composables/useApi'

const stacksStore = useStacksStore()
const teamsStore = useTeamsStore()
const { teamUrl, post } = useApi()

const submitting = ref(false)
const message = ref('')
const messageError = ref(false)
const createdRun = ref('')

const form = reactive({
  pipelineType: 'pr',
  stack: '',
  app: '',
  prNumber: 1,
  gitUrl: '',
  gitRevision: 'main',
  imageRegistry: 'localhost:5000',
  versionOverrides: '{}',
})

const stackOptions = computed(() => stacksStore.stacks.map(s => s.stack_file))
const appOptions = computed(() => {
  const stack = stacksStore.stacks.find(s => s.stack_file === form.stack)
  return stack ? stack.apps.map(a => a.name) : []
})

watch(() => teamsStore.activeTeam, () => { if (teamsStore.activeTeam) stacksStore.fetchStacks() })
onMounted(() => { if (teamsStore.activeTeam) stacksStore.fetchStacks() })

async function submit() {
  if (form.pipelineType === 'pr' && !form.prNumber) {
    message.value = 'PR number is required'
    messageError.value = true
    return
  }
  message.value = ''
  messageError.value = false
  createdRun.value = ''
  submitting.value = true
  try {
    const body = {
      pipelineType: form.pipelineType,
      stack: form.stack,
      app: form.app,
      gitUrl: form.gitUrl || undefined,
      gitRevision: form.gitRevision || undefined,
      imageRegistry: form.imageRegistry || undefined,
      versionOverrides: form.versionOverrides && form.versionOverrides.trim() !== '{}' ? form.versionOverrides : undefined,
    }
    if (form.pipelineType === 'pr') body.prNumber = form.prNumber
    const data = await post(teamUrl('/trigger'), body)
    message.value = 'PipelineRun created.'
    messageError.value = false
    if (data.pipelineRun) createdRun.value = data.pipelineRun
  } catch (e) {
    message.value = e.message || 'Request failed'
    messageError.value = true
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.trigger-form { max-width: 480px; }
.field { margin-bottom: 0.75rem; }
.field label { display: block; margin-bottom: 0.25rem; font-weight: 500; font-size: 0.9rem; }
.field select, .field input { width: 100%; padding: 0.4rem; border: 1px solid #ccc; border-radius: 4px; }
.form-actions { margin-top: 1rem; }
.form-actions button { padding: 0.5rem 1rem; cursor: pointer; background: #1a1a2e; color: #fff; border: none; border-radius: 4px; }
.form-actions button:disabled { opacity: 0.6; cursor: not-allowed; }
.msg-error { color: #c00; margin-top: 1rem; }
.msg-success { color: green; margin-top: 1rem; }
</style>
