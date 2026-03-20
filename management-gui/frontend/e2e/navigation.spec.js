import { test, expect } from '@playwright/test'
import { mockApi } from './mock-api.js'

test.describe('App layout and navigation', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
  })

  test('renders sidebar with all nav links', async ({ page }) => {
    await page.goto('/')
    const sidebar = page.locator('aside.sidebar')
    await expect(sidebar).toBeVisible()
    await expect(sidebar.locator('.logo')).toContainText('Tekton DAG')

    const links = sidebar.locator('.nav-links a')
    await expect(links).toHaveCount(6)
    await expect(links.nth(0)).toContainText('Trigger')
    await expect(links.nth(1)).toContainText('Monitor')
    await expect(links.nth(2)).toContainText('Test results')
    await expect(links.nth(3)).toContainText('DAG')
    await expect(links.nth(4)).toContainText('Git')
    await expect(links.nth(5)).toContainText('Dashboard')
  })

  test('navigates to each view via sidebar links', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('Trigger')

    await page.click('text=Monitor')
    await expect(page.locator('h1')).toContainText('Monitor')
    await expect(page).toHaveURL(/\/monitor$/)

    await page.click('text=Test results')
    await expect(page.locator('h1')).toContainText('Test results')
    await expect(page).toHaveURL(/\/test-results$/)

    await page.locator('.nav-links a', { hasText: 'DAG' }).click()
    await expect(page.locator('h1')).toContainText('Stack DAG')
    await expect(page).toHaveURL(/\/dag$/)

    await page.locator('.nav-links a', { hasText: 'Git' }).click()
    await expect(page.locator('h1')).toContainText('Explore Git repos')
    await expect(page).toHaveURL(/\/git$/)

    await page.click('text=Dashboard')
    await expect(page.locator('h1')).toContainText('Tekton Dashboard')
    await expect(page).toHaveURL(/\/dashboard$/)
  })

  test('active nav link gets highlighted class', async ({ page }) => {
    await page.goto('/')
    const triggerLink = page.locator('.nav-links a', { hasText: 'Trigger' })
    await expect(triggerLink).toHaveClass(/router-link-active/)

    await page.click('text=Monitor')
    const monitorLink = page.locator('.nav-links a', { hasText: 'Monitor' })
    await expect(monitorLink).toHaveClass(/router-link-active/)
    await expect(triggerLink).not.toHaveClass(/router-link-active/)
  })

  test('page title updates per view', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/Trigger/)

    await page.click('text=Monitor')
    await expect(page).toHaveTitle(/Monitor/)

    await page.click('text=DAG')
    await expect(page).toHaveTitle(/DAG/)
  })

  test('direct URL navigation works', async ({ page }) => {
    await page.goto('/monitor')
    await expect(page.locator('h1')).toContainText('Monitor')

    await page.goto('/dag')
    await expect(page.locator('h1')).toContainText('Stack DAG')

    await page.goto('/git')
    await expect(page.locator('h1')).toContainText('Explore Git repos')
  })
})
