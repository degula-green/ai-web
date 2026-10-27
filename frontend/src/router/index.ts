import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationRaw } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import AgentsView from '../views/AgentsView.vue'
import CreationArticleView from '../views/CreationArticleView.vue'
import CreationAvatarView from '../views/CreationAvatarView.vue'
import CreationAvatarTalkView from '../views/CreationAvatarTalkView.vue'
import CreationAvatarSalesView from '../views/CreationAvatarSalesView.vue'
import CreationAvatarProductView from '../views/CreationAvatarProductView.vue'
import CreationAvatarClipView from '../views/CreationAvatarClipView.vue'
import CreationAvatarModelView from '../views/CreationAvatarModelView.vue'
import CreationVideoView from '../views/CreationVideoView.vue'
import DashboardView from '../views/DashboardView.vue'
import DistributionView from '../views/DistributionView.vue'
import PlatformAuthView from '../views/PlatformAuthView.vue'
import ReservedWorkspaceView from '../views/ReservedWorkspaceView.vue'
import ReviewView from '../views/ReviewView.vue'
import ScheduleView from '../views/ScheduleView.vue'
import StaticImagePageView from '../views/StaticImagePageView.vue'
import WorkflowView from '../views/WorkflowView.vue'
import { authStore } from '../auth/store'
import RegisterView from '../views/auth/RegisterView.vue'
import {
  defaultNavRoute,
  isRouteNavKey,
  routeLocationByKey,
  type RouteNavKey,
} from '../navigation/config'

function withRequiredMode(mode: 'video' | 'article') {
  return (to: { path: string; query: Record<string, unknown> }): RouteLocationRaw | undefined => {
    if (to.query.mode === mode) {
      return undefined
    }

    return {
      path: to.path,
      query: {
        ...to.query,
        mode,
      },
      replace: true,
    }
  }
}

