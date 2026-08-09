import { test, expect } from "@playwright/test";

// Smoke test guarding the storefront shell and core routing. Asserts only
// data-independent UI, so it's reliable in CI whether or not the backend is up.

test("home page renders the storefront shell", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "KAIRA" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Shop" }).first()).toBeVisible();
});

test("can navigate to the shop", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Shop" }).first().click();
  await expect(page).toHaveURL(/\/shop/);
});

test("privacy policy page loads with its heading", async ({ page }) => {
  await page.goto("/privacy");
  await expect(page.getByRole("heading", { name: "Privacy Policy" })).toBeVisible();
  await expect(page).toHaveTitle(/Privacy Policy \| Kaira/);
});

test("footer exposes the legal links", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Privacy" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Terms" })).toBeVisible();
});
