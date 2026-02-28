<template>
  <div class="app">
    <nav class="nav">
      <router-link to="/">Trigger</router-link>
      <router-link to="/monitor">Monitor</router-link>
      <router-link to="/test-results">Test results</router-link>
      <router-link to="/git">Git</router-link>
      <router-link to="/dashboard">Dashboard</router-link>
    </nav>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, sans-serif; }
  .app { min-height: 100vh; display: flex; flex-direction: column; }
  .nav {
    background: #1a1a2e;
    padding: 0.75rem 1rem;
    display: flex; gap: 1rem; flex-wrap: wrap;
  }
  .nav a {
    color: #eee;
    text-decoration: none;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }
  .nav a:hover, .nav a.router-link-active { background: #16213e; color: #fff; }
  .main { flex: 1; padding: 1rem; max-width: 1200px; margin: 0 auto; width: 100%; }
  h1 { margin-top: 0; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ccc; padding: 0.5rem; text-align: left; }
  th { background: #f5f5f5; }
  .status-Succeeded { color: green; }
  .status-Failed { color: #c00; }
  .status-Running { color: #07c; }
</style>
