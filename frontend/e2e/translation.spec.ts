import { test, expect } from '@playwright/test'

test.describe('Translation Feature', () => {
  test('home page has live translate navigation link', async ({ page }) => {
    await page.goto('/')

    // Look for the navigation link
    const liveTranslateLink = page.getByRole('button', { name: /即時翻譯/i })
    await expect(liveTranslateLink).toBeVisible()
  })

  test('navigate to live translate page', async ({ page }) => {
    await page.goto('/')

    // Click on live translate link
    await page.getByRole('button', { name: /即時翻譯/i }).click()

    // Should navigate to live translate page
    await expect(page).toHaveURL('/live-translate')

    // Should show status indicator
    await expect(page.getByText('準備就緒')).toBeVisible()

    // Should show start recording button
    await expect(page.getByRole('button', { name: /開始錄音/i })).toBeVisible()
  })

  test('navigate to translation history page', async ({ page }) => {
    await page.goto('/live-translate')

    // Go back to home
    await page.getByRole('button', { name: /返回首頁/i }).click()
    await expect(page).toHaveURL('/')

    // Navigate to live translate again
    await page.getByRole('button', { name: /即時翻譯/i }).click()
    await expect(page).toHaveURL('/live-translate')
  })

  test('translation history page shows empty state', async ({ page }) => {
    await page.goto('/translation-history')

    // Should show history page title
    await expect(page.getByText('翻譯歷史')).toBeVisible()

    // Should show filter buttons
    await expect(page.getByRole('button', { name: '全部' })).toBeVisible()
    await expect(page.getByRole('button', { name: '已完成' })).toBeVisible()
  })

  test('filter buttons work on history page', async ({ page }) => {
    await page.goto('/translation-history')

    // Click on completed filter
    const completedBtn = page.getByRole('button', { name: '已完成' })
    await completedBtn.click()

    // Button should be active
    await expect(completedBtn).toHaveClass(/active/)

    // Click on all filter
    const allBtn = page.getByRole('button', { name: '全部' })
    await allBtn.click()

    // All button should be active now
    await expect(allBtn).toHaveClass(/active/)
  })

  test('page size selector works', async ({ page }) => {
    await page.goto('/translation-history')

    // Find page size buttons
    const size20 = page.getByRole('button', { name: '20' })
    const size50 = page.getByRole('button', { name: '50' })

    // Click 50
    await size50.click()
    await expect(size50).toHaveClass(/active/)

    // Click 20
    await size20.click()
    await expect(size20).toHaveClass(/active/)
  })
})

test.describe('Navigation Integration', () => {
  test('can navigate between all main pages', async ({ page }) => {
    // Start at home
    await page.goto('/')
    await expect(page.getByText('會議助理')).toBeVisible()

    // Go to history
    await page.getByRole('button', { name: /歷史紀錄/i }).click()
    await expect(page).toHaveURL('/history')

    // Go back home
    await page.getByRole('button', { name: /返回首頁/i }).click()
    await expect(page).toHaveURL('/')

    // Go to translate
    await page.getByRole('button', { name: /文件翻譯/i }).click()
    await expect(page).toHaveURL('/translate')

    // Go back home
    await page.getByRole('button', { name: /返回首頁/i }).click()
    await expect(page).toHaveURL('/')

    // Go to live translate
    await page.getByRole('button', { name: /即時翻譯/i }).click()
    await expect(page).toHaveURL('/live-translate')
  })
})
