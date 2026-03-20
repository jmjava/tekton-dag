import { test, expect } from '@playwright/test'
import { mockApi, mockApiDown, mockApiEmpty } from './mock-api.js'

test.describe('Error handling — backend down', () => {
  test('trigger view shows error when API call fails', async ({ page }) => {
    await mockApiDown(page)
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('Trigger')
  })

  test('monitor view shows error message on API failure', async ({ page }) => {
    await page.route(/\/api\//, (route) => {
      const path = new URL(route.request().url()).pathname
      if (path === '/api/teams') {
        return route.fulfill({ json: [{ name: 'alpha', namespace: 'ns', cluster: 'default', stacks: [] }] })
      }
      if (path.includes('/pipelineruns')) {
        return route.fulfill({ status: 500, json: { error: 'k8s cluster unreachable' } })
      }
      return route.fulfill({ json: {} })
    })
    await page.goto('/monitor')
    await expect(page.locator('.error')).toBeVisible()
  })

  test('git view shows error when repos API fails', async ({ page }) => {
    await page.route(/\/api\//, (route) => {
      const path = new URL(route.request().url()).pathname
      if (path === '/api/teams') {
        return route.fulfill({ json: [{ name: 'alpha', namespace: 'ns', cluster: 'default', stacks: [] }] })
      }
      if (path === '/api/repos') {
        return route.fulfill({ status: 500, json: { error: 'Internal error' } })
      }
      if (path === '/api/prs') {
        return route.fulfill({ json: { items: [], reposQueried: [], reposSkipped: [] } })
      }
      return route.fulfill({ json: {} })
    })
    await page.goto('/git')
    await expect(page.locator('.error')).toBeVisible()
  })

  test('DAG view shows error when dag endpoint fails', async ({ page }) => {
    await page.route(/\/api\//, (route) => {
      const path = new URL(route.request().url()).pathname
      if (path === '/api/teams') {
        return route.fulfill({ json: [{ name: 'alpha', namespace: 'ns', cluster: 'default', stacks: [] }] })
      }
      if (path.match(/\/stacks$/)) {
        return route.fulfill({ json: [{ name: 'Demo', stack_file: 'stacks/stack-one.yaml', apps: [] }] })
      }
      if (path.includes('/dag')) {
        return route.fulfill({ status: 500, json: { error: 'Stack parse error' } })
      }
      return route.fulfill({ json: {} })
    })
    await page.goto('/dag')
    await page.locator('.controls select').selectOption('stacks/stack-one.yaml')
    await expect(page.locator('.error')).toBeVisible()
  })
})

test.describe('Error handling — empty data', () => {
  test.beforeEach(async ({ page }) => {
    await mockApiEmpty(page)
  })

  test('monitor shows empty state with no runs', async ({ page }) => {
    await page.goto('/monitor')
    await expect(page.locator('.empty')).toContainText('No pipeline runs')
  })

  test('test results shows empty state with no matching runs', async ({ page }) => {
    await page.goto('/test-results')
    await expect(page.locator('.empty')).toContainText('No runs match')
  })

  test('trigger view has no stack options when stacks are empty', async ({ page }) => {
    await page.goto('/')
    const stackSelect = page.locator('.trigger-form select').nth(1)
    const options = stackSelect.locator('option')
    await expect(options).toHaveCount(1) // only "— select —"
  })

  test('git view shows no repos message', async ({ page }) => {
    await page.goto('/git')
    await expect(page.locator('.muted')).toContainText('No PRs found')
  })
})

test.describe('Error handling — network timeout', () => {
  test('trigger submit handles slow API gracefully', async ({ page }) => {
    await mockApi(page)
    await page.goto('/')

    await page.route(/\/api\/teams\/[^/]+\/trigger$/, (route) =>
      route.abort('timedout')
    )

    await page.locator('.trigger-form select').nth(1).selectOption('stacks/stack-one.yaml')
    await page.locator('.trigger-form select').nth(2).selectOption('demo-fe')
    await page.click('button[type="submit"]')

    await expect(page.locator('.msg-error')).toBeVisible()
  })
})
