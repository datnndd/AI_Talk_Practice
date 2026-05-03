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
    await expect(page.getByRole('button', { name: /Airport Check-in/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Coffee Shop/ })).toBeVisible();
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
    await expect(page.getByRole('button', { name: 'Save Scenario' })).toBeVisible();
  });
});

test.describe('Admin Curriculum Management', () => {
  const now = '2026-04-27T00:00:00.000Z';

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('access_token', 'admin_token');
    });

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

    const sections = [
      {
        id: 1,
        code: 'A1',
        cefr_level: 'A1',
        title: 'Beginner',
        description: 'Starter path',
        order_index: 0,
        is_active: true,
        created_at: now,
        updated_at: now,
        units: [
          {
            id: 10,
            section_id: 1,
            title: 'Greetings',
            description: 'Say hello',
            order_index: 0,
            estimated_minutes: 8,
            xp_reward: 50,
            coin_reward: 5,
            is_active: true,
            is_locked: false,
            progress_status: 'not_started',
            best_score: null,
            created_at: now,
            updated_at: now,
            lessons: [
              {
                id: 100,
                unit_id: 10,
                type: 'sentence_pronunciation',
                title: 'Say hello',
                order_index: 0,
                content: { reference_text: 'Hello there' },
                pass_score: 80,
                is_required: true,
                is_active: true,
                progress: null,
                created_at: now,
                updated_at: now,
              },
            ],
          },
        ],
      },
      {
        id: 2,
        code: 'A2',
        cefr_level: 'A2',
        title: 'Elementary',
        description: 'Next path',
        order_index: 1,
        is_active: true,
        created_at: now,
        updated_at: now,
        units: [],
      },
    ];

    const findUnit = (unitId) => sections.flatMap(section => section.units).find(unit => unit.id === unitId);
    const findLesson = (lessonId) => sections.flatMap(section => section.units).flatMap(unit => unit.lessons).find(lesson => lesson.id === lessonId);

    await page.route('**/api/admin/**', async route => {
      const request = route.request();
      const url = new URL(request.url());
      const path = url.pathname;

      if (path === '/api/admin/scenarios' && request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 7, title: 'Airport Check-in' }],
            total: 1,
            page: 1,
            page_size: 100,
          }),
        });
        return;
      }

      if (path === '/api/admin/curriculum/sections' && request.method() === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(sections) });
        return;
      }

      if (path === '/api/admin/curriculum/dictionary/lookup' && request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            word: url.searchParams.get('word'),
            language: 'en',
            definition_language: 'vi',
            meaning_vi: 'ca phe',
            ipa: '/ˈkɒfi/',
            audio_url: '/api/curriculum/dictionary/audio?word=coffee&lang=en',
            source: 'dict.minhqnd.com',
            exists: true,
            definitions: ['ca phe'],
          }),
        });
        return;
      }

      if (path === '/api/admin/curriculum/audio/tts' && request.method() === 'POST') {
        const payload = request.postDataJSON();
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 900,
            lesson_id: payload.lesson_id || null,
            source: 'tts',
            text: payload.text,
            voice: payload.voice || 'Cherry',
            language: payload.language || 'en',
            filename: 'coffee.wav',
            url: '/static/uploads/lesson-audio/coffee.wav',
            content_type: 'audio/wav',
            size_bytes: 4,
            created_at: now,
            updated_at: now,
          }),
        });
        return;
      }

      if (path === '/api/admin/curriculum/sections' && request.method() === 'POST') {
        const payload = request.postDataJSON();
        const section = { id: 3, units: [], created_at: now, updated_at: now, ...payload };
        sections.push(section);
        await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(section) });
        return;
      }

      if (path === '/api/admin/curriculum/units' && request.method() === 'POST') {
        const payload = request.postDataJSON();
        const section = sections.find(item => item.id === payload.section_id);
        const unit = {
          id: 30,
          lessons: [],
          is_locked: false,
          progress_status: 'not_started',
          best_score: null,
          created_at: now,
          updated_at: now,
          ...payload,
        };
        section.units.push(unit);
        await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(unit) });
        return;
      }

      if (path === '/api/admin/curriculum/lessons' && request.method() === 'POST') {
        const payload = request.postDataJSON();
        expect(payload.title).toBe('Lesson 1');
        expect(payload.content.words[0].word).toBe('coffee');
        const unit = findUnit(payload.unit_id);
        const lesson = { id: 300, progress: null, created_at: now, updated_at: now, ...payload };
        unit.lessons.push(lesson);
        await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(lesson) });
        return;
      }

      const lessonMatch = path.match(/^\/api\/admin\/curriculum\/lessons\/(\d+)$/);
      if (lessonMatch && request.method() === 'PUT') {
        const lesson = findLesson(Number(lessonMatch[1]));
        Object.assign(lesson, request.postDataJSON());
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(lesson) });
        return;
      }

      if (lessonMatch && request.method() === 'DELETE') {
        const lesson = findLesson(Number(lessonMatch[1]));
        lesson.is_active = false;
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(lesson) });
        return;
      }

      if (path === '/api/admin/curriculum/sections/reorder' && request.method() === 'POST') {
        const payload = request.postDataJSON();
        expect(payload.items).toEqual([{ id: 2, order_index: 0 }, { id: 1, order_index: 1 }]);
        payload.items.forEach(item => {
          const section = sections.find(entry => entry.id === item.id);
          section.order_index = item.order_index;
        });
        sections.sort((a, b) => a.order_index - b.order_index);
        await route.fulfill({ status: 204, body: '' });
        return;
      }

      await route.fallback();
    });
  });

  test('loads curriculum tree', async ({ page }) => {
    await page.goto('/admin/curriculum');
    await expect(page.getByRole('button', { name: /1\. Beginner/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /1\. Greetings/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /1\. Say hello/ })).toBeVisible();
  });

  test('creates section, unit, and lesson from builder forms', async ({ page }) => {
    await page.goto('/admin/curriculum');

    await page.getByTestId('new-section-button').click();
    await page.getByTestId('level-code-input').fill('B1');
    await page.getByTestId('level-title-input').fill('Intermediate');
    await page.getByTestId('save-curriculum-entity').click();
    await expect(page.getByText('section saved.')).toBeVisible();

    await page.getByTestId('new-unit-button').click();
    await page.getByTestId('lesson-title-input').fill('Cafe order');
    await page.getByTestId('save-curriculum-entity').click();
    await expect(page.getByText('unit saved.')).toBeVisible();

    await page.getByTestId('new-lesson-button').click();
    await expect(page.getByTestId('exercise-title-input')).toHaveValue('Lesson 1');
    await page.getByTestId('vocab-word-input-0').fill('coffee');
    await page.getByRole('button', { name: /Lấy nghĩa/ }).click();
    await expect(page.getByTestId('vocab-meaning-input-0')).toHaveValue('ca phe');
    page.once('dialog', async dialog => {
      expect(dialog.defaultValue()).toBe('coffee');
      await dialog.accept('coffee');
    });
    await page.getByRole('button', { name: /Generate TTS/ }).click();
    await expect(page.locator('audio')).toHaveAttribute('src', /lesson-audio\/coffee\.wav/);
    await page.getByTestId('save-curriculum-entity').click();
    await expect(page.getByText('lesson saved.')).toBeVisible();
    await expect(page.getByTestId('curriculum-exercise-row-300')).toContainText('Lesson 1');
  });

  test('edits exercise content through JSON tab', async ({ page }) => {
    await page.goto('/admin/curriculum');
    await page.getByTestId('curriculum-exercise-row-100').click();
    await page.getByTestId('edit-exercise-button').click();
    await page.getByTestId('exercise-json-tab').click();
    await page.getByTestId('exercise-json-input').fill(JSON.stringify({ reference_text: 'Good morning' }, null, 2));
    await page.getByTestId('save-curriculum-entity').click();
    await expect(page.getByText('Good morning')).toBeVisible();
  });

  test('deactivates and restores an exercise', async ({ page }) => {
    await page.goto('/admin/curriculum');
    await page.getByTestId('curriculum-exercise-row-100').click();
    await page.getByTestId('toggle-exercise-button').click();
    await expect(page.getByTestId('curriculum-exercise-row-100')).toContainText('Inactive');
    await page.getByTestId('toggle-exercise-button').click();
    await expect(page.getByTestId('curriculum-exercise-row-100')).toContainText('Active');
  });

  test('reorders levels with normalized payload', async ({ page }) => {
    await page.goto('/admin/curriculum');
    await page.getByTestId('curriculum-level-row-1').click();
    await page.getByTestId('move-level-down').click();
    await expect(page.getByText('section order updated.')).toBeVisible();
  });
});
