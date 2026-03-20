import { test, expect } from '@playwright/test'
import { mockApi } from './mock-api.js'
import { PIPELINE_RUNS } from './fixtures.js'

test.describe('Monitor view', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
    await page.goto('/monitor')
  })

  test('renders table with pipeline runs', async ({ page }) => {
    const table = page.locator('.data-table')
    await expect(table).toBeVisible()

    const headers = table.locator('th')
    await expect(headers.nth(0)).toContainText('Name')
    await expect(headers.nth(1)).toContainText('Pipeline')
    await expect(headers.nth(2)).toContainText('Status')

    const rows = table.locator('tbody tr')
    await expect(rows).toHaveCount(PIPELINE_RUNS.items.length)
  })

  test('each run name is a link to its detail page', async ({ page }) => {
    const firstRunLink = page.locator('.data-table a', { hasText: 'pr-run-001' })
    await expect(firstRunLink).toHaveAttribute('href', '/monitor/pr-run-001')
  })

  test('status badges render for each run', async ({ page }) => {
    const badges = page.locator('.data-table .status-badge, .data-table span')
    const firstRow = page.locator('.data-table tbody tr').first()
    await expect(firstRow).toContainText('Succeeded')
  })

  test('clicking a run name navigates to run detail', async ({ page }) => {
    await page.click('.data-table a >> text=pr-run-001')
    await expect(page).toHaveURL(/\/monitor\/pr-run-001/)
    await expect(page.locator('h1')).toContainText('pr-run-001')
  })

  test('empty state shows message when no runs', async ({ page }) => {
    await mockApi(page, { pipelineRuns: { items: [] } })
    await page.goto('/monitor')
    await expect(page.locator('.empty')).toContainText('No pipeline runs found')
  })
})

test.describe('Run Detail view', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('shows run details and taskruns table', async ({ page }) => {
    await page.goto('/monitor/pr-run-001')
    await expect(page.locator('h1')).toContainText('pr-run-001')
    await expect(page.locator('text=stack-pr-pipeline')).toBeVisible()
    await expect(page.locator('.status-badge').first()).toContainText('Succeeded')

    const taskTable = page.locator('.data-table')
    await expect(taskTable).toBeVisible()
    const taskRows = taskTable.locator('tbody tr')
    await expect(taskRows).toHaveCount(4)
    await expect(taskRows.first()).toContainText('build-task')
  })

  test('shows test results section when testSummary exists', async ({ page }) => {
    await page.goto('/monitor/pr-run-001')
    await expect(page.locator('h2', { hasText: 'Test results' })).toBeVisible()
    await expect(page.locator('.test-summary')).toContainText('passed')
    await expect(page.locator('.test-summary')).toContainText('12')
  })

  test('back link navigates to monitor', async ({ page }) => {
    await page.goto('/monitor/pr-run-001')
    await page.click('text=← Back to Monitor')
    await expect(page).toHaveURL(/\/monitor$/)
  })

  test('404 run shows error', async ({ page }) => {
    await page.goto('/monitor/nonexistent-run')
    await expect(page.locator('.error')).toBeVisible()
  })
})
