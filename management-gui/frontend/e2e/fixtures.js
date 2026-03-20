/**
 * Realistic mock data for Playwright E2E tests.
 * Mirrors the exact shapes returned by the Flask backend.
 */

export const TEAMS_MULTI = [
  { name: 'alpha', namespace: 'alpha-ns', cluster: 'cluster-east', stacks: ['stacks/stack-one.yaml'] },
  { name: 'beta', namespace: 'beta-ns', cluster: 'cluster-west', stacks: ['stacks/stack-two.yaml'] },
]

export const TEAMS_SINGLE = [
  { name: 'default', namespace: 'tekton-pipelines', cluster: 'default', stacks: [] },
]

export const STACKS = [
  {
    name: 'Demo Stack',
    stack_file: 'stacks/stack-one.yaml',
    apps: [
      { name: 'demo-fe', repo: 'git@github.com:jmjava/tekton-dag-vue-fe.git', role: 'consumer', propagationRole: 'originator' },
      { name: 'demo-api', repo: 'git@github.com:jmjava/tekton-dag-spring-boot.git', role: 'backend', propagationRole: 'forwarder' },
      { name: 'demo-db', repo: 'git@github.com:jmjava/tekton-dag-flask.git', role: 'datastore', propagationRole: 'terminal' },
    ],
  },
]

export const DAG = {
  nodes: [
    { id: 'demo-fe', role: 'consumer', propagationRole: 'originator', repo: 'git@github.com:jmjava/tekton-dag-vue-fe.git', build: 'npm', runtime: 'nginx' },
    { id: 'demo-api', role: 'backend', propagationRole: 'forwarder', repo: 'git@github.com:jmjava/tekton-dag-spring-boot.git', build: 'gradle', runtime: 'jvm' },
    { id: 'demo-db', role: 'datastore', propagationRole: 'terminal', repo: 'git@github.com:jmjava/tekton-dag-flask.git', build: 'pip', runtime: 'python' },
  ],
  edges: [
    { source: 'demo-fe', target: 'demo-api' },
    { source: 'demo-api', target: 'demo-db' },
  ],
}

function ts(minutesAgo) {
  return new Date(Date.now() - minutesAgo * 60000).toISOString()
}

export const PIPELINE_RUNS = {
  items: [
    { name: 'pr-run-001', pipeline: 'stack-pr-pipeline', status: 'Succeeded', startTime: ts(30), completionTime: ts(25), durationSeconds: 300, testSummary: '{"passed":12,"failed":0}', prNumber: '42', changedApp: 'demo-fe', namespace: 'alpha-ns' },
    { name: 'pr-run-002', pipeline: 'stack-pr-pipeline', status: 'Failed', startTime: ts(60), completionTime: ts(55), durationSeconds: 290, testSummary: '{"passed":10,"failed":2}', prNumber: '41', changedApp: 'demo-api', namespace: 'alpha-ns' },
    { name: 'bootstrap-run-003', pipeline: 'stack-bootstrap-pipeline', status: 'Running', startTime: ts(5), completionTime: null, durationSeconds: null, testSummary: null, prNumber: null, changedApp: null, namespace: 'alpha-ns' },
    { name: 'merge-run-004', pipeline: 'stack-merge-pipeline', status: 'Succeeded', startTime: ts(120), completionTime: ts(115), durationSeconds: 300, testSummary: null, prNumber: null, changedApp: 'demo-fe', namespace: 'alpha-ns' },
  ],
}

export const RUN_DETAIL = {
  name: 'pr-run-001',
  pipeline: 'stack-pr-pipeline',
  status: 'Succeeded',
  message: 'Tasks completed: 4 (Succeeded: 4, Cancelled: 0)',
  startTime: ts(30),
  completionTime: ts(25),
  durationSeconds: 300,
  testSummary: '{"passed":12,"failed":0,"skipped":1}',
  prNumber: '42',
  changedApp: 'demo-fe',
  namespace: 'alpha-ns',
  spec: {},
  statusFull: {},
}

