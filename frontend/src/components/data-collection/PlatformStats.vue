<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
    <div class="bg-white rounded-xl p-5 border border-slate-200 shadow-card hover:shadow-card-hover transition-all relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
        <span class="material-symbols-outlined text-5xl text-primary">apps</span>
      </div>
      <p class="text-slate-500 text-sm font-medium mb-1">接入平台数</p>
      <div class="flex items-baseline gap-2 mb-2">
        <h3 class="text-3xl font-bold text-slate-800 font-display tracking-tight">{{ stats.platformCount || 0 }}</h3>
      </div>
      <p class="text-xs text-slate-400">目前支持解析的平台总线</p>
    </div>

    <div class="bg-white rounded-xl p-5 border border-slate-200 shadow-card hover:shadow-card-hover transition-all relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
        <span class="material-symbols-outlined text-5xl text-cyan-500">cloud_download</span>
      </div>
      <p class="text-slate-500 text-sm font-medium mb-1">今日抓取总数</p>
      <div class="flex items-baseline gap-2 mb-2">
        <h3 class="text-3xl font-bold text-slate-800 font-display tracking-tight">{{ stats.todayFetched || 0 }}</h3>
        <span class="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 px-1.5 py-0.5 rounded flex items-center">
          <span class="material-symbols-outlined text-[12px] mr-1">trending_up</span> 12.5%
        </span>
      </div>
      <p class="text-xs text-slate-400">所有平台抓取的数据条数</p>
    </div>

    <div class="bg-white rounded-xl p-5 border border-slate-200 shadow-card hover:shadow-card-hover transition-all relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
        <span class="material-symbols-outlined text-5xl text-violet-500">update</span>
      </div>
      <p class="text-slate-500 text-sm font-medium mb-1">热榜更新次数</p>
      <div class="flex items-baseline gap-2 mb-2">
        <h3 class="text-3xl font-bold text-slate-800 font-display tracking-tight">{{ stats.hotRankUpdates || 0 }}</h3>
      </div>
      <p class="text-xs text-slate-400">累计自动定时刷新次数</p>
    </div>

    <div class="bg-white rounded-xl p-5 border border-slate-200 shadow-card hover:shadow-card-hover transition-all relative overflow-hidden group">
      <div class="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
        <span class="material-symbols-outlined text-5xl text-emerald-500">task_alt</span>
      </div>
      <p class="text-slate-500 text-sm font-medium mb-1">采集任务数</p>
      <div class="flex items-baseline gap-2 mb-2">
        <h3 class="text-3xl font-bold text-slate-800 font-display tracking-tight">{{ stats.keywordTasks || 0 }}</h3>
        <span class="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 px-1.5 py-0.5 rounded flex items-center">
          进行中 {{ stats.keywordTasksActive || 0 }}
        </span>
      </div>
      <p class="text-xs text-slate-400">目前设定的主动采集任务</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  stats: {
    platformCount?: number
    todayFetched?: number
    hotRankUpdates?: number
    keywordTasks?: number
    keywordTasksActive?: number
  }
}>()
</script>
