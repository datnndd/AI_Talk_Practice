import { expect, test } from "@playwright/test";

test.describe("Edit Profile", () => {
  test("renders the redesigned page and saves profile changes", async ({ page }) => {
    let patchPayload: Record<string, unknown> | null = null;

    await page.addInitScript(() => {
      window.localStorage.setItem("access_token", "profile_token");
    });

    await page.route("**/api/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 7,
          email: "alex.j@emeraldquest.com",
          display_name: "Alex Johnson",
          avatar: "",
          target_language: "de",
          favorite_topics: ["Daily Life", "Travel"],
          daily_goal: 20,
          auth_provider: "google",
          has_password: false,
          is_admin: false,
          is_onboarding_completed: true,
          preferences: {
            bio: "I practice speaking English 20 minutes every day!",
            handle: "alex_quest",
            profile_theme: "green",
            theme_preference: "light",
          },
          subscription: null,
          created_at: "2026-04-01T00:00:00Z",
          updated_at: "2026-04-01T00:00:00Z",
        }),
      });
    });

    await page.route("**/api/users/me", async (route) => {
      if (route.request().method() !== "PATCH") {
        await route.fallback();
        return;
      }

      patchPayload = route.request().postDataJSON();

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 7,
          email: "alex.j@emeraldquest.com",
          display_name: "Alex Explorer",
          avatar: "",
          target_language: "fr",
          favorite_topics: ["Daily Life", "Travel", "Business"],
          daily_goal: 35,
          auth_provider: "google",
          has_password: false,
          is_admin: false,
          is_onboarding_completed: true,
          preferences: {
            bio: "Focused on fluency for meetings and travel.",
            handle: "alex_quest",
            profile_theme: "blue",
            theme_preference: "light",
          },
          subscription: null,
          created_at: "2026-04-01T00:00:00Z",
          updated_at: "2026-04-20T00:00:00Z",
        }),
      });
    });

    await page.goto("/profile");

    await expect(page.getByRole("heading", { name: "Edit Profile" })).toBeVisible();
    await expect(page.getByText("Emerald Quest")).toBeVisible();
    await expect(page.locator('input[value="Alex Johnson"]')).toBeVisible();

    await page.getByLabel("FULL NAME").fill("Alex Explorer");
    await page.getByLabel("BIO").fill("Focused on fluency for meetings and travel.");
    await page.getByRole("button", { name: "Business" }).click();
    await page.getByLabel("Target Language").selectOption("fr");
    await page.locator("#daily-goal").evaluate((element) => {
      const input = element as HTMLInputElement;
      const descriptor = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value");
      descriptor?.set?.call(input, "35");
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await page.getByLabel("Set profile theme to blue").click();

    await page.getByRole("button", { name: "Save Changes" }).click();

    await expect(page.getByText("Profile updated successfully.")).toBeVisible();
    await expect(page.getByText("Alex Explorer").first()).toBeVisible();

    expect(patchPayload).toEqual({
      display_name: "Alex Explorer",
      avatar: null,
      target_language: "fr",
      favorite_topics: ["Daily Life", "Travel", "Business"],
      daily_goal: 35,
      preferences: {
        bio: "Focused on fluency for meetings and travel.",
        handle: "alex_quest",
        profile_theme: "blue",
        theme_preference: "light",
      },
    });
  });
});
