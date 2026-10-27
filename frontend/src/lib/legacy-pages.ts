import legacyLayoutHtml from '../legacy/index.html?raw'
import dashboardHtml from '../legacy/pages/1.html?raw'
import distributionHtml from '../legacy/pages/2.html?raw'
import agentsHtml from '../legacy/pages/agents.html?raw'
import creationHtml from '../legacy/pages/creation.html?raw'
import platformHtml from '../legacy/pages/platfrom.html?raw'
import reviewHtml from '../legacy/pages/review.html?raw'
import scheduleHtml from '../legacy/pages/schedule.html?raw'
import workflowHtml from '../legacy/pages/workflow.html?raw'
import { defaultNavRoute, routeLocationByKey as navRouteLocationByKey, type RouteNavKey } from '../navigation/config'

export type LegacyPageKey = RouteNavKey

export interface LegacyPageDefinition {
  key: LegacyPageKey
  title: string
  path: string
  scope: string
  priority: 'P0' | 'P1'
  legacySrc: string
  html: string
  query?: Record<string, string>
}

export const defaultLegacyRoute = defaultNavRoute

export const legacyLayoutSource = legacyLayoutHtml

export const legacyPages: LegacyPageDefinition[] = [
  {
    key: 'data-dashboard',
    title: '数据看板 - 全渠道数据闭环仪表盘',
    path: '/dashboard',
    scope: 'dashboard',
    priority: 'P0',
    legacySrc: '1.html',
    html: dashboardHtml,
  },
  {
    key: 'distribution',
    title: '分发内容页 - 工作流系统',
    path: '/distribution',
    scope: 'distribution',
    priority: 'P0',
    legacySrc: '2.html',
    html: distributionHtml,
  },
  {
    key: 'data-collection',
    title: '数据采集平台',
    path: '/data-collection',
    scope: 'data-collection',
    priority: 'P0',
    legacySrc: '',
    html: '',
  },
  {
    key: 'brand-manager',
    title: '品牌资产管理',
    path: '/brand-manager',
    scope: 'brand-manager',
    priority: 'P0',
    legacySrc: '',
    html: '',
  },
  {
    key: 'ai-chat',
    title: 'AI对话',
    path: '/ai-chat',
    scope: 'ai-chat',
    priority: 'P0',
    legacySrc: '',
    html: '',
  },
  {
    key: 'creation-video',
    title: 'AI内容仿写创作台',
    path: '/creation/video',
    scope: 'creation-video',
    priority: 'P0',
    legacySrc: 'creation.html?mode=video',
    html: creationHtml,
    query: { mode: 'video' },
  },
  {
    key: 'creation-article',
    title: 'AI内容仿写创作台',
    path: '/creation/article',
    scope: 'creation-article',
    priority: 'P0',
    legacySrc: 'creation.html?mode=article',
    html: creationHtml,
    query: { mode: 'article' },
  },
  {
    key: 'creation-avatar',
    title: '口播数字人创作台',
    path: '/creation/avatar',
    scope: 'creation-avatar',
    priority: 'P0',
    legacySrc: '',
    html: '',
  },
  {
    key: 'review',
    title: 'AI Content Auto - Content Review',
    path: '/review',
    scope: 'review',
    priority: 'P0',
    legacySrc: 'review.html',
    html: reviewHtml,
  },
  {
    key: 'schedule',
    title: '任务批处理与发布计划表',
    path: '/schedule',
    scope: 'schedule',
    priority: 'P1',
    legacySrc: 'schedule.html',
    html: scheduleHtml,
  },
  {
    key: 'workflow',
    title: 'AI工作流编排与控制台 (浅色版)',
    path: '/workflow',
    scope: 'workflow',
    priority: 'P1',
    legacySrc: 'workflow.html',
    html: workflowHtml,
  },
  {
    key: 'agents',
    title: '多智能体配置与调优中心',
    path: '/agents',
    scope: 'agents',
    priority: 'P1',
    legacySrc: 'agents.html',
    html: agentsHtml,
  },
  {
    key: 'platform',
    title: 'AI内容自动化 - 平台授权',
    path: '/platform',
    scope: 'platform',
    priority: 'P1',
    legacySrc: 'platfrom.html',
    html: platformHtml,
  },
]

export const legacyPagesByKey = Object.fromEntries(
  legacyPages.map((page) => [page.key, page]),
) as Record<LegacyPageKey, LegacyPageDefinition>

export const routeLocationByKey = navRouteLocationByKey
