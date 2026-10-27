<template>
  <div class="h-full bg-slate-50 overflow-y-auto p-6 flex flex-col gap-6 font-sans text-slate-800">
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 font-display flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-[28px]">travel_explore</span>
          数据采集
        </h1>
        <p class="text-slate-500 text-sm mt-1">统一管理平台热榜和关键词采集任务。</p>
      </div>
      <button
        @click="fetchData"
        class="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all shadow-sm flex items-center gap-2"
      >
        <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': loading }">refresh</span>
        刷新数据
      </button>
    </div>

    <PlatformStats :stats="stats" />

    <div>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-bold text-slate-800 font-display flex items-center gap-2">
          <span class="material-symbols-outlined text-slate-400">category</span>
          平台采集大厅
        </h2>
      </div>

      <div class="flex items-center justify-center p-12" v-if="loading && platforms.length === 0">
        <div class="w-8 h-8 border-4 border-slate-200 border-t-primary rounded-full animate-spin"></div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        <PlatformCard
          v-for="platform in platforms"
          :key="platform.platformCode"
          :platform="platform"
          @click="goToPlatformDetail"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getOverview } from '../../api/dataCollection'
import PlatformCard from '../../components/data-collection/PlatformCard.vue'
import PlatformStats from '../../components/data-collection/PlatformStats.vue'
import type { PlatformSummary } from '../../types/dataCollection'

const router = useRouter()
const loading = ref(false)
const platforms = ref<PlatformSummary[]>([])
const stats = ref({
  platformCount: 0,
  todayFetched: 0,
  hotRankUpdates: 0,
  keywordTasks: 0,
  keywordTasksActive: 0,
})

async function fetchData() {
  loading.value = true
  try {
    const overview = await getOverview()
    platforms.value = overview.platforms
    stats.value = {
      platformCount: overview.stats.platformCount,
      todayFetched: overview.stats.todayFetched,
      hotRankUpdates: overview.stats.hotRankUpdates,
      keywordTasks: overview.stats.keywordTaskCount,
      keywordTasksActive: overview.stats.keywordTaskActive,
    }
  } catch (error) {
    console.error('Failed to fetch platforms', error)
  } finally {
    loading.value = false
  }
}

function goToPlatformDetail(platformCode: string) {
  router.push({
    path: '/data-collection/platform',
    query: { code: platformCode },
  })
}

onMounted(async () => {
  await fetchData()
})
</script>
