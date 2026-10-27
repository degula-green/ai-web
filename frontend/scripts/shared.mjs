import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const rootDir = fileURLToPath(new URL('..', import.meta.url))
export const defaultViewport = { width: 1440, height: 960 }

export const pageConfigs = [
  {
    key: 'layout-shell',
    name: '旧系统壳层',
    priority: 'P0',
    legacyPath: 'index.html',
    legacyUrl: 'http://127.0.0.1:4174/index.html',
    vueUrl: 'http://127.0.0.1:4173/#creation-video',
    legacySelector: 'body',
    vueSelector: 'body',
    compareMode: 'full-page',
  },
  {
    key: 'data-dashboard',
    name: '数据看板',
    priority: 'P0',
    legacyPath: '1.html',
    legacyUrl: 'http://127.0.0.1:4174/1.html',
    vueUrl: 'http://127.0.0.1:4173/#data-dashboard',
    legacySelector: 'body',
    vueSelector: '#content-frame',
    compareMode: 'content',
  },
  {
    key: 'distribution',
    name: '分发内容管理',
    priority: 'P0',
    legacyPath: '2.html',
    legacyUrl: 'http://127.0.0.1:4174/2.html',
    vueUrl: 'http://127.0.0.1:4173/#distribution',
    legacySelector: 'body',
    vueSelector: '#content-frame',
    compareMode: 'content',
  },
  {
    key: 'creation-video',
    name: '创作台-视频',
    priority: 'P0',
    legacyPath: 'creation.html?mode=video',
    legacyUrl: 'http://127.0.0.1:4174/creation.html?mode=video',
    vueUrl: 'http://127.0.0.1:4173/#creation-video',
    legacySelector: 'body',
    vueSelector: '#content-frame',
    compareMode: 'content',
  },
  {
    key: 'creation-article',
    name: '创作台-图文',
    priority: 'P0',
    legacyPath: 'creation.html?mode=article',
    legacyUrl: 'http://127.0.0.1:4174/creation.html?mode=article',
    vueUrl: 'http://127.0.0.1:4173/#creation-article',
    legacySelector: 'body',
    vueSelector: '#content-frame',
    compareMode: 'content',
  },
  {
    key: 'review',
    name: '内容审核',
    priority: 'P0',
    legacyPath: 'review.html',
    legacyUrl: 'http://127.0.0.1:4174/review.html',
    vueUrl: 'http://127.0.0.1:4173/#review',
    legacySelector: 'body',
    vueSelector: '#content-frame',
    compareMode: 'content',
  },
  {
    key: 'schedule',
    name: '发布计划',
    priority: 'P1',
    legacyPath: 'schedule.html',
    legacyUrl: 'http://127.0.0.1:4174/schedule.html',
    vueUrl: 'http://127.0.0.1:4173/#schedule',
    legacySelector: 'body',
    vueSelector: '#content-frame',
    compareMode: 'content',
  },
  {
    key: 'workflow',
    name: '工作流编排',
    priority: 'P1',
    legacyPath: 'workflow.html',
    legacyUrl: 'http://127.0.0.1:4174/workflow.html',
    vueUrl: 'http://127.0.0.1:4173/#workflow',
    legacySelector: 'body',
    vueSelector: '#content-frame',
    compareMode: 'content',
  },
  {
    key: 'agents',
    name: '多智能体中心',
    priority: 'P1',
    legacyPath: 'agents.html',
    legacyUrl: 'http://127.0.0.1:4174/agents.html',
    vueUrl: 'http://127.0.0.1:4173/#agents',
    legacySelector: 'body',
    vueSelector: '#content-frame',
    compareMode: 'content',
  },
  {
    key: 'platform',
    name: '平台授权',
    priority: 'P1',
    legacyPath: 'platfrom.html',
    legacyUrl: 'http://127.0.0.1:4174/platfrom.html',
    vueUrl: 'http://127.0.0.1:4173/#platform',
    legacySelector: 'body',
    vueSelector: '#content-frame',
    compareMode: 'content',
  },
]

export function parseArgs(argv) {
  const args = {}

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index]
    if (!token.startsWith('--')) continue

    const keyValue = token.slice(2).split('=')
    if (keyValue.length > 1) {
      const [key, ...rest] = keyValue
      args[key] = rest.join('=')
      continue
    }

    const next = argv[index + 1]
    if (!next || next.startsWith('--')) {
      args[token.slice(2)] = true
      continue
    }

    args[token.slice(2)] = next
    index += 1
  }

  return args
}

export async function ensureDir(filePath) {
  await fs.mkdir(path.dirname(filePath), { recursive: true })
}

export async function writeJson(filePath, data) {
  await ensureDir(filePath)
  await fs.writeFile(filePath, `${JSON.stringify(data, null, 2)}\n`, 'utf8')
}

export async function writeText(filePath, text) {
  await ensureDir(filePath)
  await fs.writeFile(filePath, text, 'utf8')
}

export async function readJson(filePath) {
  const text = await fs.readFile(filePath, 'utf8')
  return JSON.parse(text)
}

export function normalizeList(value) {
  if (!value) return []
  return String(value)
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function resolvePages(selectedKeys) {
  if (!selectedKeys.length) {
    return pageConfigs
  }

  const requested = new Set(selectedKeys)
  return pageConfigs.filter((page) => requested.has(page.key))
}

export function relativeFromRoot(filePath) {
  return path.relative(rootDir, filePath).replaceAll('\\', '/')
}

export async function collectMetrics(page, selector = 'body') {
  return page.evaluate((query) => {
    const root = query === 'body' ? document.body : document.querySelector(query)
    const visible = (element) => {
      if (!(element instanceof HTMLElement)) return false
      const style = window.getComputedStyle(element)
      const rect = element.getBoundingClientRect()
      return (
        style.display !== 'none' &&
        style.visibility !== 'hidden' &&
        style.opacity !== '0' &&
        rect.width > 0 &&
        rect.height > 0
      )
    }

    if (!root) {
      return null
    }

    const textContent = root.innerText
      .split(/\s+/)
      .map((value) => value.trim())
      .filter(Boolean)

    const firstTable = root.querySelector('table')
    const tableColumns = firstTable
      ? firstTable.querySelectorAll('thead th').length ||
        firstTable.querySelectorAll('tr:first-child th, tr:first-child td').length
      : 0

    const menuItems = root.querySelectorAll('#main-nav .nav-item, #main-nav .sub-nav-item').length
    const activeMenu = Array.from(
      root.querySelectorAll('#main-nav .nav-item.active, #main-nav .sub-nav-item.active'),
    ).map((element) => element.textContent?.trim()).filter(Boolean)

    return {
      title: document.title,
      heading:
        root.querySelector('h1, h2, h3')?.textContent?.replace(/\s+/g, ' ').trim() || '',
      textSample: textContent.slice(0, 40),
      visibleTextCount: textContent.length,
      buttons: Array.from(root.querySelectorAll('button')).filter(visible).length,
      links: Array.from(root.querySelectorAll('a')).filter(visible).length,
      formItems: Array.from(root.querySelectorAll('input, select, textarea')).filter(visible).length,
      images: Array.from(root.querySelectorAll('img')).filter(visible).length,
      tables: root.querySelectorAll('table').length,
      tableColumns,
      cardsOrModules: root.querySelectorAll('section, article, form, table, .rounded-2xl, .rounded-xl').length,
      menuItems,
      activeMenu,
    }
  }, selector)
}

export function diffNumbers(left, right) {
  return Math.abs((left || 0) - (right || 0))
}
