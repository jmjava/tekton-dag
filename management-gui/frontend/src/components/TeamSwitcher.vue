<template>
  <div v-if="teams.showSwitcher" class="team-switcher">
    <label>Team</label>
    <select :value="teams.activeTeam" @change="switchTeam($event.target.value)">
      <option v-for="t in teams.teams" :key="t.name" :value="t.name">
        {{ t.name }} ({{ t.cluster || 'default' }})
      </option>
    </select>
  </div>
</template>

<script setup>
import { useTeamsStore } from '../stores/teams'
import { useRunsStore } from '../stores/runs'
import { useStacksStore } from '../stores/stacks'

const teams = useTeamsStore()

function switchTeam(name) {
  teams.setActiveTeam(name)
  useRunsStore().reset()
  useStacksStore().reset()
}
</script>

<style scoped>
.team-switcher { padding: 0.5rem 1rem; }
.team-switcher label { display: block; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #aaa; margin-bottom: 0.25rem; }
.team-switcher select { width: 100%; padding: 0.35rem; background: #16213e; color: #fff; border: 1px solid #2a3a5c; border-radius: 4px; }
</style>
