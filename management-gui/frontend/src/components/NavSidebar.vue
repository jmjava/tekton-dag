<template>
  <aside class="sidebar">
    <div class="logo">Tekton DAG</div>
    <TeamSwitcher />
    <nav class="nav-links">
      <router-link to="/">Trigger</router-link>
      <router-link to="/monitor">Monitor</router-link>
      <router-link to="/test-results">Test results</router-link>
      <router-link to="/dag">DAG</router-link>
      <router-link to="/git">Git</router-link>
      <router-link to="/dashboard">Dashboard</router-link>
    </nav>
  </aside>
</template>

<script setup>
import TeamSwitcher from './TeamSwitcher.vue'
</script>

<style scoped>
.sidebar {
  width: 220px;
  min-height: 100vh;
  background: #1a1a2e;
  color: #eee;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.logo {
  padding: 1rem;
  font-size: 1.1rem;
  font-weight: 700;
  border-bottom: 1px solid #2a3a5c;
}
.nav-links {
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0;
}
.nav-links a {
  color: #ccc;
  text-decoration: none;
  padding: 0.6rem 1rem;
  font-size: 0.95rem;
  transition: background 0.15s;
}
.nav-links a:hover { background: #16213e; color: #fff; }
.nav-links a.router-link-active { background: #16213e; color: #fff; font-weight: 600; }
</style>