function resolveLegacyHash(hash: string) {
  if (!hash) {
    return undefined
  }

  const key = hash.replace(/^#/, '')
  return isRouteNavKey(key) ? routeLocationByKey[key] : undefined
}

function buildRouteMeta(key: RouteNavKey) {
  return {
    legacyKey: key,
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: (to) => resolveLegacyHash(to.hash) ?? defaultNavRoute,
    },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: 'workbench/dashboard',
          name: 'workbench-dashboard',
          component: DashboardView,
          meta: buildRouteMeta('workbench-dashboard'),
        },
        {
          path: 'workbench/ai-chat',
          name: 'workbench-ai-chat',
          component: () => import('../views/ai-chat/index.vue'),
          meta: buildRouteMeta('workbench-ai-chat'),
        },
        {
          path: 'content-creation/rewrite',
          name: 'content-rewrite',
          component: StaticImagePageView,
          props: {
            title: '一键仿写',
            breadcrumb: '内容创作 / 一键仿写',
            imageSrc: '/reference-pages/one-click-rewrite.png',
          },
          meta: buildRouteMeta('content-rewrite'),
        },
        {
          path: 'content-creation/digital-human',
          name: 'content-digital-human',
          redirect: (to) => ({
            path: '/content-creation/digital-human/talk',
            query: to.query,
          }),
          meta: buildRouteMeta('content-digital-human'),
        },
        {
          path: 'content-creation/digital-human/talk',
          name: 'content-digital-human-talk',
          component: CreationAvatarTalkView,
          meta: buildRouteMeta('content-digital-human'),
        },
        {
          path: 'content-creation/digital-human/sales',
          name: 'content-digital-human-sales',
          component: CreationAvatarSalesView,
          meta: buildRouteMeta('content-digital-human'),
        },
        {
          path: 'content-creation/digital-human/product',
          name: 'content-digital-human-product',
          component: CreationAvatarProductView,
          meta: buildRouteMeta('content-digital-human'),
        },
        {
          path: 'content-creation/digital-human/model',
          name: 'content-digital-human-model',
          component: CreationAvatarModelView,
          meta: buildRouteMeta('content-digital-human'),
        },
        {
          path: 'content-creation/digital-human/clip',
          name: 'content-digital-human-clip',
          component: CreationAvatarClipView,
          meta: buildRouteMeta('content-digital-human'),
        },
        {
          path: 'content-production/article-batch',
          name: 'content-batch-article',
          component: CreationArticleView,
          beforeEnter: withRequiredMode('article'),
          meta: buildRouteMeta('content-batch-article'),
        },
        {
          path: 'content-production/video-batch',
          name: 'content-batch-video',
          component: CreationVideoView,
          beforeEnter: withRequiredMode('video'),
          meta: buildRouteMeta('content-batch-video'),
        },
        {
          path: 'content-production/humanized-batch',
          name: 'content-batch-humanized',
          component: ReservedWorkspaceView,
          props: {
            title: '拟人量产',
            breadcrumb: '内容量产 / 拟人量产',
          },
          meta: buildRouteMeta('content-batch-humanized'),
        },
        {
          path: 'matrix-distribution/accounts',
          name: 'matrix-account-management',
          component: PlatformAuthView,
          meta: buildRouteMeta('matrix-account-management'),
        },
        {
          path: 'matrix-distribution/publishing',
          name: 'matrix-content-publishing',
          component: ScheduleView,
          meta: buildRouteMeta('matrix-content-publishing'),
        },
        {
          path: 'matrix-distribution/data',
          name: 'matrix-data-management',
          component: DistributionView,
          meta: buildRouteMeta('matrix-data-management'),
        },
        {
          path: 'brand-ip/viral-library',
          name: 'brand-viral-library',
          component: () => import('../views/data-collection/index.vue'),
          meta: buildRouteMeta('brand-viral-library'),
        },
        {
          path: 'brand-ip/new-product',
          name: 'brand-new-product',
          component: () => import('../views/brand-manager/index.vue'),
          meta: buildRouteMeta('brand-new-product'),
        },
        {
          path: 'brand-ip/hit-product',
          name: 'brand-hit-product',
          component: StaticImagePageView,
          props: {
            title: '爆品策划（1-100）',
            breadcrumb: '品牌/IP策划 / 爆品策划（1-100）',
            imageSrc: '/reference-pages/hit-product-strategy.png',
          },
          meta: buildRouteMeta('brand-hit-product'),
        },
        {
          path: 'brand-ip/influencer',
          name: 'brand-influencer',
          component: ReservedWorkspaceView,
          props: {
            title: '红人策划',
            breadcrumb: '品牌/IP策划 / 红人策划',
          },
          meta: buildRouteMeta('brand-influencer'),
        },
        {
          path: 'experts',
          name: 'experts',
          component: AgentsView,
          meta: buildRouteMeta('experts'),
        },
        {
          path: 'marketplace',
          name: 'marketplace',
          component: ReservedWorkspaceView,
          props: {
            title: '自由交易市场',
            breadcrumb: '自由交易市场',
          },
          meta: buildRouteMeta('marketplace'),
        },
        {
          path: 'profile',
          name: 'profile',
          component: DashboardView, // Removed ProfileView route
          meta: {},
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
          meta: buildRouteMeta('workbench-dashboard'),
        },
        {
          path: 'distribution',
          name: 'distribution',
          component: DistributionView,
          meta: buildRouteMeta('matrix-data-management'),
        },
        {
          path: 'data-collection',
          name: 'data-collection',
          component: () => import('../views/data-collection/index.vue'),
          meta: buildRouteMeta('brand-viral-library'),
        },
        {
          path: 'brand-manager',
          name: 'brand-manager',
          component: () => import('../views/brand-manager/index.vue'),
          meta: buildRouteMeta('brand-new-product'),
        },
        {
          path: 'brand-manager/detail/:id',
          name: 'brand-manager-detail',
          component: () => import('../views/brand-manager/detail.vue'),
          meta: buildRouteMeta('brand-new-product'),
        },
        {
          path: 'ai-chat',
          name: 'ai-chat',
          component: () => import('../views/ai-chat/index.vue'),
          meta: buildRouteMeta('workbench-ai-chat'),
        },
        {
          path: 'data-collection/platform',
          name: 'data-collection-platform',
          component: () => import('../views/data-collection/platform-detail.vue'),
          meta: buildRouteMeta('brand-viral-library'),
        },
        {
          path: 'creation/video',
          name: 'creation-video',
          component: CreationVideoView,
          beforeEnter: withRequiredMode('video'),
          meta: buildRouteMeta('content-batch-video'),
        },
        {
          path: 'creation/article',
          name: 'creation-article',
          component: CreationArticleView,
          beforeEnter: withRequiredMode('article'),
          meta: buildRouteMeta('content-batch-article'),
        },
        {
          path: 'creation/avatar',
          name: 'creation-avatar',
          component: CreationAvatarView,
          meta: buildRouteMeta('content-digital-human'),
        },
        {
          path: 'review',
          name: 'review',
          component: ReviewView,
          meta: buildRouteMeta('review'),
        },
        {
          path: 'schedule',
          name: 'schedule',
          component: ScheduleView,
          meta: buildRouteMeta('matrix-content-publishing'),
        },
        {
          path: 'workflow',
          name: 'workflow',
          component: WorkflowView,
          meta: buildRouteMeta('workflow'),
        },
        {
          path: 'agents',
          name: 'agents',
          component: AgentsView,
          meta: buildRouteMeta('experts'),
        },
        {
          path: 'platform',
          name: 'platform',
          component: PlatformAuthView,
          meta: buildRouteMeta('matrix-account-management'),
        },
      ],
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { guestOnly: true },
    },
  ],
  scrollBehavior() {
    return { left: 0, top: 0 }
  },
})

router.beforeEach(async (to) => {
  await authStore.ensureInitialized()

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const guestOnly = to.matched.some((record) => record.meta.guestOnly)

  if (guestOnly && authStore.isAuthenticated.value) {
    return typeof to.query.redirect === 'string' ? to.query.redirect : '/dashboard'
  }

  if (requiresAuth && !authStore.isAuthenticated.value) {
    return {
      name: 'register',
      query: { redirect: to.fullPath },
    }
  }

  return true
})

export default router
