import { expect, test } from "@playwright/test";

test.describe("Leaderboard", () => {
  test("renders leaderboard inside shared navbar and loads backend data by period", async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem("access_token", "leaderboard_token");
    });

    await page.route("**/api/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 99,
          email: "learner@example.com",
          display_name: "Avery",
          avatar: "",
          target_language: "es",
          auth_provider: "google",
          has_password: false,
          is_admin: false,
          is_onboarding_completed: true,
          preferences: {
            weekly_xp: 120,
            weekly_rank: "10k+",
            streak_days: 3,
          },
          subscription: null,
          created_at: "2026-04-01T00:00:00Z",
          updated_at: "2026-04-20T00:00:00Z",
        }),
      });
    });

    await page.route("**/api/gamification/leaderboard**", async (route) => {
      const url = new URL(route.request().url());
      const period = url.searchParams.get("period") ?? "weekly";

      const responses = {
        weekly: {
          period: "weekly",
          entries: [
            { user_id: 1, rank: 1, score: 585942, current_streak: 1240, display_name: "HELLO WORLD", email: "hello@example.com", avatar: "", target_language: "en" },
            { user_id: 2, rank: 2, score: 500777, current_streak: 84, display_name: "Tomoko", email: "tomoko@example.com", avatar: "", target_language: "ja" },
            { user_id: 3, rank: 3, score: 490776, current_streak: 42, display_name: "Akiyo Nagashima", email: "akiyo@example.com", avatar: "", target_language: "ja" },
            { user_id: 4, rank: 4, score: 486454, current_streak: 42, display_name: "Unnamed Learner", email: "unnamed@example.com", avatar: "", target_language: "en" },
            { user_id: 5, rank: 5, score: 466956, current_streak: 156, display_name: "blueskyle53", email: "blueskyle53@example.com", avatar: "", target_language: "fr" },
          ],
          current_user: { user_id: 99, rank: 10234, score: 120, current_streak: 3, display_name: "Avery", email: "learner@example.com", avatar: "", target_language: "es" },
          available_periods: ["weekly", "all_time"],
        },
        all_time: {
          period: "all_time",
          entries: [
            { user_id: 3, rank: 1, score: 990776, current_streak: 142, display_name: "Akiyo Nagashima", email: "akiyo@example.com", avatar: "", target_language: "ja" },
            { user_id: 1, rank: 2, score: 985942, current_streak: 1240, display_name: "HELLO WORLD", email: "hello@example.com", avatar: "", target_language: "en" },
            { user_id: 2, rank: 3, score: 900777, current_streak: 84, display_name: "Tomoko", email: "tomoko@example.com", avatar: "", target_language: "ja" },
            { user_id: 4, rank: 4, score: 886454, current_streak: 52, display_name: "Unnamed Learner", email: "unnamed@example.com", avatar: "", target_language: "en" },
            { user_id: 5, rank: 5, score: 866956, current_streak: 166, display_name: "blueskyle53", email: "blueskyle53@example.com", avatar: "", target_language: "fr" },
          ],
          current_user: { user_id: 99, rank: 9876, score: 4200, current_streak: 3, display_name: "Avery", email: "learner@example.com", avatar: "", target_language: "es" },
          available_periods: ["weekly", "all_time"],
        },
      };

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(responses[period]),
      });
    });

    await page.goto("/leaderboard");

    await expect(page.getByRole("link", { name: /SpeakEasy AI/i })).toBeVisible();
    await expect(page.getByRole("link", { name: "Leaderboard" }).first()).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("heading", { name: "Weekly Speaking Leaderboard" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Weekly" })).toHaveAttribute("aria-pressed", "true");

    await expect(page.getByTestId("leaderboard-podium-1")).toContainText("HELLO WORLD");
    await expect(page.getByTestId("leaderboard-podium-2")).toContainText("Tomoko");
    await expect(page.getByTestId("leaderboard-podium-3")).toContainText("Akiyo");

    await expect(page.getByTestId("leaderboard-row-4")).toContainText("Unnamed Learner");
    await expect(page.getByTestId("leaderboard-row-5")).toContainText("blueskyle53");
    await expect(page.getByTestId("leaderboard-current-user")).toContainText("Avery");
    await expect(page.getByTestId("leaderboard-current-user")).toContainText("120 XP");

    await page.getByRole("button", { name: "All-time" }).click();

    await expect(page.getByRole("heading", { name: "All-time Speaking Leaderboard" })).toBeVisible();
    await expect(page.getByRole("button", { name: "All-time" })).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByTestId("leaderboard-podium-1")).toContainText("Akiyo Nagashima");
    await expect(page.getByTestId("leaderboard-current-user")).toContainText("4,200 XP");
    await expect(page.getByTestId("leaderboard-current-user")).toContainText("9876");
  });
});
