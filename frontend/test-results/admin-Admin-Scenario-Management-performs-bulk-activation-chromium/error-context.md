# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin.spec.ts >> Admin Scenario Management >> performs bulk activation
- Location: tests/admin.spec.ts:94:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.check: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('div').filter({ hasText: 'Coffee Shop' }).filter({ has: locator('input[type="checkbox"]') }).locator('input[type="checkbox"]')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - complementary [ref=e4]:
    - generic [ref=e5]:
      - paragraph [ref=e6]: Categories
      - generic [ref=e7]:
        - generic [ref=e8] [cursor=pointer]:
          - img [ref=e9]
          - generic [ref=e11]: Home
        - generic [ref=e12] [cursor=pointer]:
          - img [ref=e13]
          - generic [ref=e15]: Dashboard
        - generic [ref=e16] [cursor=pointer]:
          - img [ref=e17]
          - generic [ref=e19]: Topics
        - generic [ref=e20] [cursor=pointer]:
          - img [ref=e21]
          - generic [ref=e23]: Practice
        - generic [ref=e24] [cursor=pointer]:
          - img [ref=e25]
          - generic [ref=e27]: Profile
    - generic [ref=e28]:
      - generic [ref=e30]:
        - generic [ref=e31]: A
        - generic [ref=e32]:
          - paragraph [ref=e33]: Admin User
          - paragraph [ref=e34]: Beginner
      - button "Logout" [ref=e35]
  - generic [ref=e36]:
    - banner [ref=e37]:
      - generic [ref=e38]:
        - generic [ref=e39] [cursor=pointer]:
          - img [ref=e41]
          - generic [ref=e43]: LingoAI
        - navigation [ref=e44]:
          - link "Explore" [ref=e45] [cursor=pointer]:
            - /url: "#"
          - link "My Progress" [ref=e46] [cursor=pointer]:
            - /url: "#"
          - link "Community" [ref=e47] [cursor=pointer]:
            - /url: "#"
      - generic [ref=e48]:
        - generic [ref=e49]:
          - img [ref=e50]
          - textbox "Search topics..." [ref=e52]
        - link [ref=e53] [cursor=pointer]:
          - /url: /profile
          - img [ref=e55]
    - main [ref=e57]:
      - generic [ref=e58]:
        - generic [ref=e59]:
          - generic [ref=e60]:
            - heading "Good afternoon, Elara" [level=1] [ref=e61]
            - paragraph [ref=e62]: Ready for your daily linguistic challenge?
          - generic [ref=e63]:
            - img "Buddy" [ref=e65]
            - img "Buddy" [ref=e67]
            - img "Buddy" [ref=e69]
            - generic [ref=e70] [cursor=pointer]: "+2"
        - generic [ref=e71]:
          - generic [ref=e72]:
            - generic [ref=e74]:
              - img [ref=e75]
              - generic [ref=e78]:
                - generic [ref=e79]: 85%
                - generic [ref=e80]: Weekly
            - generic [ref=e81]:
              - heading "Goal Status" [level=3] [ref=e82]
              - paragraph [ref=e83]: Almost there! 3 more lessons left.
          - generic [ref=e84]:
            - generic [ref=e85]:
              - paragraph [ref=e86]: Current Streak
              - generic [ref=e87]:
                - generic [ref=e88]: "12"
                - generic [ref=e89]: days
            - img [ref=e93]
          - generic [ref=e98]:
            - generic [ref=e99]:
              - generic [ref=e100]: AI Tutor Live
              - button "Practice Speaking Now" [ref=e101]
            - img [ref=e103]
          - generic [ref=e105]:
            - generic [ref=e106]:
              - heading "The Intelligent List Auto-Sorting" [level=2] [ref=e107]:
                - text: The Intelligent List
                - generic [ref=e108]: Auto-Sorting
              - button "View Roadmap" [ref=e109]
            - generic [ref=e110]:
              - generic [ref=e111] [cursor=pointer]:
                - generic [ref=e112]: ☕
                - generic [ref=e113]:
                  - heading "Cafe Conversations" [level=4] [ref=e114]
                  - paragraph [ref=e115]: Intermediate • 8 mins
                - generic [ref=e116]:
                  - generic [ref=e117]: +45 XP
                  - img [ref=e119]
              - generic [ref=e121] [cursor=pointer]:
                - generic [ref=e122]: ✈️
                - generic [ref=e123]:
                  - heading "Airport Logistics" [level=4] [ref=e124]
                  - paragraph [ref=e125]: Beginner • 12 mins
                - generic [ref=e126]:
                  - generic [ref=e127]: +30 XP
                  - img [ref=e129]
              - generic [ref=e131] [cursor=pointer]:
                - generic [ref=e132]: 💼
                - generic [ref=e133]:
                  - heading "Business Etiquette" [level=4] [ref=e134]
                  - paragraph [ref=e135]: Advanced • 15 mins
                - generic [ref=e136]:
                  - generic [ref=e137]: +60 XP
                  - img [ref=e139]
