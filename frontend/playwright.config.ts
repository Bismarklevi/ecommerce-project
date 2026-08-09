import { defineConfig, devices } from "@playwright/test";

// E2E lives in ./e2e so it never overlaps the Vitest unit suite (src/**).
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  // Serves the built app. Locally, a running `npm run dev` is reused; otherwise
  // this starts the production server (run `npm run build` first, or let CI do
  // it). The smoke test asserts data-independent shell/routing, so it passes
  // even without the Django backend running.
  webServer: {
    command: "npm run start",
    url: process.env.E2E_BASE_URL || "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
