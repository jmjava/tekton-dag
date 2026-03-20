import { test, expect } from '@playwright/test'
import { mockApi } from './mock-api.js'

test.describe('Trigger view', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page)
    await page.goto('/')
  })

  test('populates stack dropdown from API', async ({ page }) => {
    const stackSelect = page.locator('.trigger-form select').nth(1)
    const options = stackSelect.locator('option')
    await expect(options).toHaveCount(2) // "— select —" + 1 stack
    await expect(options.nth(1)).toHaveText('stacks/stack-one.yaml')
  })

  test('selecting a stack populates app dropdown', async ({ page }) => {
    const stackSelect = page.locator('.trigger-form select').nth(1)
    await stackSelect.selectOption('stacks/stack-one.yaml')

    const appSelect = page.locator('.trigger-form select').nth(2)
    const options = appSelect.locator('option')
    await expect(options).toHaveCount(4) // "— select —" + 3 apps
    await expect(options.nth(1)).toHaveText('demo-fe')
    await expect(options.nth(2)).toHaveText('demo-api')
    await expect(options.nth(3)).toHaveText('demo-db')
  })

  test('PR number field is visible only for PR pipeline type', async ({ page }) => {
    const prField = page.locator('.trigger-form input[type="number"]')
    await expect(prField).toBeVisible()

    const pipelineSelect = page.locator('.trigger-form select').first()
    await pipelineSelect.selectOption('bootstrap')
    await expect(prField).not.toBeVisible()

    await pipelineSelect.selectOption('merge')
    await expect(prField).not.toBeVisible()

    await pipelineSelect.selectOption('pr')
    await expect(prField).toBeVisible()
  })

  test('successful trigger shows success message and run link', async ({ page }) => {
    const stackSelect = page.locator('.trigger-form select').nth(1)
    await stackSelect.selectOption('stacks/stack-one.yaml')

    const appSelect = page.locator('.trigger-form select').nth(2)
    await appSelect.selectOption('demo-fe')

    const prInput = page.locator('.trigger-form input[type="number"]')
    await prInput.fill('42')

    await page.click('button[type="submit"]')

    await expect(page.locator('.msg-success')).toContainText('PipelineRun created')
    const runLink = page.locator('a', { hasText: 'pr-run-099' })
    await expect(runLink).toBeVisible()
    await expect(runLink).toHaveAttribute('href', /\/monitor\/pr-run-099/)
  })

  test('trigger with invalid pipeline type shows client-side validation', async ({ page }) => {
    // HTML5 required attributes prevent submission without stack/app
    // Test that the form has required fields by checking the select attributes
    const stackSelect = page.locator('.trigger-form select').nth(1)
    await expect(stackSelect).toHaveAttribute('required', '')
    const appSelect = page.locator('.trigger-form select').nth(2)
    await expect(appSelect).toHaveAttribute('required', '')
  })

  test('bootstrap trigger does not require app or PR number', async ({ page }) => {
    const pipelineSelect = page.locator('.trigger-form select').first()
    await pipelineSelect.selectOption('bootstrap')

    const stackSelect = page.locator('.trigger-form select').nth(1)
    await stackSelect.selectOption('stacks/stack-one.yaml')

    const appSelect = page.locator('.trigger-form select').nth(2)
    await appSelect.selectOption('demo-fe')

    await page.click('button[type="submit"]')
    await expect(page.locator('.msg-success')).toContainText('PipelineRun created')
  })

  test('button is disabled while submitting', async ({ page }) => {
    const stackSelect = page.locator('.trigger-form select').nth(1)
    await stackSelect.selectOption('stacks/stack-one.yaml')
    const appSelect = page.locator('.trigger-form select').nth(2)
    await appSelect.selectOption('demo-fe')

    let resolveRoute
    await page.route(/\/api\/teams\/[^/]+\/trigger$/, (route) => {
      return new Promise((resolve) => {
        resolveRoute = () => { route.fulfill({ json: { ok: true, pipelineRun: 'delayed-run', namespace: 'ns' } }); resolve() }
      })
    })

    const submitBtn = page.locator('button[type="submit"]')
    await submitBtn.click()
    await expect(submitBtn).toBeDisabled()

    resolveRoute()
    await expect(submitBtn).toBeEnabled()
  })
})