```

# Test source

```ts
  15  |     });
  16  | 
  17  |     // Mock auth/me for non-admin
  18  |     await page.route('**/api/auth/me', async route => {
  19  |       await route.fulfill({
  20  |         status: 200,
  21  |         contentType: 'application/json',
  22  |         body: JSON.stringify({
  23  |           id: 2,
  24  |           email: 'user@example.com',
  25  |           display_name: 'Regular User',
  26  |           preferences: { is_admin: false }
  27  |         })
  28  |       });
  29  |     });
  30  | 
  31  |     await page.goto('/admin/scenarios');
  32  |     // Depending on frontend implementation, it might redirect to /dashboard or show error
  33  |     // Here we check that it's NOT on the admin page
  34  |     await expect(page).not.toHaveURL('/admin/scenarios');
  35  |   });
  36  | });
  37  | 
  38  | test.describe('Admin Scenario Management', () => {
  39  |   test.beforeEach(async ({ page }) => {
  40  |     // Mock admin token
  41  |     await page.addInitScript(() => {
  42  |       window.localStorage.setItem('access_token', 'admin_token');
  43  |     });
  44  | 
  45  |     // Mock auth/me for admin
  46  |     await page.route('**/api/auth/me', async route => {
  47  |       await route.fulfill({
  48  |         status: 200,
  49  |         contentType: 'application/json',
  50  |         body: JSON.stringify({
  51  |           id: 1,
  52  |           email: 'admin@example.com',
  53  |           display_name: 'Admin User',
  54  |           preferences: { is_admin: true }
  55  |         })
  56  |       });
  57  |     });
  58  | 
  59  |     // Mock scenario list
  60  |     await page.route('**/api/admin/scenarios*', async route => {
  61  |       await route.fulfill({
  62  |         status: 200,
  63  |         contentType: 'application/json',
  64  |         body: JSON.stringify([
  65  |           {
  66  |             id: 1,
  67  |             title: 'Airport Check-in',
  68  |             description: 'Practice check-in process',
  69  |             is_active: true,
  70  |             quality_score: 92,
  71  |             category: 'travel'
  72  |           },
  73  |           {
  74  |             id: 2,
  75  |             title: 'Coffee Shop',
  76  |             description: 'Ordering coffee',
  77  |             is_active: false,
  78  |             quality_score: 75,
  79  |             category: 'daily'
  80  |           }
  81  |         ])
  82  |       });
  83  |     });
  84  |   });
  85  | 
  86  |   test('displays scenario list with quality scores', async ({ page }) => {
  87  |     await page.goto('/admin/scenarios');
  88  |     await expect(page.locator('text=Airport Check-in')).toBeVisible();
  89  |     await expect(page.locator('text=Coffee Shop')).toBeVisible();
  90  |     await expect(page.locator('text=92')).toBeVisible();
  91  |     await expect(page.locator('text=75')).toBeVisible();
  92  |   });
  93  | 
  94  |   test('performs bulk activation', async ({ page }) => {
  95  |     // Mock bulk action API
  96  |     await page.route('**/api/admin/scenarios/bulk-actions', async route => {
  97  |       expect(route.request().method()).toBe('POST');
  98  |       const payload = route.request().postDataJSON();
  99  |       expect(payload.action).toBe('activate');
  100 |       expect(payload.scenario_ids).toContain(2);
  101 |       
  102 |       await route.fulfill({
  103 |         status: 200,
  104 |         contentType: 'application/json',
  105 |         body: JSON.stringify({ success: true, message: 'Scenarios updated' })
  106 |       });
  107 |     });
  108 | 
  109 |     await page.goto('/admin/scenarios');
  110 |     
  111 |     // Find Coffee Shop and its checkbox (assuming it has a checkbox)
  112 |     // This part depends on the actual UI implementation
  113 |     // For now, let's assume there's a Select button or checkbox
  114 |     const coffeeRow = page.locator('div', { hasText: 'Coffee Shop' }).filter({ has: page.locator('input[type="checkbox"]') });
> 115 |     await coffeeRow.locator('input[type="checkbox"]').check();
      |                                                       ^ Error: locator.check: Test timeout of 30000ms exceeded.
  116 |     
  117 |     await page.click('button:has-text("Activate")');
  118 |     
  119 |     // Verify success message
  120 |     await expect(page.locator('text=Scenarios updated')).toBeVisible();
  121 |   });
  122 | 
  123 |   test('shows generation progress', async ({ page }) => {
  124 |     // Mock task status API
  125 |     await page.route('**/api/admin/tasks/*', async route => {
  126 |       await route.fulfill({
  127 |         status: 200,
  128 |         contentType: 'application/json',
  129 |         body: JSON.stringify({
  130 |           task_id: 'task_123',
  131 |           status: 'running',
  132 |           progress: 50,
  133 |           total_variations: 8,
  134 |           processed_variations: 4
  135 |         })
  136 |       });
  137 |     });
  138 | 
  139 |     await page.goto('/admin/scenarios');
  140 |     
  141 |     // Simulate active task (if the UI checks for it on load or poll)
  142 |     // This depends on how the UI displays task progress
  143 |   });
  144 | });
  145 | 
```