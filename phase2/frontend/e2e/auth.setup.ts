import { test as setup, expect } from '@playwright/test'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const authFile = path.join(__dirname, '.auth/user.json')

/**
 * Logs in once and saves the auth token to e2e/.auth/user.json.
 * All other test projects depend on this setup step.
 *
 * Set credentials via env vars:
 *   TEST_USER=admin TEST_PASSWORD=yourpassword npm run test:e2e
 */
setup('authenticate', async ({ page }) => {
  const user = process.env.TEST_USER ?? 'admin'
  const password = process.env.TEST_PASSWORD ?? ''

  await page.goto('/login')
  await expect(page.getByText('Climate Dashboard')).toBeVisible()

  await page.getByLabel('Username').fill(user)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign In' }).click()

  // Wait for redirect to executive dashboard
  await page.waitForURL('**/dashboard/executive', { timeout: 15_000 })
  await expect(page).toHaveURL(/dashboard\/executive/)

  // Persist auth state (JWT in localStorage/cookies)
  await page.context().storageState({ path: authFile })
})
