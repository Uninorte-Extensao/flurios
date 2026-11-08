/* global process */
import { defineConfig } from '@playwright/test'

// Rode por `npm run test:e2e` (e2e/rodar.mjs): ele sobe API e frontend em portas livres e define as variaveis E2E_*.
export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.js',
  timeout: 180_000,
  expect: { timeout: 10_000 },
  workers: 1,
  fullyParallel: false,
  reporter: [['list']],
  outputDir: process.env.E2E_TEMP ? `${process.env.E2E_TEMP}/resultados` : 'node_modules/.cache/playwright-resultados',
  use: {
    baseURL: process.env.E2E_FRONT_URL,
    locale: 'pt-BR',
    timezoneId: 'America/Manaus',
    viewport: { width: 1440, height: 900 },
    trace: 'off',
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
})
