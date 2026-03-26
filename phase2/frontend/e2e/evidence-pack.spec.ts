import { test, expect } from '@playwright/test'

/**
 * Evidence Pack Dashboard E2E tests.
 * Uses stored auth state from auth.setup.ts.
 */
test.describe('Evidence Pack Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/evidence')
    // Wait for the lazy-loaded page to fully render
    await page.waitForLoadState('networkidle')
  })

  test('loads the Evidence Pack page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /evidence/i })).toBeVisible({ timeout: 15_000 })
  })

  test('execution history table is visible', async ({ page }) => {
    // Table should exist and contain rows
    const table = page.locator('table').first()
    await expect(table).toBeVisible({ timeout: 15_000 })
    const rows = table.locator('tbody tr')
    await expect(rows).toHaveCount({ minimum: 1 } as any, { timeout: 15_000 })
  })

  test('execution history table container is scrollable', async ({ page }) => {
    // The TableContainer should have overflow-y: auto and a max-height set
    // (This verifies the scrollable fix we deployed on Mar 24)
    const tableContainer = page.locator('table').first().locator('xpath=ancestor::div[contains(@class,"MuiTableContainer")]')
    const overflowY = await tableContainer.evaluate((el) => getComputedStyle(el).overflowY)
    expect(['auto', 'scroll']).toContain(overflowY)
  })

  test('shadow run progress is displayed', async ({ page }) => {
    // Look for the forecast count / shadow run progress text
    await expect(page.getByText(/forecast/i).first()).toBeVisible({ timeout: 15_000 })
  })
})
