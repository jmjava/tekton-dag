<template>
  <span class="status-badge" :class="'status-' + status">{{ status }}</span>
</template>

<script setup>
defineProps({ status: { type: String, default: 'Unknown' } })
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 3px;
  font-size: 0.85rem;
  font-weight: 500;
}
.status-Succeeded { background: #d4edda; color: #155724; }
.status-Failed { background: #f8d7da; color: #721c24; }
.status-Running { background: #cce5ff; color: #004085; }
.status-Unknown { background: #e2e3e5; color: #383d41; }
</style>
