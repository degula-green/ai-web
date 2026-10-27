<template>
  <aside id="sidebar">
    <div class="sidebar-logo">
      <div class="logo-icon">
        <span class="material-symbols-outlined">auto_fix_high</span>
      </div>
      <div class="logo-text">
        <h1>内容营销自动化</h1>
        <span>工作台系统 V2.0</span>
      </div>
    </div>

    <nav id="main-nav">
      <template v-for="key in primaryNavigationKeys" :key="key">
        <div v-if="isParentNavKey(key)">
          <button
            class="nav-item has-sub"
            :class="{ active: isParentNavKeyActive(key, currentKey) }"
            type="button"
            @click="toggleGroup(key)"
          >
            <span class="material-symbols-outlined">{{ navigationDisplayByKey[key].icon }}</span>
            <span class="nav-label" style="flex: 1">{{ navigationDisplayByKey[key].label }}</span>
            <span class="material-symbols-outlined" style="font-size: 16px">expand_more</span>
          </button>
          <div class="sub-nav" :class="{ collapsed: isCollapsed(key) }">
            <button
              v-for="childKey in navigationDisplayByKey[key].children"
              :key="childKey"
              class="sub-nav-item"
              :class="{ active: currentKey === childKey }"
              type="button"
              @click="goToRoute(childKey)"
            >
              {{ navigationDisplayByKey[childKey].label }}
            </button>
          </div>
        </div>

        <button
          v-else
          class="nav-item"
          :class="{ active: currentKey === key }"
          type="button"
          @click="goToRoute(key)"
        >
          <span class="material-symbols-outlined">{{ navigationDisplayByKey[key].icon }}</span>
          <span class="nav-label">{{ navigationDisplayByKey[key].label }}</span>
        </button>
      </template>
    </nav>

    <UserMenuPanel />
  </aside>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UserMenuPanel from './UserMenuPanel.vue'
import {
  childRouteKeysByParent,
  isParentNavKey,
  isParentNavKeyActive,
  navigationDisplayByKey,
  primaryNavigationKeys,
  routeLocationByKey,
  type ParentNavKey,
  type RouteNavKey,
} from '../../navigation/config'

const route = useRoute()
const router = useRouter()

const currentKey = computed(() => route.meta.legacyKey as RouteNavKey | undefined)
const collapsedGroups = reactive<Record<ParentNavKey, boolean>>({
  'workbench-home': true,
  'content-creation': false,
  'content-production': true,
  'matrix-distribution': true,
  'brand-ip-strategy': true,
})

watch(
  currentKey,
  (key) => {
    for (const parentKey of Object.keys(childRouteKeysByParent) as ParentNavKey[]) {
      if (isParentNavKeyActive(parentKey, key)) {
        collapsedGroups[parentKey] = false
      }
    }
  },
  { immediate: true },
)

function toggleGroup(key: ParentNavKey) {
  collapsedGroups[key] = !collapsedGroups[key]
}

function isCollapsed(key: ParentNavKey) {
  return collapsedGroups[key]
}

function goToRoute(key: RouteNavKey) {
  router.push(routeLocationByKey[key])
}
</script>
