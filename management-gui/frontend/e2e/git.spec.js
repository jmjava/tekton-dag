import { test, expect } from '@playwright/test'
import { mockApi } from './mock-api.js'

test.describe('Git view', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
    await page.goto('/git')
  })

  test('renders repo table with all repos from stacks', async ({ page }) => {
    // The repos table comes AFTER the cross-repo PRs section
    const repoTable = page.locator('.data-table').nth(1)
    await expect(repoTable).toBeVisible()

    const rows = repoTable.locator('tbody tr')
    await expect(rows).toHaveCount(3)
    await expect(rows.nth(0)).toContainText('tekton-dag-vue-fe')
    await expect(rows.nth(1)).toContainText('tekton-dag-spring-boot')
    await expect(rows.nth(2)).toContainText('tekton-dag-flask')
  })

  test('each repo row shows associated apps and stacks', async ({ page }) => {
    const repoTable = page.locator('.data-table').nth(1)
    const firstRow = repoTable.locator('tbody tr').first()
    await expect(firstRow).toContainText('demo-fe')
    await expect(firstRow).toContainText('stacks/stack-one.yaml')
  })

  test('cross-repo PRs section loads and displays PRs', async ({ page }) => {
    const prsSection = page.locator('.all-prs-section')
    await expect(prsSection).toBeVisible()
    await expect(prsSection.locator('h2')).toContainText('Open PRs')

    const prRows = prsSection.locator('.data-table tbody tr')
    await expect(prRows).toHaveCount(2)
    await expect(prRows.nth(0)).toContainText('tekton-dag-vue-fe')
    await expect(prRows.nth(0)).toContainText('#42')
    await expect(prRows.nth(1)).toContainText('tekton-dag-spring-boot')
  })

  test('cross-repo PR state filter works', async ({ page }) => {
    const stateSelect = page.locator('.prs-filter select')
    await expect(stateSelect).toHaveValue('open')

    await stateSelect.selectOption('closed')
    // The mock always returns the same data, but we verify the select fires
    await expect(stateSelect).toHaveValue('closed')
  })

  test('clicking Browse opens repo detail with branches tab', async ({ page }) => {
    await page.click('button >> text=Browse')
    const detail = page.locator('.repo-detail')
    await expect(detail).toBeVisible()

    const branchItems = detail.locator('ul li')
    await expect(branchItems).toHaveCount(3)
    await expect(branchItems.nth(0)).toContainText('main')
    await expect(branchItems.nth(1)).toContainText('feature/new-widget')
  })

  test('switching tabs in repo detail loads tags', async ({ page }) => {
    await page.click('button >> text=Browse')
    const detail = page.locator('.repo-detail')

    await detail.locator('button', { hasText: 'tags' }).click()
    const items = detail.locator('ul li')
    await expect(items).toHaveCount(2)
    await expect(items.nth(0)).toContainText('v1.2.0')
  })

  test('commits tab shows commit messages with short sha', async ({ page }) => {
    await page.click('button >> text=Browse')
    const detail = page.locator('.repo-detail')

    await detail.locator('button', { hasText: 'commits' }).click()
    const items = detail.locator('ul li')
    await expect(items).toHaveCount(3)
    await expect(items.nth(0)).toContainText('feat: add responsive layout')
    await expect(items.nth(0)).toContainText('abc1234')
  })

  test('prs tab shows PR table', async ({ page }) => {
    await page.click('button >> text=Browse')
    const detail = page.locator('.repo-detail')

    await detail.locator('button', { hasText: 'prs' }).click()
    const prTable = detail.locator('.data-table')
    await expect(prTable).toBeVisible()
    await expect(prTable.locator('tbody tr')).toHaveCount(2)
    await expect(prTable).toContainText('#42')
  })

  test('close button hides repo detail', async ({ page }) => {
    await page.click('button >> text=Browse')
    await expect(page.locator('.repo-detail')).toBeVisible()

    await page.locator('.repo-detail button', { hasText: 'Close' }).click()
    await expect(page.locator('.repo-detail')).not.toBeVisible()
  })
})
