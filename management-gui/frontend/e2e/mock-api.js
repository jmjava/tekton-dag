import * as F from './fixtures.js'

/**
 * Set up standard API mocks so the Vue app works without a real backend.
 * Uses a single catch-all route with path-based dispatch for reliable
 * interception through the Vite proxy.
 */
export async function mockApi(page, overrides = {}) {
  const teams = overrides.teams ?? F.TEAMS_MULTI

  await page.route(/\/api\//, (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname
    const method = route.request().method()

    // GET /api/health
    if (path === '/api/health') {
      return route.fulfill({ json: { ok: true } })
    }

    // GET /api/teams
    if (path === '/api/teams') {
      return route.fulfill({ json: teams })
    }

    // GET /api/prs (cross-repo)
    if (path === '/api/prs') {
      return route.fulfill({ json: overrides.prsAll ?? F.PRS_ALL })
    }

    // GET /api/repos (list all)
    if (path === '/api/repos') {
      return route.fulfill({ json: overrides.repos ?? F.REPOS })
    }

    // POST /api/teams/:team/trigger
    const triggerMatch = path.match(/^\/api\/teams\/([^/]+)\/trigger$/)
    if (triggerMatch && method === 'POST') {
      if (triggerMatch[1] === 'nonexistent') {
        return route.fulfill({ status: 404, json: { error: 'Unknown team: nonexistent' } })
      }
      const body = JSON.parse(route.request().postData() || '{}')
      if (!body.pipelineType || !['pr', 'bootstrap', 'merge'].includes(body.pipelineType)) {
        return route.fulfill({ status: 400, json: { error: 'pipelineType must be pr, bootstrap, or merge' } })
      }
      if (!body.stack) {
        return route.fulfill({ status: 400, json: { error: 'stack is required' } })
      }
      if (body.pipelineType === 'pr' && !body.prNumber) {
        return route.fulfill({ status: 400, json: { error: 'prNumber required for PR runs' } })
      }
      return route.fulfill({ json: overrides.triggerResult ?? F.TRIGGER_SUCCESS })
    }

    // GET /api/teams/:team/stacks/:stack_file/dag
    const dagMatch = path.match(/^\/api\/teams\/([^/]+)\/stacks\/(.+)\/dag$/)
    if (dagMatch) {
      if (dagMatch[1] === 'nonexistent') {
        return route.fulfill({ status: 404, json: { error: `Unknown team: ${dagMatch[1]}` } })
      }
      return route.fulfill({ json: overrides.dag ?? F.DAG })
    }

    // GET /api/teams/:team/stacks
    const stacksMatch = path.match(/^\/api\/teams\/([^/]+)\/stacks$/)
    if (stacksMatch) {
      if (stacksMatch[1] === 'nonexistent' || stacksMatch[1] === 'nonexistent-team-xyz') {
        return route.fulfill({ status: 404, json: { error: `Unknown team: ${stacksMatch[1]}` } })
      }
      return route.fulfill({ json: overrides.stacks ?? F.STACKS })
    }

    // GET /api/teams/:team/taskruns
    const taskrunsMatch = path.match(/^\/api\/teams\/([^/]+)\/taskruns$/)
    if (taskrunsMatch) {
      if (taskrunsMatch[1] === 'nonexistent') {
        return route.fulfill({ status: 404, json: { error: `Unknown team: ${taskrunsMatch[1]}` } })
      }
      return route.fulfill({ json: overrides.taskruns ?? F.TASKRUNS })
    }

    // GET /api/teams/:team/pipelineruns/:name (detail - must be before list)
    const runDetailMatch = path.match(/^\/api\/teams\/([^/]+)\/pipelineruns\/([^/]+)$/)
    if (runDetailMatch) {
      if (runDetailMatch[1] === 'nonexistent') {
        return route.fulfill({ status: 404, json: { error: `Unknown team: ${runDetailMatch[1]}` } })
      }
      if (runDetailMatch[2] === 'pr-run-001') {
        return route.fulfill({ json: overrides.runDetail ?? F.RUN_DETAIL })
      }
      return route.fulfill({ status: 404, json: { error: 'PipelineRun not found' } })
    }

    // GET /api/teams/:team/pipelineruns (list)
    const runsMatch = path.match(/^\/api\/teams\/([^/]+)\/pipelineruns$/)
    if (runsMatch) {
      if (runsMatch[1] === 'nonexistent') {
        return route.fulfill({ status: 404, json: { error: `Unknown team: ${runsMatch[1]}` } })
      }
      return route.fulfill({ json: overrides.pipelineRuns ?? F.PIPELINE_RUNS })
    }

    // GET /api/repos/:owner/:repo/branches
    if (path.match(/^\/api\/repos\/[^/]+\/[^/]+\/branches$/)) {
      return route.fulfill({ json: overrides.branches ?? F.BRANCHES })
    }

    // GET /api/repos/:owner/:repo/tags
    if (path.match(/^\/api\/repos\/[^/]+\/[^/]+\/tags$/)) {
      return route.fulfill({ json: overrides.tags ?? F.TAGS })
    }

    // GET /api/repos/:owner/:repo/commits
    if (path.match(/^\/api\/repos\/[^/]+\/[^/]+\/commits$/)) {
      return route.fulfill({ json: overrides.commits ?? F.COMMITS })
    }

    // GET /api/repos/:owner/:repo/prs
    if (path.match(/^\/api\/repos\/[^/]+\/[^/]+\/prs$/)) {
      return route.fulfill({ json: overrides.prsRepo ?? F.PRS_REPO })
    }

    // Unmatched API route — return 404 to surface problems clearly
    return route.fulfill({ status: 404, json: { error: `Mock not found: ${method} ${path}` } })
  })
}

/**
 * Mock API but have all endpoints return 500 to simulate backend outage.
 */
export async function mockApiDown(page) {
  await page.route(/\/api\//, (route) =>
    route.fulfill({ status: 500, json: { error: 'Internal server error' } })
  )
}

/**
 * Mock API with empty data to test empty states.
 */
export async function mockApiEmpty(page) {
  await mockApi(page, {
    stacks: [],
    pipelineRuns: { items: [] },
    taskruns: { items: [] },
    repos: { items: [] },
    prsAll: { items: [], reposQueried: [], reposSkipped: [] },
    dag: { nodes: [], edges: [] },
  })
}
