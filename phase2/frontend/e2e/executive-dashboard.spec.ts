import { test, expect } from '@playwright/test'

/**
 * Executive Dashboard E2E tests — the main post-login landing page.
 * Uses stored auth state from auth.setup.ts.
 */
test.describe('Executive Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/executive')
    await page.waitForLoadState('networkidle')
  })

  test('loads without errors', async ({ page }) => {
    // No error boundary / crash page visible
    await expect(page.getByText(/something went wrong/i)).not.toBeVisible({ timeout: 10_000 })
    await expect(page.getByText(/error/i).first()).not.toBeVisible()
  })

  test('navigation sidebar is present', async ({ page }) => {
    // App layout sidebar should be visible
    await expect(page.locator('nav, [role="navigation"]').first()).toBeVisible({ timeout: 10_000 })
  })

  test('can navigate to Evidence Pack dashboard', async ({ page }) => {
    // Click evidence/shadow run link in sidebar
    await page.getByRole('link', { name: /evidence/i }).click()
    await page.waitForURL('**/dashboard/evidence', { timeout: 10_000 })
    await expect(page).toHaveURL(/dashboard\/evidence/)
  })

  test('can navigate to Triggers dashboard', async ({ page }) => {
    await page.getByRole('link', { name: /trigger/i }).click()
    await page.waitForURL('**/dashboard/triggers', { timeout: 10_000 })
    await expect(page).toHaveURL(/dashboard\/triggers/)
  })
})
