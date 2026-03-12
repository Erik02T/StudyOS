const { test, expect } = require("@playwright/test");
const { setupApiMock, seedAuthenticatedStorage } = require("./helpers/mock-api");

test.describe("Auth flows", () => {
  test("user can register and reach dashboard", async ({ page }) => {
    const state = await setupApiMock(page);

    await page.goto("/auth/register");
    await page.getByPlaceholder("you@email.com").fill("new@studyos.dev");
    await page.getByPlaceholder("Your password").fill("StrongPass123!");
    await page.getByPlaceholder("Repeat password").fill("StrongPass123!");
    await page.getByRole("button", { name: "Create account" }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText("Evolution Score", { exact: true })).toBeVisible();
    await expect.poll(() => state.captured.authRegister.length).toBe(1);
    await expect
      .poll(() => state.captured.authRegister[0] && state.captured.authRegister[0].email)
      .toBe("new@studyos.dev");
  });

  test("user can login and reach dashboard", async ({ page }) => {
    const state = await setupApiMock(page);

    await page.goto("/auth/login");
    await page.getByPlaceholder("you@email.com").fill("owner@acme.com");
    await page.getByPlaceholder("Your password").fill("OwnerPass123!");
    await page.getByRole("button", { name: "Login" }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText("Evolution Score", { exact: true })).toBeVisible();
    await expect.poll(() => state.captured.authLogin.length).toBe(1);
    await expect.poll(() => state.captured.authLogin[0] && state.captured.authLogin[0].email).toBe("owner@acme.com");
  });

  test("register shows a clear message when the API is unreachable", async ({ page }) => {
    await page.goto("/auth/register");
    await page.getByPlaceholder("you@email.com").fill("new@studyos.dev");
    await page.getByPlaceholder("Your password").fill("StrongPass123!");
    await page.getByPlaceholder("Repeat password").fill("StrongPass123!");
    await page.getByRole("button", { name: "Create account" }).click();

    await expect(
      page.getByText(
        "Cannot reach the StudyOS API. Check backend health, CORS, and NEXT_PUBLIC_API_BASE_URL."
      )
    ).toBeVisible();
  });

  test("expired access token refreshes once and retries protected requests", async ({ page }) => {
    await seedAuthenticatedStorage(page, {
      token: "expired-token",
      refreshToken: "valid-refresh-token",
      email: "owner@acme.com",
    });
    const state = await setupApiMock(page, {
      auth: {
        expiredAccessToken: "expired-token",
        validRefreshToken: "valid-refresh-token",
        refreshedAccessToken: "fresh-access-token",
        refreshedRefreshToken: "fresh-refresh-token",
      },
    });

    await page.goto("/dashboard");

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText("Evolution Score", { exact: true })).toBeVisible();
    await expect.poll(() => state.captured.authRefresh.length).toBe(1);
    await expect
      .poll(() =>
        page.evaluate(() => ({
          access: window.localStorage.getItem("studyos_token"),
          refresh: window.localStorage.getItem("studyos_refresh_token"),
        }))
      )
      .toEqual({ access: "fresh-access-token", refresh: "fresh-refresh-token" });
  });

  test("invalid refresh clears auth state and redirects to login", async ({ page }) => {
    await seedAuthenticatedStorage(page, {
      token: "expired-token",
      refreshToken: "invalid-refresh-token",
      email: "owner@acme.com",
    });
    const state = await setupApiMock(page, {
      auth: {
        expiredAccessToken: "expired-token",
        validRefreshToken: "valid-refresh-token",
        failRefresh: true,
      },
    });

    await page.goto("/dashboard");

    await expect(page).toHaveURL(/\/auth\/login/);
    await expect.poll(() => state.captured.authRefresh.length).toBe(1);
    await expect
      .poll(() =>
        page.evaluate(() => ({
          access: window.localStorage.getItem("studyos_token"),
          refresh: window.localStorage.getItem("studyos_refresh_token"),
          email: window.localStorage.getItem("studyos_email"),
        }))
      )
      .toEqual({ access: null, refresh: null, email: null });
  });
});
