import { defineConfig, devices } from '@playwright/test'

/**
 * HewaSense E2E Test Configuration
 *
 * Prerequisites before running:
 *   - Backend must be running (docker compose or local)
 *   - Set TEST_USER and TEST_PASSWORD env vars (or use defaults below)
 *
 * Usage:
 *   npm run test:e2e          — run all E2E tests (headless)
 *   npm run test:e2e:ui       — interactive Playwright UI
 *   npm run test:e2e:headed   — run with visible browser
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['line']],

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
  },

  projects: [
    // Auth setup runs first — saves session to e2e/.auth/user.json
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  // Auto-start the Vite dev server if not already running
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 30_000,
  },
})
