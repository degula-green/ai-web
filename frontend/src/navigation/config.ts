import type { RouteLocationRaw } from 'vue-router'

export type RouteNavKey =
  | 'data-dashboard'
  | 'ai-chat'
  | 'distribution'
  | 'data-collection'
  | 'brand-manager'
  | 'creation-video'
  | 'creation-article'
  | 'creation-avatar'
  | 'review'
  | 'schedule'
  | 'workflow'
  | 'agents'
  | 'platform'
  | 'workbench-dashboard'
  | 'workbench-ai-chat'
  | 'content-rewrite'
  | 'content-digital-human'
  | 'content-batch-article'
  | 'content-batch-video'
  | 'content-batch-humanized'
  | 'matrix-account-management'
  | 'matrix-content-publishing'
  | 'matrix-data-management'
  | 'brand-viral-library'
  | 'brand-new-product'
  | 'brand-hit-product'
  | 'brand-influencer'
  | 'experts'
  | 'marketplace'

export type ParentNavKey =
  | 'workbench-home'
  | 'content-creation'
  | 'content-production'
  | 'matrix-distribution'
  | 'brand-ip-strategy'

export type AppNavKey = RouteNavKey | ParentNavKey

interface NavigationRouteDefinition {
  key: RouteNavKey
  to: RouteLocationRaw
  parentKey?: ParentNavKey
  hidden?: boolean
}

interface NavigationDisplayDefinition {
  key: AppNavKey
  label: string
  icon?: string
  children?: RouteNavKey[]
}

const navigationRouteDefinitions: NavigationRouteDefinition[] = [
  { key: 'workbench-dashboard', to: { path: '/workbench/dashboard' }, parentKey: 'workbench-home' },
  { key: 'workbench-ai-chat', to: { path: '/workbench/ai-chat' }, parentKey: 'workbench-home' },
  { key: 'content-rewrite', to: { path: '/content-creation/rewrite' }, parentKey: 'content-creation' },
  { key: 'content-digital-human', to: { path: '/content-creation/digital-human/talk' }, parentKey: 'content-creation' },
  { key: 'content-batch-article', to: { path: '/content-production/article-batch' }, parentKey: 'content-production' },
  { key: 'content-batch-video', to: { path: '/content-production/video-batch' }, parentKey: 'content-production' },
  { key: 'content-batch-humanized', to: { path: '/content-production/humanized-batch' }, parentKey: 'content-production' },
  { key: 'matrix-account-management', to: { path: '/matrix-distribution/accounts' }, parentKey: 'matrix-distribution' },
  { key: 'matrix-content-publishing', to: { path: '/matrix-distribution/publishing' }, parentKey: 'matrix-distribution' },
  { key: 'matrix-data-management', to: { path: '/matrix-distribution/data' }, parentKey: 'matrix-distribution' },
  { key: 'brand-viral-library', to: { path: '/brand-ip/viral-library' }, parentKey: 'brand-ip-strategy' },
  { key: 'brand-new-product', to: { path: '/brand-ip/new-product' }, parentKey: 'brand-ip-strategy' },
  { key: 'brand-hit-product', to: { path: '/brand-ip/hit-product' }, parentKey: 'brand-ip-strategy' },
  { key: 'brand-influencer', to: { path: '/brand-ip/influencer' }, parentKey: 'brand-ip-strategy' },
  { key: 'experts', to: { path: '/experts' } },
  { key: 'marketplace', to: { path: '/marketplace' } },

  { key: 'data-dashboard', to: { path: '/dashboard' }, hidden: true },
  { key: 'ai-chat', to: { path: '/ai-chat' }, hidden: true },
  { key: 'distribution', to: { path: '/distribution' }, hidden: true },
  { key: 'data-collection', to: { path: '/data-collection' }, hidden: true },
  { key: 'brand-manager', to: { path: '/brand-manager' }, hidden: true },
  { key: 'creation-video', to: { path: '/creation/video', query: { mode: 'video' } }, hidden: true },
  { key: 'creation-article', to: { path: '/creation/article', query: { mode: 'article' } }, hidden: true },
  { key: 'creation-avatar', to: { path: '/creation/avatar' }, hidden: true },
  { key: 'review', to: { path: '/review' }, hidden: true },
  { key: 'schedule', to: { path: '/schedule' }, hidden: true },
  { key: 'workflow', to: { path: '/workflow' }, hidden: true },
  { key: 'agents', to: { path: '/agents' }, hidden: true },
  { key: 'platform', to: { path: '/platform' }, hidden: true },
]

