import { test, expect } from '@playwright/test'
import { mockApi } from './mock-api.js'

test.describe('Dashboard view', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
    await page.goto('/dashboard')
  })

  test('shows URL input and view controls', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Tekton Dashboard')
    const urlInput = page.locator('input[placeholder="http://localhost:9097"]')
    await expect(urlInput).toBeVisible()

    const viewSelect = page.locator('.controls select')
    await expect(viewSelect).toBeVisible()
    await expect(viewSelect.locator('option')).toHaveCount(2)
  })

  test('no iframe shown when URL is empty', async ({ page }) => {
    await expect(page.locator('.muted')).toContainText('Enter a Dashboard base URL')
    await expect(page.locator('iframe')).not.toBeVisible()
  })

  test('entering a URL renders iframe', async ({ page }) => {
    const urlInput = page.locator('input[placeholder="http://localhost:9097"]')
    await urlInput.fill('http://tekton-dashboard.example.com')

    const iframe = page.locator('iframe.dashboard-iframe')
    await expect(iframe).toBeVisible()
    const src = await iframe.getAttribute('src')
    expect(src).toContain('http://tekton-dashboard.example.com')
    expect(src).toContain('pipelineruns')
  })

  test('list view constructs correct iframe URL', async ({ page }) => {
    await page.locator('input[placeholder="http://localhost:9097"]').fill('http://dash.local')
    const iframe = page.locator('iframe')
    const src = await iframe.getAttribute('src')
    expect(src).toBe('http://dash.local/#/namespaces/tekton-pipelines/pipelineruns')
  })

  test('detail view shows namespace and run name inputs', async ({ page }) => {
    await page.locator('input[placeholder="http://localhost:9097"]').fill('http://dash.local')
    const viewSelect = page.locator('.controls select')
    await viewSelect.selectOption('detail')

    const nsInput = page.locator('input[placeholder="tekton-pipelines"]')
    await expect(nsInput).toBeVisible()

    const runInput = page.locator('.controls input[type="text"]').last()
    await expect(runInput).toBeVisible()
  })

  test('detail view constructs correct URL with run name', async ({ page }) => {
    await page.locator('input[placeholder="http://localhost:9097"]').fill('http://dash.local')

    const viewSelect = page.locator('.controls select')
    await viewSelect.selectOption('detail')

    const runInput = page.locator('.controls input[type="text"]').last()
    await runInput.fill('my-pipeline-run-001')

    const iframe = page.locator('iframe')
    const src = await iframe.getAttribute('src')
    expect(src).toContain('/pipelineruns/my-pipeline-run-001')
    expect(src).toContain('/namespaces/tekton-pipelines/')
  })

  test('"Open in new tab" link has matching href', async ({ page }) => {
    await page.locator('input[placeholder="http://localhost:9097"]').fill('http://dash.local')

    const link = page.locator('a', { hasText: 'Open in new tab' })
    await expect(link).toBeVisible()
    const href = await link.getAttribute('href')
    expect(href).toContain('http://dash.local')
  })

  test('query param ?run= pre-fills run detail view', async ({ page }) => {
    await page.goto('/dashboard?run=auto-run-123&namespace=custom-ns')
    await page.locator('input[placeholder="http://localhost:9097"]').fill('http://dash.local')

    const iframe = page.locator('iframe')
    const src = await iframe.getAttribute('src')
    expect(src).toContain('/namespaces/custom-ns/pipelineruns/auto-run-123')
  })
})