export const TASKRUNS = {
  items: [
    { name: 'pr-run-001-build-task', pipelineRun: 'pr-run-001', task: 'build-task', status: 'Succeeded', message: null, startTime: ts(30), completionTime: ts(28) },
    { name: 'pr-run-001-test-task', pipelineRun: 'pr-run-001', task: 'test-task', status: 'Succeeded', message: null, startTime: ts(28), completionTime: ts(27) },
    { name: 'pr-run-001-deploy-task', pipelineRun: 'pr-run-001', task: 'deploy-task', status: 'Succeeded', message: null, startTime: ts(27), completionTime: ts(26) },
    { name: 'pr-run-001-integration-task', pipelineRun: 'pr-run-001', task: 'integration-task', status: 'Succeeded', message: null, startTime: ts(26), completionTime: ts(25) },
  ],
}

export const REPOS = {
  items: [
    { id: 'jmjava/tekton-dag-vue-fe', owner: 'jmjava', repo: 'tekton-dag-vue-fe', apps: ['demo-fe'], stacks: ['stacks/stack-one.yaml'] },
    { id: 'jmjava/tekton-dag-spring-boot', owner: 'jmjava', repo: 'tekton-dag-spring-boot', apps: ['demo-api'], stacks: ['stacks/stack-one.yaml'] },
    { id: 'jmjava/tekton-dag-flask', owner: 'jmjava', repo: 'tekton-dag-flask', apps: ['demo-db'], stacks: ['stacks/stack-one.yaml'] },
  ],
}

export const BRANCHES = {
  items: [
    { name: 'main', sha: 'abc1234567890def1234567890abcdef12345678' },
    { name: 'feature/new-widget', sha: 'def4567890abc1234567890def1234567890abcd' },
    { name: 'bugfix/login-fix', sha: '789abc1234567890def1234567890abcdef12345' },
  ],
}

export const TAGS = {
  items: [
    { name: 'v1.2.0', sha: '111aaa2222333bbb4444ccc5555ddd6666eee777' },
    { name: 'v1.1.0', sha: '888fff9999000aaa1111bbb2222ccc3333ddd444' },
  ],
}

export const COMMITS = {
  items: [
    { sha: 'abc1234567890def1234567890abcdef12345678', message: 'feat: add responsive layout', date: ts(1), url: 'https://github.com/jmjava/tekton-dag-vue-fe/commit/abc123' },
    { sha: 'def4567890abc1234567890def1234567890abcd', message: 'fix: correct API endpoint path', date: ts(120), url: 'https://github.com/jmjava/tekton-dag-vue-fe/commit/def456' },
    { sha: '789abc1234567890def1234567890abcdef12345', message: 'chore: update dependencies', date: ts(300), url: 'https://github.com/jmjava/tekton-dag-vue-fe/commit/789abc' },
  ],
}

export const PRS_REPO = {
  items: [
    { number: 42, title: 'Add dark mode support', state: 'open', url: 'https://github.com/jmjava/tekton-dag-vue-fe/pull/42' },
    { number: 40, title: 'Update CI config', state: 'open', url: 'https://github.com/jmjava/tekton-dag-vue-fe/pull/40' },
  ],
}

export const PRS_ALL = {
  items: [
    { repoId: 'jmjava/tekton-dag-vue-fe', pr: { number: 42, title: 'Add dark mode support', state: 'open', url: 'https://github.com/jmjava/tekton-dag-vue-fe/pull/42' } },
    { repoId: 'jmjava/tekton-dag-spring-boot', pr: { number: 15, title: 'Refactor auth module', state: 'open', url: 'https://github.com/jmjava/tekton-dag-spring-boot/pull/15' } },
  ],
  reposQueried: ['jmjava/tekton-dag-vue-fe', 'jmjava/tekton-dag-spring-boot', 'jmjava/tekton-dag-flask'],
  reposSkipped: [],
}

export const TRIGGER_SUCCESS = { ok: true, pipelineRun: 'pr-run-099', namespace: 'alpha-ns' }