export const defaultNavRoute = navigationRouteDefinitions.find(
  (item) => item.key === 'workbench-dashboard',
)!.to

export const routeLocationByKey = Object.fromEntries(
  navigationRouteDefinitions.map((item) => [item.key, item.to]),
) as Record<RouteNavKey, RouteLocationRaw>

export const parentKeyByRouteKey = Object.fromEntries(
  navigationRouteDefinitions
    .filter((item) => item.parentKey)
    .map((item) => [item.key, item.parentKey]),
) as Partial<Record<RouteNavKey, ParentNavKey>>

export const childRouteKeysByParent = navigationRouteDefinitions.reduce(
  (accumulator, item) => {
    if (!item.parentKey) {
      return accumulator
    }

    const siblings = accumulator[item.parentKey] ?? []
    siblings.push(item.key)
    accumulator[item.parentKey] = siblings
    return accumulator
  },
  {} as Partial<Record<ParentNavKey, RouteNavKey[]>>,
)

const navigationDisplayDefinitions: NavigationDisplayDefinition[] = [
  {
    key: 'workbench-home',
    label: '工作台首页',
    icon: 'home',
    children: ['workbench-dashboard', 'workbench-ai-chat'],
  },
  {
    key: 'content-creation',
    label: '内容创作',
    icon: 'edit_square',
    children: ['content-rewrite', 'content-digital-human'],
  },
  {
    key: 'content-production',
    label: '内容量产',
    icon: 'library_add',
    children: ['content-batch-article', 'content-batch-video', 'content-batch-humanized'],
  },
  {
    key: 'matrix-distribution',
    label: '矩阵分发',
    icon: 'device_hub',
    children: ['matrix-account-management', 'matrix-content-publishing', 'matrix-data-management'],
  },
  {
    key: 'brand-ip-strategy',
    label: '品牌/IP策划',
    icon: 'strategy',
    children: ['brand-viral-library', 'brand-new-product', 'brand-hit-product', 'brand-influencer'],
  },
  { key: 'workbench-dashboard', label: '数据总览' },
  { key: 'workbench-ai-chat', label: 'AI对话' },
  { key: 'content-rewrite', label: '一键仿写' },
  { key: 'content-digital-human', label: '数字人' },
  { key: 'content-batch-article', label: '图文量产' },
  { key: 'content-batch-video', label: '视频量产' },
  { key: 'content-batch-humanized', label: '拟人量产' },
  { key: 'matrix-account-management', label: '账号管理' },
  { key: 'matrix-content-publishing', label: '内容发布' },
  { key: 'matrix-data-management', label: '数据管理' },
  { key: 'brand-viral-library', label: '爆文库' },
  { key: 'brand-new-product', label: '新品策划（0-1）' },
  { key: 'brand-hit-product', label: '爆品策划（1-100）' },
  { key: 'brand-influencer', label: '红人策划' },
  { key: 'experts', label: '专家库', icon: 'groups_2' },
  { key: 'marketplace', label: '自由交易市场', icon: 'storefront' },
]

export const navigationDisplayByKey = Object.fromEntries(
  navigationDisplayDefinitions.map((item) => [item.key, item]),
) as Record<AppNavKey, NavigationDisplayDefinition>

export const primaryNavigationKeys: AppNavKey[] = [
  'workbench-home',
  'content-creation',
  'content-production',
  'matrix-distribution',
  'brand-ip-strategy',
  'experts',
  'marketplace',
]

export function isRouteNavKey(value: string): value is RouteNavKey {
  return value in routeLocationByKey
}

export function isParentNavKey(value: AppNavKey): value is ParentNavKey {
  return value in childRouteKeysByParent
}

export function isParentNavKeyActive(parentKey: ParentNavKey, currentKey?: string) {
  if (!currentKey || !isRouteNavKey(currentKey)) {
    return false
  }

  return (childRouteKeysByParent[parentKey] ?? []).includes(currentKey)
}
