<template>
  <div>
    <h1>Trigger jobs</h1>
    <p>Start a pipeline run (PR test, bootstrap, or merge).</p>

    <form @submit.prevent="submit" class="trigger-form">
      <div class="form-row">
        <label>Pipeline type</label>
        <select v-model="form.pipelineType" required>
          <option value="pr">PR test</option>
          <option value="bootstrap">Bootstrap</option>
          <option value="merge">Merge</option>
        </select>
      </div>

      <div class="form-row">
        <label>Stack file</label>
        <select v-model="form.stack" required>
          <option value="">— select —</option>
          <option v-for="s in stacks" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div class="form-row">
        <label>Changed app</label>
        <select v-model="form.app" required>
          <option value="">— select —</option>
          <option v-for="a in apps" :key="a.name" :value="a.name">{{ a.name }} ({{ a.stack }})</option>
        </select>
        <input v-if="apps.length === 0" v-model="form.app" type="text" placeholder="e.g. demo-fe" required />
      </div>

      <div class="form-row" v-if="form.pipelineType === 'pr'">
        <label>PR number</label>
        <input v-model.number="form.prNumber" type="number" min="1" required placeholder="e.g. 1" />
      </div>

      <div class="form-row">
        <label>Git URL</label>
        <input v-model="form.gitUrl" type="text" placeholder="https://github.com/jmjava/tekton-dag.git" />
      </div>

      <div class="form-row">
        <label>Git revision</label>
        <input v-model="form.gitRevision" type="text" placeholder="main" />
      </div>

      <div class="form-row">
        <label>Image registry</label>
        <input v-model="form.imageRegistry" type="text" placeholder="localhost:5000" />
      </div>

      <div class="form-row">
        <label>Version overrides (JSON)</label>
        <input v-model="form.versionOverrides" type="text" placeholder='{}' />
      </div>

      <div class="form-row">
        <label>
          <input v-model="form.buildImages" type="checkbox" />
          Use dedicated build images
        </label>
      </div>

      <div class="form-row">
        <label>Storage class</label>
        <input v-model="form.storageClass" type="text" placeholder="empty for Kind" />
      </div>

      <div class="form-actions">
        <button type="submit" :disabled="submitting">Create PipelineRun</button>
      </div>
    </form>

    <div v-if="message" :class="messageError ? 'error' : 'success'">{{ message }}</div>
    <p v-if="createdRun">
      <router-link :to="'/monitor/' + createdRun">View run: {{ createdRun }}</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';

const api = import.meta.env.VITE_API_URL || '';
const stacks = ref([]);
const apps = ref([]);
const submitting = ref(false);
const message = ref('');
const messageError = ref(false);
const createdRun = ref('');

const form = reactive({
  pipelineType: 'pr',
  stack: '',
  app: '',
  prNumber: 1,
  gitUrl: '',
  gitRevision: 'main',
  imageRegistry: 'localhost:5000',
  versionOverrides: '{}',
  buildImages: false,
  storageClass: '',
});

onMounted(async () => {
  try {
    const r = await fetch(`${api}/api/stacks`);
    if (r.ok) {
      const data = await r.json();
      stacks.value = data.stacks || [];
      apps.value = data.apps || [];
      if (stacks.value.length && !form.stack) form.stack = stacks.value[0];
      if (apps.value.length && !form.app) form.app = apps.value[0]?.name || '';
    }
  } catch {
    stacks.value = [];
    apps.value = [];
  }
});

async function submit() {
  if (form.pipelineType === 'pr' && !form.prNumber) {
    message.value = 'PR number is required for PR runs';
    messageError.value = true;
    return;
  }
  message.value = '';
  messageError.value = false;
  createdRun.value = '';
  submitting.value = true;
  try {
    const body = {
      pipelineType: form.pipelineType,
      stack: form.stack,
      app: form.app,
      gitUrl: form.gitUrl || undefined,
      gitRevision: form.gitRevision || undefined,
      imageRegistry: form.imageRegistry || undefined,
      versionOverrides: form.versionOverrides && form.versionOverrides.trim() !== '{}' ? form.versionOverrides : undefined,
      buildImages: form.buildImages,
      storageClass: form.storageClass || undefined,
    };
    if (form.pipelineType === 'pr') body.prNumber = form.prNumber;
    const r = await fetch(`${api}/api/trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      message.value = data.error || r.statusText || 'Trigger failed';
      messageError.value = true;
      return;
    }
    message.value = 'PipelineRun created.';
    messageError.value = false;
    if (data.pipelineRun) createdRun.value = data.pipelineRun;
  } catch (e) {
    message.value = e.message || 'Request failed';
    messageError.value = true;
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
  .trigger-form { max-width: 480px; }
  .form-row { margin-bottom: 0.75rem; }
  .form-row label { display: block; margin-bottom: 0.25rem; font-weight: 500; }
  .form-row select, .form-row input[type="text"], .form-row input[type="number"] { width: 100%; padding: 0.35rem; }
  .form-actions { margin-top: 1rem; }
  .form-actions button { padding: 0.5rem 1rem; cursor: pointer; }
  .form-actions button:disabled { opacity: 0.7; cursor: not-allowed; }
  .error { color: #c00; margin-top: 1rem; }
  .success { color: green; margin-top: 1rem; }
</style>
