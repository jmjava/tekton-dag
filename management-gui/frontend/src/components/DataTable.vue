<template>
  <table class="data-table">
    <thead>
      <tr>
        <th v-for="col in columns" :key="col.key">{{ col.label }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(row, i) in rows" :key="i">
        <td v-for="col in columns" :key="col.key">
          <slot :name="col.key" :row="row" :value="row[col.key]">
            {{ row[col.key] ?? '-' }}
          </slot>
        </td>
      </tr>
      <tr v-if="rows.length === 0">
        <td :colspan="columns.length" class="empty">{{ emptyText }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  emptyText: { type: String, default: 'No data.' },
})
</script>

<style scoped>
.data-table { width: 100%; border-collapse: collapse; }
.data-table th,
.data-table td { border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #f8f9fa; font-weight: 600; font-size: 0.9rem; }
.data-table tr:hover td { background: #f5f5f5; }
.empty { text-align: center; color: #888; padding: 1.5rem; }
</style>
