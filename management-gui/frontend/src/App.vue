<template>
  <div class="app">
    <NavSidebar />
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import NavSidebar from './components/NavSidebar.vue'
import { useTeamsStore } from './stores/teams'

const teams = useTeamsStore()
onMounted(() => teams.fetchTeams())
</script>

<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, sans-serif; }
.app { display: flex; min-height: 100vh; }
.main { flex: 1; padding: 1.5rem 2rem; max-width: 1200px; overflow-y: auto; }
h1 { margin-top: 0; font-size: 1.5rem; }
</style>
