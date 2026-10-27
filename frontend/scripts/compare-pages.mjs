import fs from 'node:fs/promises'
import path from 'node:path'
import pixelmatch from 'pixelmatch'
import { PNG } from 'pngjs'
import {
  diffNumbers,
  parseArgs,
  readJson,
  relativeFromRoot,
  rootDir,
  writeJson,
  writeText,
} from './shared.mjs'

const argv = parseArgs(process.argv.slice(2))

if (argv.help || argv.h) {
  console.log(`
Usage:
  node scripts/compare-pages.mjs --legacy docs/runtime/legacy-pages.json --vue docs/runtime/vue-pages.json

Options:
  --legacy    Legacy metrics JSON, default: docs/runtime/legacy-pages.json
  --vue       Vue metrics JSON, default: docs/runtime/vue-pages.json
  --pages     Output compare JSON, default: docs/pages-compare.json
  --report    Output markdown report, default: docs/parity-report.md
  --visual    Output visual summary, default: docs/visual-diff-summary.md
  --help      Show this message
`.trim())
  process.exit(0)
}

const legacyData = await readJson(path.resolve(rootDir, argv.legacy || 'docs/runtime/legacy-pages.json'))
const vueData = await readJson(path.resolve(rootDir, argv.vue || 'docs/runtime/vue-pages.json'))

const legacyByKey = Object.fromEntries(legacyData.pages.map((page) => [page.key, page]))
const vueByKey = Object.fromEntries(vueData.pages.map((page) => [page.key, page]))

const comparisons = []

for (const key of Object.keys(legacyByKey)) {
  if (key === 'layout-shell') {
    continue
  }

  const legacyPage = legacyByKey[key]
  const vuePage = vueByKey[key]
  if (!vuePage) continue

  const metricDiff = {
    titleMatch: legacyPage.metrics?.title === vuePage.metrics?.title,
    visibleTextDelta: diffNumbers(legacyPage.metrics?.visibleTextCount, vuePage.metrics?.visibleTextCount),
    buttonDelta: diffNumbers(legacyPage.metrics?.buttons, vuePage.metrics?.buttons),
    linkDelta: diffNumbers(legacyPage.metrics?.links, vuePage.metrics?.links),
    formItemDelta: diffNumbers(legacyPage.metrics?.formItems, vuePage.metrics?.formItems),
    imageDelta: diffNumbers(legacyPage.metrics?.images, vuePage.metrics?.images),
    tableDelta: diffNumbers(legacyPage.metrics?.tables, vuePage.metrics?.tables),
    tableColumnDelta: diffNumbers(legacyPage.metrics?.tableColumns, vuePage.metrics?.tableColumns),
    cardModuleDelta: diffNumbers(legacyPage.metrics?.cardsOrModules, vuePage.metrics?.cardsOrModules),
    menuItemDelta: diffNumbers(legacyPage.metrics?.menuItems, vuePage.metrics?.menuItems),
  }

  const imageDiff = await compareImages(
    path.resolve(rootDir, legacyPage.screenshot),
    path.resolve(rootDir, vuePage.screenshot),
  )

  const reasons = []
  if (!metricDiff.titleMatch) reasons.push('title mismatch')
  if (legacyPage.pageErrors.length || vuePage.pageErrors.length) reasons.push('runtime errors detected')
  if (metricDiff.visibleTextDelta > 20) reasons.push('visible text count drift')
  if (metricDiff.buttonDelta > 1) reasons.push('button count drift')
  if (metricDiff.formItemDelta > 1) reasons.push('form item count drift')
  if (metricDiff.tableColumnDelta > 0) reasons.push('table column mismatch')
  if (imageDiff.diffRatio > 0.18) reasons.push('visual diff above 18%')
  if (imageDiff.dimensionMismatch) reasons.push('screenshot dimensions differ')

  const severity = classifySeverity(metricDiff, imageDiff, legacyPage.pageErrors, vuePage.pageErrors)

  comparisons.push({
    key,
    name: legacyPage.name,
    priority: legacyPage.priority,
    severity,
    reasons,
    legacy: legacyPage,
    vue: vuePage,
    diff: {
      ...metricDiff,
      pixelDiff: imageDiff.pixelDiff,
      diffRatio: imageDiff.diffRatio,
      dimensionMismatch: imageDiff.dimensionMismatch,
      width: imageDiff.width,
      height: imageDiff.height,
    },
  })
}

const totals = {
  pages: comparisons.length,
  passed: comparisons.filter((item) => item.severity !== 'high').length,
  high: comparisons.filter((item) => item.severity === 'high').length,
  medium: comparisons.filter((item) => item.severity === 'medium').length,
  low: comparisons.filter((item) => item.severity === 'low').length,
}

