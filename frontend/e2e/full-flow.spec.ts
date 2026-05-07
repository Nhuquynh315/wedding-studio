import { test, expect } from '@playwright/test'

test('register → create wedding → add guest → see on dashboard', async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`
  const password = 'testpass123'

  // ── Register ─────────────────────────────────────────────────────
  await page.goto('/register')
  await page.getByLabel('Name').fill('E2E Test User')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByLabel('Confirm password').fill(password)
  await page.getByRole('button', { name: /sign up/i }).click()

  // After register, lands on dashboard empty state
  await expect(page.getByRole('heading', { name: /welcome to wedding studio/i })).toBeVisible()

  // ── Create wedding ────────────────────────────────────────────────
  await page.getByRole('button', { name: /create your first wedding/i }).click()
  await page.getByLabel('Partner 1').fill('Alice')
  await page.getByLabel('Partner 2').fill('Bob')
  // Fill the required date and location fields the spec's selector list omitted
  await page.getByLabel('Wedding date').fill('2027-06-15')
  await page.getByLabel('Location').fill('Melbourne, VIC')
  await page.getByLabel('Venue').fill('Test Venue')
  await page.getByRole('button', { name: /create wedding/i }).click()

  // Dashboard shows the new wedding heading
  await expect(page.getByRole('heading', { name: /alice & bob/i })).toBeVisible({ timeout: 10_000 })

  // ── Navigate to Guests ────────────────────────────────────────────
  await page.getByRole('link', { name: 'Guests' }).click()
  await expect(page).toHaveURL(/\/guests/)

  // Empty state — click the Add guest button
  await page.getByRole('button', { name: /add guest/i }).first().click()

  // ── Add guest ─────────────────────────────────────────────────────
  await page.getByLabel('Name *').fill('First Guest')
  await page.getByLabel('Email').fill('guest@example.com')
  await page.getByRole('button', { name: 'Add guest' }).click()

  // Guest appears in the list
  await expect(page.getByText('First Guest')).toBeVisible()

  // ── Verify dashboard count updated ────────────────────────────────
  await page.getByRole('link', { name: 'Dashboard' }).click()
  // Wait for the wedding heading so we know the page loaded
  await expect(page.getByRole('heading', { name: /alice & bob/i })).toBeVisible()
  // Scope to <main> to avoid the sidebar nav "Guests" link
  const main = page.locator('main')
  const guestsCard = main.getByText('Guests').locator('..').locator('..')
  await expect(guestsCard).toContainText('1')
})
