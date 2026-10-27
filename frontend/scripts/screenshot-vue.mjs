import path from 'node:path'
import { chromium } from '@playwright/test'
import {
  collectMetrics,
  defaultViewport,
  normalizeList,
  parseArgs,
  relativeFromRoot,
  resolvePages,
  rootDir,
  writeJson,
} from './shared.mjs'

const argv = parseArgs(process.argv.slice(2))

if (argv.help || argv.h) {
  console.log(`
Usage:
  node scripts/screenshot-vue.mjs --pages data-dashboard,review

Options:
  --pages    Comma-separated page keys
  --out      Output JSON path, default: docs/runtime/vue-pages.json
  --shots    Screenshot directory, default: docs/screenshots/vue
  --help     Show this message
`.trim())
  process.exit(0)
}

const outputPath = path.resolve(rootDir, argv.out || 'docs/runtime/vue-pages.json')
const screenshotDir = path.resolve(rootDir, argv.shots || 'docs/screenshots/vue')
const pages = resolvePages(normalizeList(argv.pages))

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: defaultViewport })
const results = []

for (const entry of pages) {
  const screenshotPath = path.join(screenshotDir, `${entry.key}.png`)
  const pageErrors = []
  page.removeAllListeners('pageerror')
  page.removeAllListeners('console')
  page.on('pageerror', (error) => pageErrors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') {
      pageErrors.push(message.text())
    }
  })

  await page.goto(entry.vueUrl, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1200)

  const target = entry.compareMode === 'full-page' ? page : page.locator(entry.vueSelector)
  await target.screenshot({ path: screenshotPath })
  const metrics = await collectMetrics(page, entry.vueSelector)

  results.push({
    ...entry,
    kind: 'vue',
    url: page.url(),
    screenshot: relativeFromRoot(screenshotPath),
    pageErrors,
    metrics,
  })
}

await browser.close()
await writeJson(outputPath, {
  generatedAt: new Date().toISOString(),
  kind: 'vue',
  viewport: defaultViewport,
  pages: results,
})

console.log(`Wrote ${relativeFromRoot(outputPath)}`)
