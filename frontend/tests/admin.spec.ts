import { test, expect } from '@playwright/test';

test.describe('Admin Panel Protection', () => {
  test('redirects unauthorized user to login', async ({ page }) => {
    await page.goto('/admin/scenarios');
    // PrivateRoute redirects to /login if not authenticated
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });

  test('denies access to regular user', async ({ page }) => {
    // Mock regular user token
    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'regular_user_token');
    });

    // Mock auth/me for non-admin
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 2,
          email: 'user@example.com',
          display_name: 'Regular User',
          is_admin: false,
          preferences: { is_admin: false }
        })
      });
    });

    await page.goto('/admin/scenarios');
    // Depending on frontend implementation, it might redirect to /dashboard or show error
    // Here we check that it's NOT on the admin page
    await expect(page).not.toHaveURL('/admin/scenarios');
  });
});

test.describe('Admin Scenario Management', () => {
  test.beforeEach(async ({ page }) => {
    // Mock admin token
    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'admin_token');
    });

    // Mock auth/me for admin
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          email: 'admin@example.com',
          display_name: 'Admin User',
          is_admin: true,
          preferences: { is_admin: true }
        })
      });
    });

    const scenarioList = {
      items: [
        {
          id: 1,
          title: 'Airport Check-in',
          description: 'Practice check-in process',
          is_active: true,
          category: 'travel',
          difficulty: 'medium',
          usage_count: 5,
          tags: ['airport'],
          tasks: ['Confirm booking', 'Ask about baggage'],
          ai_role: 'Airline check-in agent',
          user_role: 'Traveler at airport',
          estimated_duration_minutes: 12,
          is_pro: false,
        },
        {
          id: 2,
          title: 'Coffee Shop',
          description: 'Ordering coffee',
          is_active: false,
          category: 'daily',
          difficulty: 'easy',
          usage_count: 2,
          tags: ['coffee'],
          tasks: ['Ask for coffee'],
          ai_role: 'Barista',
          user_role: 'Customer',
          estimated_duration_minutes: 8,
          is_pro: false,
        },
      ],
      total: 2,
      page: 1,
      page_size: 12,
    };

    await page.route('**/api/admin/**', async route => {
      const request = route.request();
      const url = new URL(request.url());
      const path = url.pathname;

      if (path === '/api/admin/scenarios' && request.method() === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(scenarioList) });
        return;
      }

      if (path === '/api/admin/scenarios/bulk-actions' && request.method() === 'POST') {
        const payload = request.postDataJSON();
        expect(payload.action).toBe('activate');
        expect(payload.scenario_ids).toContain(2);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, message: 'Scenarios updated' }),
        });
        return;
      }

      await route.fallback();
    });
  });

  test('displays scenario list with quality scores', async ({ page }) => {
    await page.goto('/admin/scenarios');
    await expect(page.getByTestId('scenario-row-1')).toContainText('Airport Check-in');
    await expect(page.getByTestId('scenario-row-2')).toContainText('Coffee Shop');
    await expect(page.locator('text=/Prompt \\d+/')).toHaveCount(0);
  });

  test('performs bulk activation', async ({ page }) => {
    await page.goto('/admin/scenarios');

    await page.getByTestId('scenario-row-2').locator('input[type="checkbox"]').check();
    await page.click('button:has-text("Activate")');

    await expect(page.locator('text=Scenarios updated')).toBeVisible();
  });

  test('selects a scenario and opens edit modal from contextual actions', async ({ page }) => {
    await page.goto('/admin/scenarios');
    await page.getByTestId('scenario-row-1').getByText('Airport Check-in').click();
    await expect(page.locator('text=Airline check-in agent')).toBeVisible();
    await page.click('button:has-text("Edit Scenario")');
    await expect(page.locator('text=Edit Scenario')).toBeVisible();
  });
});
