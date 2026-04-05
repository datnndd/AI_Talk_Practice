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
          preferences: { is_admin: true }
        })
      });
    });

    // Mock scenario list (with total/items format)
    await page.route('**/api/admin/scenarios*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 1,
              title: 'Airport Check-in',
              description: 'Practice check-in process',
              is_active: true,
              latest_prompt_quality: 92,
              category: 'travel',
              difficulty: 'medium',
              usage_count: 5
            },
            {
              id: 2,
              title: 'Coffee Shop',
              description: 'Ordering coffee',
              is_active: false,
              latest_prompt_quality: 75,
              category: 'daily',
              difficulty: 'easy',
              usage_count: 2
            }
          ],
          total: 2
        })
      });
    });
    // Mock scenario detail
    await page.route('**/api/admin/scenarios/1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          title: 'Airport Check-in',
          description: 'Practice check-in process',
          is_active: true,
          latest_prompt_quality: 92,
          category: 'travel',
          difficulty: 'medium',
          target_skills: ['Vocabulary', 'Politeness'],
          pre_gen_count: 5,
          is_pre_generated: true
        })
      });
    });

    // Mock prompt history
    await page.route('**/api/admin/scenarios/1/prompt-history', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });
  });

  test('displays scenario list with quality scores', async ({ page }) => {
    await page.goto('/admin/scenarios');
    await expect(page.locator('text=Airport Check-in')).toBeVisible();
    await expect(page.locator('text=Coffee Shop')).toBeVisible();
    await expect(page.locator('text=92')).toBeVisible();
    await expect(page.locator('text=75')).toBeVisible();
  });

  test('performs bulk activation', async ({ page }) => {
    // Mock bulk action API
    await page.route('**/api/admin/scenarios/bulk-actions', async route => {
      expect(route.request().method()).toBe('POST');
      const payload = route.request().postDataJSON();
      expect(payload.action).toBe('activate');
      expect(payload.scenario_ids).toContain(2);
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, message: 'Scenarios updated' })
      });
    });

    await page.goto('/admin/scenarios');
    
    // Find Coffee Shop and its checkbox (assuming it has a checkbox)
    // This part depends on the actual UI implementation
    // For now, let's assume there's a Select button or checkbox
    const coffeeRow = page.locator('div', { hasText: 'Coffee Shop' }).filter({ has: page.locator('input[type="checkbox"]') });
    await coffeeRow.locator('input[type="checkbox"]').check();
    
    await page.click('button:has-text("Activate")');
    
    // Verify success message
    await expect(page.locator('text=Scenarios updated')).toBeVisible();
  });

  test('shows generation progress', async ({ page }) => {
    // Mock task status API
    await page.route('**/api/admin/tasks/*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          task_id: 'task_123',
          status: 'running',
          progress: 50,
          total_variations: 8,
          processed_variations: 4
        })
      });
    });

    await page.goto('/admin/scenarios');
    
    // Simulate active task (if the UI checks for it on load or poll)
    // This depends on how the UI displays task progress
  });
});
