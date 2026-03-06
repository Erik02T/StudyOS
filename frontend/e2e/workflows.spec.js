const { test, expect } = require("@playwright/test");
const { setupApiMock, seedAuthenticatedStorage } = require("./helpers/mock-api");

test.describe("Study workflows", () => {
  test("finalize manual session from dashboard", async ({ page }) => {
    await seedAuthenticatedStorage(page, { email: "owner@acme.com" });
    const state = await setupApiMock(page, { reviews: [] });

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: "Finalize Session" })).toBeVisible();

    await page.getByLabel("Study minutes").fill("60");
    await page.getByLabel("Focus score").fill("82");
    await page.getByRole("button", { name: "Finalize Session" }).click();

    await expect(page.getByText("Session finalized and analytics updated.")).toBeVisible();
    await expect.poll(() => state.captured.sessionsFinalize.length).toBeGreaterThan(0);
    await expect
      .poll(() => state.captured.sessionsFinalize[state.captured.sessionsFinalize.length - 1].source)
      .toBe("manual");
  });

  test("answer review and auto-finalize session in review page", async ({ page }) => {
    await seedAuthenticatedStorage(page, { email: "owner@acme.com" });
    const state = await setupApiMock(page, {
      reviews: [
        {
          task_id: 88,
          title: "漢字",
          subject: "Japanese",
          category: "language",
          estimated_time: 15,
          next_review_date: "2026-03-06",
          interval: 2,
          ease_factor: 2.5,
          mastery_level: 54,
        },
      ],
    });

    await page.goto("/review");
    await expect(page.getByText("漢字")).toBeVisible();

    await page.getByRole("button", { name: "Good" }).click();

    await expect(page.getByText("Review completed: 漢字")).toBeVisible();
    await expect(page.getByText("漢字")).not.toBeVisible();
    await expect.poll(() => state.captured.reviewsAnswer.length).toBe(1);
    await expect.poll(() => state.captured.sessionsFinalize.length).toBe(1);
    await expect.poll(() => state.captured.sessionsFinalize[0].source).toBe("review");
  });

  test("organization admin can invite, update role and remove member", async ({ page }) => {
    await seedAuthenticatedStorage(page, { email: "owner@acme.com" });
    const state = await setupApiMock(page, {
      members: [
        { user_id: 1, email: "owner@acme.com", role: "owner", created_at: 1 },
        { user_id: 2, email: "member@acme.com", role: "member", created_at: 2 },
      ],
    });

    await page.goto("/settings");
    await expect(page.getByText("Organization Administration")).toBeVisible();

    await page.getByPlaceholder("member@email.com").fill("newmember@acme.com");
    await page.getByTestId("invite-form").getByRole("combobox").selectOption("admin");
    await page.getByTestId("invite-form").getByRole("button", { name: "Invite" }).click();

    await expect(page.getByText("Member invited.")).toBeVisible();
    await expect(page.getByText("newmember@acme.com")).toBeVisible();
    await expect.poll(() => state.captured.membersInvite.length).toBe(1);

    await page.getByTestId("member-role-select-2").selectOption("admin");
    await page.getByTestId("member-save-role-2").click();

    await expect(page.getByText("member@acme.com role updated to admin.")).toBeVisible();
    await expect.poll(() => state.captured.membersRole.length).toBe(1);

    await page.getByTestId("member-remove-2").click();
    await expect(page.getByText("Remove member from organization?")).toBeVisible();
    await page.getByTestId("confirm-remove-member").click();

    await expect(page.getByText("member@acme.com removed.")).toBeVisible();
    await expect(page.getByTestId("member-row-2")).toHaveCount(0);
    await expect.poll(() => state.captured.membersRemove.length).toBe(1);
  });
});
