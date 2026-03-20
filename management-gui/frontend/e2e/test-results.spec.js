import { test, expect } from '@playwright/test'
import { mockApi } from './mock-api.js'

test.describe('Test Results view', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
    await page.goto('/test-results')
  })

  test('renders filter dropdown with three options', async ({ page }) => {
    const filterSelect = page.locator('.filters select')
    await expect(filterSelect).toBeVisible()

    const options = filterSelect.locator('option')
    await expect(options).toHaveCount(3)
    await expect(options.nth(0)).toHaveText('Last 50 runs')
    await expect(options.nth(1)).toHaveText('Failed in last 24h')
    await expect(options.nth(2)).toHaveText('Last 20 succeeded')
  })

  test('default "Last 50" filter shows all runs', async ({ page }) => {
    const rows = page.locator('.data-table tbody tr')
    await expect(rows).toHaveCount(4)
  })

  test('"Failed in last 24h" filter narrows to failed runs', async ({ page }) => {
    const filterSelect = page.locator('.filters select')
    await filterSelect.selectOption('failed24')

    const rows = page.locator('.data-table tbody tr')
    await expect(rows).toHaveCount(1)
    await expect(rows.first()).toContainText('Failed')
  })

  test('"Last 20 succeeded" filter narrows to succeeded runs', async ({ page }) => {
    const filterSelect = page.locator('.filters select')
    await filterSelect.selectOption('succeeded')

    const rows = page.locator('.data-table tbody tr')
    await expect(rows).toHaveCount(2) // pr-run-001 + merge-run-004
    for (const row of await rows.all()) {
      await expect(row).toContainText('Succeeded')
    }
  })

  test('table headers include Test summary column', async ({ page }) => {
    const table = page.locator('.data-table').first()
    const headers = table.locator('th')
    await expect(headers).toHaveCount(5)
    const texts = await headers.allTextContents()
    expect(texts).toContain('Test summary')
  })

  test('run name links to run detail', async ({ page }) => {
    const link = page.locator('.data-table a', { hasText: 'pr-run-001' })
    await expect(link).toHaveAttribute('href', '/monitor/pr-run-001')
  })

  test('empty state when no runs match filter', async ({ page }) => {
    await mockApi(page, { pipelineRuns: { items: [] } })
    await page.goto('/test-results')
    await expect(page.locator('.empty')).toContainText('No runs match')
  })
})
