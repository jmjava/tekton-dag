import { defineConfig } from '@playwright/test'

const TEST_PORT = 4173

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 0,
  use: {
    baseURL: `http://localhost:${TEST_PORT}`,
    headless: true,
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
  webServer: {
    command: `npx vite --port ${TEST_PORT}`,
    port: TEST_PORT,
    reuseExistingServer: false,
    timeout: 15000,
  },
})
