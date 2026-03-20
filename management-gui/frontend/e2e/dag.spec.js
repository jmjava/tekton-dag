import { test, expect } from '@playwright/test'
import { mockApi, mockApiEmpty } from './mock-api.js'

test.describe('DAG view', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
    await page.goto('/dag')
  })

  test('shows stack dropdown populated from API', async ({ page }) => {
    const select = page.locator('.controls select')
    const options = select.locator('option')
    await expect(options).toHaveCount(2) // "— select —" + 1 stack
    await expect(options.nth(1)).toContainText('Demo Stack')
  })

  test('shows prompt before a stack is selected', async ({ page }) => {
    await expect(page.locator('.muted')).toContainText('Select a stack')
  })

  test('selecting a stack renders the DAG container', async ({ page }) => {
    const select = page.locator('.controls select')
    await select.selectOption('stacks/stack-one.yaml')

    const dagContainer = page.locator('.dag-container')
    await expect(dagContainer).toBeVisible()
  })

  test('DAG renders correct number of nodes', async ({ page }) => {
    await page.locator('.controls select').selectOption('stacks/stack-one.yaml')

    const nodes = page.locator('.dag-node')
    await expect(nodes).toHaveCount(3)
  })

  test('nodes display correct names', async ({ page }) => {
    await page.locator('.controls select').selectOption('stacks/stack-one.yaml')

    await expect(page.locator('.node-name', { hasText: 'demo-fe' })).toBeVisible()
    await expect(page.locator('.node-name', { hasText: 'demo-api' })).toBeVisible()
    await expect(page.locator('.node-name', { hasText: 'demo-db' })).toBeVisible()
  })

  test('nodes display role metadata', async ({ page }) => {
    await page.locator('.controls select').selectOption('stacks/stack-one.yaml')

    await expect(page.locator('.node-meta').first()).toBeVisible()
    const allMeta = await page.locator('.node-meta').allTextContents()
    expect(allMeta.some(m => m.includes('consumer'))).toBeTruthy()
    expect(allMeta.some(m => m.includes('backend'))).toBeTruthy()
    expect(allMeta.some(m => m.includes('datastore'))).toBeTruthy()
  })

  test('nodes have propagation role CSS classes', async ({ page }) => {
    await page.locator('.controls select').selectOption('stacks/stack-one.yaml')

    await expect(page.locator('.role-originator')).toBeVisible()
    await expect(page.locator('.role-forwarder')).toBeVisible()
    await expect(page.locator('.role-terminal')).toBeVisible()
  })

  test('empty stacks list shows only the placeholder option', async ({ page }) => {
    await mockApiEmpty(page)
    await page.goto('/dag')
    const select = page.locator('.controls select')
    const options = select.locator('option')
    await expect(options).toHaveCount(1) // only "— select —"
    await expect(page.locator('.muted')).toContainText('Select a stack')
  })
})
