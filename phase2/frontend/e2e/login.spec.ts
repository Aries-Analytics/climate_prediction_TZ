import { test, expect } from '@playwright/test'

/**
 * Login flow tests — run without stored auth state.
 * These tests use a fresh browser context each time.
 */
test.use({ storageState: { cookies: [], origins: [] } })

test.describe('Login page', () => {
  test('shows login form', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByText('Climate Dashboard')).toBeVisible()
    await expect(page.getByLabel('Username')).toBeVisible()
    await expect(page.getByLabel('Password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible()
  })

  test('shows error on wrong credentials', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('wronguser')
    await page.getByLabel('Password').fill('wrongpass')
    await page.getByRole('button', { name: 'Sign In' }).click()
    await expect(page.getByRole('alert')).toBeVisible({ timeout: 10_000 })
  })

  test('redirects unauthenticated access to /login', async ({ page }) => {
    await page.goto('/dashboard/executive')
    await page.waitForURL('**/login', { timeout: 10_000 })
    await expect(page).toHaveURL(/login/)
  })

  test('successful login redirects to executive dashboard', async ({ page }) => {
    const user = process.env.TEST_USER ?? 'admin'
    const password = process.env.TEST_PASSWORD ?? ''

    await page.goto('/login')
    await page.getByLabel('Username').fill(user)
    await page.getByLabel('Password').fill(password)
    await page.getByRole('button', { name: 'Sign In' }).click()
    await page.waitForURL('**/dashboard/executive', { timeout: 15_000 })
    await expect(page).toHaveURL(/dashboard\/executive/)
  })
})
