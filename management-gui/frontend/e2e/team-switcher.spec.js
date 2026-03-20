import { test, expect } from '@playwright/test'
import { mockApi } from './mock-api.js'
import { TEAMS_MULTI, TEAMS_SINGLE } from './fixtures.js'

test.describe('Team Switcher — multi-team', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page, { teams: TEAMS_MULTI })
    await page.goto('/')
  })

  test('team switcher is visible when multiple teams', async ({ page }) => {
    const switcher = page.locator('.team-switcher')
    await expect(switcher).toBeVisible()
    await expect(switcher.locator('label')).toContainText('Team')
  })

  test('dropdown lists all teams with cluster context', async ({ page }) => {
    const options = page.locator('.team-switcher select option')
    await expect(options).toHaveCount(2)
    await expect(options.nth(0)).toContainText('alpha')
    await expect(options.nth(0)).toContainText('cluster-east')
    await expect(options.nth(1)).toContainText('beta')
    await expect(options.nth(1)).toContainText('cluster-west')
  })

  test('first team is auto-selected on load', async ({ page }) => {
    const select = page.locator('.team-switcher select')
    await expect(select).toHaveValue('alpha')
  })

  test('switching team reloads stacks in trigger view', async ({ page }) => {
    const apiCalls = []
    await page.route('**/api/teams/*/stacks', (route) => {
      apiCalls.push(route.request().url())
      route.fulfill({ json: [] })
    })

    const select = page.locator('.team-switcher select')
    await select.selectOption('beta')

    // Wait for the new API call triggered by team switch
    await page.waitForTimeout(500)
    const betaCalls = apiCalls.filter(u => u.includes('/teams/beta/'))
    expect(betaCalls.length).toBeGreaterThan(0)
  })

  test('switching team reloads monitor data', async ({ page }) => {
    await page.locator('.nav-links a', { hasText: 'Monitor' }).click()
    await page.waitForTimeout(300)

    const apiCalls = []
    page.on('request', (req) => {
      if (req.url().includes('/api/teams/beta/')) {
        apiCalls.push(req.url())
      }
    })

    const select = page.locator('.team-switcher select')
    await select.selectOption('beta')

    await page.waitForTimeout(1000)
    expect(apiCalls.length).toBeGreaterThan(0)
  })
})

test.describe('Team Switcher — single-team', () => {
  test('team switcher is hidden when only one team', async ({ page }) => {
    await mockApi(page, { teams: TEAMS_SINGLE })
    await page.goto('/')
    await expect(page.locator('.team-switcher')).not.toBeVisible()
  })

  test('single team still loads data correctly', async ({ page }) => {
    await mockApi(page, { teams: TEAMS_SINGLE })
    await page.goto('/monitor')
    const table = page.locator('.data-table')
    await expect(table).toBeVisible()
  })
})
