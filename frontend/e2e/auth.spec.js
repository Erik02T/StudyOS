const { test, expect } = require("@playwright/test");
const { setupApiMock } = require("./helpers/mock-api");

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
});
