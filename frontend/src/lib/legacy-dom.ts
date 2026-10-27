export interface LegacyRenderOptions {
  container: HTMLElement
  html: string
  scope: string
  isolateIds?: boolean
  executeScripts?: boolean
  functionNames?: string[]
  transformBodyHtml?: (html: string) => string
}

export interface LegacyRenderResult {
  cleanup: () => void
  scopeApi: Record<string, (...args: unknown[]) => unknown>
  title: string
}

interface ParsedLegacyDocument {
  title: string
  bodyClassName: string
  bodyStyle: string
  bodyHtml: string
  styles: string[]
  scripts: string[]
  idMap: Map<string, string>
}

export function ensureLegacyScope(scope: string) {
  window.__legacyScopes ??= {}
  window.__legacyScopes[scope] ??= {}
  return window.__legacyScopes[scope]
}

export function renderLegacyFragment(options: LegacyRenderOptions): LegacyRenderResult {
  const {
    container,
    html,
    scope,
    isolateIds = true,
    executeScripts = true,
    functionNames = [],
    transformBodyHtml,
  } = options

  const parsed = parseLegacyHtml(html, scope, isolateIds)
  const scopedFunctionNames = [...new Set([...functionNames, ...collectFunctionNames(parsed.scripts)])]
  const wrapperSelector = `[data-legacy-body="${scope}"]`
  const styles = parsed.styles.map((style, index) => {
    const element = document.createElement('style')
    element.dataset.legacyStyle = `${scope}-${index}`
    element.textContent = rewriteCssIds(scopeBodySelectors(style, wrapperSelector), parsed.idMap)
    document.head.appendChild(element)
    return element
  })

  const scopeApi = ensureLegacyScope(scope)
  Object.keys(scopeApi).forEach((key) => delete scopeApi[key])

  const bodyHtml = transformBodyHtml ? transformBodyHtml(parsed.bodyHtml) : parsed.bodyHtml
  const bodyDocument = new DOMParser().parseFromString(`<body>${bodyHtml}</body>`, 'text/html')
  rewriteInlineHandlers(bodyDocument.body, scope, scopedFunctionNames)

  const wrapper = document.createElement('div')
  wrapper.className = parsed.bodyClassName
  wrapper.dataset.legacyBody = scope
  wrapper.style.cssText = parsed.bodyStyle
  wrapper.innerHTML = bodyDocument.body.innerHTML

  container.innerHTML = ''
  container.appendChild(wrapper)

  if (executeScripts) {
    parsed.scripts
      .map((script) => rewriteScriptIds(script, parsed.idMap))
      .forEach((script) => runLegacyScript(script, scopeApi, scopedFunctionNames))
  }

  return {
    title: parsed.title,
    scopeApi,
    cleanup: () => {
      styles.forEach((style) => style.remove())
      container.innerHTML = ''
      delete window.__legacyScopes?.[scope]
    },
  }
}

function parseLegacyHtml(html: string, scope: string, isolateIds: boolean): ParsedLegacyDocument {
  const doc = new DOMParser().parseFromString(html, 'text/html')
  const body = doc.body.cloneNode(true) as HTMLBodyElement
  const scripts = Array.from(body.querySelectorAll('script'))
    .map((script) => script.textContent ?? '')
    .filter(Boolean)
  body.querySelectorAll('script').forEach((script) => script.remove())

  const idMap = new Map<string, string>()
  if (isolateIds) {
    const elementsWithId = body.querySelectorAll<HTMLElement>('[id]')
    elementsWithId.forEach((element) => {
      const originalId = element.id
      const newId = `${scope}__${originalId}`
      idMap.set(originalId, newId)
      element.id = newId
    })
    rewriteReferencedAttributes(body, idMap)
  }

  return {
    title: doc.title.trim(),
    bodyClassName: body.className,
    bodyStyle: body.getAttribute('style') ?? '',
    bodyHtml: body.innerHTML,
    styles: Array.from(doc.querySelectorAll('style')).map((style) => style.textContent ?? ''),
    scripts,
    idMap,
  }
}

function rewriteReferencedAttributes(root: HTMLElement, idMap: Map<string, string>) {
  const referenceAttrs = ['for', 'aria-controls', 'aria-labelledby', 'aria-describedby', 'list']
  root.querySelectorAll<HTMLElement>('*').forEach((element) => {
    referenceAttrs.forEach((attr) => {
      const current = element.getAttribute(attr)
      if (!current) return
      if (idMap.has(current)) {
        element.setAttribute(attr, idMap.get(current)!)
      }
    })

    const href = element.getAttribute('href')
    if (href?.startsWith('#')) {
      const targetId = href.slice(1)
      if (idMap.has(targetId)) {
        element.setAttribute('href', `#${idMap.get(targetId)}`)
      }
    }
  })
}

function rewriteInlineHandlers(root: HTMLElement, scope: string, functionNames: string[]) {
  const safeFunctionNames = [...new Set(functionNames)].sort((left, right) => right.length - left.length)
  root.querySelectorAll<HTMLElement>('*').forEach((element) => {
    Array.from(element.attributes)
      .filter((attribute) => attribute.name.startsWith('on'))
      .forEach((attribute) => {
        let nextValue = attribute.value
        safeFunctionNames.forEach((functionName) => {
          const pattern = new RegExp(`\\b${functionName}\\s*\\(`, 'g')
          nextValue = nextValue.replace(
            pattern,
            `window.__legacyScopes["${scope}"].${functionName}(`,
          )
        })
        element.setAttribute(attribute.name, nextValue)
      })
  })
}

function collectFunctionNames(scripts: string[]) {
  return scripts.flatMap((script) =>
    Array.from(script.matchAll(/function\s+([A-Za-z_$][\w$]*)/g), (match) => match[1]),
  )
}

function scopeBodySelectors(css: string, bodySelector: string) {
  return css
    .replace(/\bhtml\b/g, bodySelector)
    .replace(/\bbody\b/g, bodySelector)
}

function rewriteCssIds(css: string, idMap: Map<string, string>) {
  let output = css
  idMap.forEach((newId, oldId) => {
    output = output.replaceAll(`#${oldId}`, `#${newId}`)
  })
  return output
}

function rewriteScriptIds(script: string, idMap: Map<string, string>) {
  let output = script
  idMap.forEach((newId, oldId) => {
    const escapedOldId = escapeRegExp(oldId)
    output = output.replace(
      new RegExp(`getElementById\\((['"\`])${escapedOldId}\\1\\)`, 'g'),
      `getElementById('${
        newId
      }')`,
    )
    output = output.replace(
      new RegExp(`([#])${escapedOldId}\\b`, 'g'),
      `#${newId}`,
    )
  })
  return output
}

function runLegacyScript(
  script: string,
  scopeApi: Record<string, (...args: unknown[]) => unknown>,
  functionNames: string[],
) {
  const exportsBlock = functionNames
    .map(
      (name) =>
        `if (typeof ${name} === 'function') { scopeApi[${JSON.stringify(name)}] = ${name}; }`,
    )
    .join('\n')

  const executor = new Function(
    'scopeApi',
    'window',
    'document',
    `${script}\n${exportsBlock}`,
  )

  executor(scopeApi, window, document)
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
