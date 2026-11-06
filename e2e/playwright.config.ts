import { defineConfig } from "@playwright/test";
import { delimiter, resolve } from "node:path";

const FRONTEND_PORT = 5176;

export default defineConfig({
  testDir: ".",
  timeout: 120_000,
  expect: { timeout: 30_000 },
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    channel: process.env.PW_CHANNEL ?? "chrome",
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    locale: "en-IN",
  },
  webServer: [
    {
      command: "python -m uvicorn app.main:app --port 8000",
      cwd: "../backend",
      url: "http://localhost:8000/api/health",
      reuseExistingServer: true,
      timeout: 120_000,
      env: { PYTHONUTF8: "1", PATH: [resolve("../backend/.venv/Scripts"), resolve("../backend/.venv/bin"), process.env.PATH].join(delimiter) },
    },
    {
      command: `npx vite --port ${FRONTEND_PORT} --strictPort`,
      cwd: "../frontend",
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