const pagesComparePath = path.resolve(rootDir, argv.pages || 'docs/pages-compare.json')
const reportPath = path.resolve(rootDir, argv.report || 'docs/parity-report.md')
const visualPath = path.resolve(rootDir, argv.visual || 'docs/visual-diff-summary.md')

await writeJson(pagesComparePath, {
  generatedAt: new Date().toISOString(),
  totals,
  pages: comparisons,
})

await writeText(reportPath, buildParityReport(totals, comparisons))
await writeText(visualPath, buildVisualSummary(comparisons))

console.log(`Wrote ${relativeFromRoot(pagesComparePath)}`)
console.log(`Wrote ${relativeFromRoot(reportPath)}`)
console.log(`Wrote ${relativeFromRoot(visualPath)}`)

function classifySeverity(metricDiff, imageDiff, legacyErrors, vueErrors) {
  if (legacyErrors.length || vueErrors.length) return 'high'
  if (!metricDiff.titleMatch) return 'high'
  if (metricDiff.tableColumnDelta > 0) return 'high'
  if (metricDiff.buttonDelta > 2 || metricDiff.formItemDelta > 2) return 'high'
  if (
    metricDiff.visibleTextDelta > 5 ||
    metricDiff.buttonDelta > 0 ||
    metricDiff.formItemDelta > 0 ||
    metricDiff.imageDelta > 0 ||
    metricDiff.cardModuleDelta > 2
  ) {
    return 'medium'
  }
  if (imageDiff.dimensionMismatch || imageDiff.diffRatio > 0.18) return 'medium'
  if (imageDiff.diffRatio > 0.06) return 'low'
  return 'low'
}

async function compareImages(leftPath, rightPath) {
  const [leftBuffer, rightBuffer] = await Promise.all([
    fs.readFile(leftPath),
    fs.readFile(rightPath),
  ])

  const left = PNG.sync.read(leftBuffer)
  const right = PNG.sync.read(rightBuffer)

  const width = Math.max(left.width, right.width)
  const height = Math.max(left.height, right.height)
  const leftImage = fitToCanvas(left, width, height)
  const rightImage = fitToCanvas(right, width, height)
  const diff = new PNG({ width, height })

  const pixelDiff = pixelmatch(
    leftImage.data,
    rightImage.data,
    diff.data,
    width,
    height,
    { threshold: 0.1 },
  )

  return {
    width,
    height,
    pixelDiff,
    diffRatio: pixelDiff / (width * height),
    dimensionMismatch: left.width !== right.width || left.height !== right.height,
  }
}

function fitToCanvas(image, width, height) {
  if (image.width === width && image.height === height) {
    return image
  }

  const canvas = new PNG({ width, height })
  PNG.bitblt(image, canvas, 0, 0, image.width, image.height, 0, 0)
  return canvas
}

function buildParityReport(totals, comparisons) {
  const lines = [
    '# Parity Report',
    '',
    '## Totals',
    `- Pages checked: ${totals.pages}`,
    `- Passed without high diff: ${totals.passed}`,
    `- High diff: ${totals.high}`,
    `- Medium diff: ${totals.medium}`,
    `- Low diff: ${totals.low}`,
    '',
    '## Page Results',
  ]

  comparisons.forEach((item) => {
    lines.push(`### ${item.name} (${item.key})`)
    lines.push(`- Priority: ${item.priority}`)
    lines.push(`- Severity: ${item.severity}`)
    lines.push(`- Legacy title: ${item.legacy.metrics?.title || 'n/a'}`)
    lines.push(`- Vue title: ${item.vue.metrics?.title || 'n/a'}`)
    lines.push(`- Pixel diff ratio: ${(item.diff.diffRatio * 100).toFixed(2)}%`)
    lines.push(`- Button delta: ${item.diff.buttonDelta}`)
    lines.push(`- Form delta: ${item.diff.formItemDelta}`)
    lines.push(`- Text delta: ${item.diff.visibleTextDelta}`)
    lines.push(`- Reasons: ${item.reasons.length ? item.reasons.join('; ') : 'No critical mismatch detected'}`)
    lines.push('')
  })

  return lines.join('\n')
}

function buildVisualSummary(comparisons) {
  const lines = [
    '# Visual Diff Summary',
    '',
    '| Page | Priority | Severity | Pixel Diff | Screenshot Pair |',
    '| --- | --- | --- | --- | --- |',
  ]

  comparisons.forEach((item) => {
    lines.push(
      `| ${item.name} | ${item.priority} | ${item.severity} | ${(item.diff.diffRatio * 100).toFixed(2)}% | ${item.legacy.screenshot} vs ${item.vue.screenshot} |`,
    )
  })

  return lines.join('\n')
}
