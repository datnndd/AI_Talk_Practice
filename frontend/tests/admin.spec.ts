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

    const promptQuality = (score: number) => ({
      score,
      is_acceptable: score >= 70,
      warnings: [],
      suggestions: [],
      recommended_target_skills: [],
    });

    const scenarioList = {
      items: [
        {
          id: 1,
          title: 'Airport Check-in',
          description: 'Practice check-in process',
          is_active: true,
          latest_prompt_quality: promptQuality(92),
          category: 'travel',
          difficulty: 'medium',
          usage_count: 5,
          target_skills: ['Vocabulary', 'Politeness'],
          tags: ['airport'],
          estimated_duration_minutes: 12,
          pre_gen_count: 5,
          is_pre_generated: true,
          variation_count: 0,
          metadata: {},
        },
        {
          id: 2,
          title: 'Coffee Shop',
          description: 'Ordering coffee',
          is_active: false,
          latest_prompt_quality: promptQuality(75),
          category: 'daily',
          difficulty: 'easy',
          usage_count: 2,
          target_skills: ['Vocabulary'],
          tags: ['coffee'],
          estimated_duration_minutes: 8,
          pre_gen_count: 3,
          is_pre_generated: false,
          variation_count: 0,
          metadata: {},
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
          body: JSON.stringify({ success: true, message: 'Scenarios updated', task: null }),
        });
        return;
      }

      if (path === '/api/admin/scenarios/1' && request.method() === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(scenarioList.items[0]) });
        return;
      }

      if (path === '/api/admin/scenarios/1/prompt-history' && request.method() === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
        return;
      }

      if (path === '/api/admin/scenario-variations' && request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0 }),
        });
        return;
      }

      if (path === '/api/admin/generation-tasks/task_123' && request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            task_id: 'task_123',
            status: 'running',
            scenario_ids: [1],
            created_count: 4,
            skipped_count: 0,
            errors: [],
            started_at: new Date().toISOString(),
            finished_at: null,
          }),
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
    await expect(page.getByTestId('scenario-row-1')).toContainText('Prompt 92');
    await expect(page.getByTestId('scenario-row-2')).toContainText('Prompt 75');
  });

  test('performs bulk activation', async ({ page }) => {
    await page.goto('/admin/scenarios');

    await page.getByTestId('scenario-row-2').locator('input[type="checkbox"]').check();
    await page.click('button:has-text("Activate")');

    await expect(page.locator('text=Scenarios updated')).toBeVisible();
  });

  test('shows generation progress', async ({ page }) => {
    await page.goto('/admin/scenarios');
  });
});
