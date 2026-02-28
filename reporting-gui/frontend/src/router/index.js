import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  { path: '/', name: 'Trigger', component: () => import('../views/TriggerView.vue'), meta: { title: 'Trigger' } },
  { path: '/monitor', name: 'Monitor', component: () => import('../views/MonitorView.vue'), meta: { title: 'Monitor' } },
  { path: '/monitor/:name', name: 'RunDetail', component: () => import('../views/RunDetailView.vue'), meta: { title: 'Run detail' } },
  { path: '/test-results', name: 'TestResults', component: () => import('../views/TestResultsView.vue'), meta: { title: 'Test results' } },
  { path: '/git', name: 'Git', component: () => import('../views/GitView.vue'), meta: { title: 'Git' } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: 'Dashboard' } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.afterEach((to) => {
  document.title = to.meta?.title ? `${to.meta.title} — Tekton DAG` : 'Tekton DAG Reporting';
});

export default router;
