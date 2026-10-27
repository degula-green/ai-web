<template>
  <div 
    class="bg-white rounded-xl border border-slate-200 shadow-card hover:shadow-card-hover hover:border-primary/30 transition-all cursor-pointer flex flex-col group overflow-hidden"
    @click="$emit('click', platform.platformCode)"
  >
    <div class="p-5 flex items-start justify-between border-b border-slate-100">
      <div class="flex items-center gap-3">
        <div 
          class="w-12 h-12 rounded-xl flex items-center justify-center shadow-sm"
          :class="platform.themeColor || 'bg-primary/10 text-primary border border-primary/20'"
        >
          <span class="material-symbols-outlined text-[24px]">{{ platform.icon }}</span>
        </div>
        <div>
          <h3 class="text-base font-bold text-slate-800 font-display flex items-center gap-2">
            {{ platform.platformName }}
            <span v-if="platform.status === 'collecting'" class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span v-else-if="platform.status === 'error'" class="w-2 h-2 rounded-full bg-red-500"></span>
            <span v-else class="w-2 h-2 rounded-full bg-slate-300"></span>
          </h3>
          <p class="text-xs text-slate-400 mt-0.5">更新于 {{ platform.latestUpdateTime }}</p>
        </div>
      </div>
      
      <div class="text-[10px] font-bold px-2 py-1 rounded-full whitespace-nowrap"
        :class="{
          'bg-emerald-50 text-emerald-600': platform.status === 'normal',
          'bg-blue-50 text-primary animate-pulse': platform.status === 'collecting',
          'bg-red-50 text-red-500': platform.status === 'error'
        }">
        {{ statusText }}
      </div>
    </div>
    
    <div class="p-5 flex-1 flex flex-col gap-4">
      <div class="grid grid-cols-2 gap-3 flex-1">
        <div class="bg-slate-50 rounded-lg p-3 text-center border border-slate-100 group-hover:bg-primary/5 transition-colors">
          <p class="text-xs text-slate-500 mb-1">热榜数据</p>
          <p class="text-lg font-bold text-slate-800 font-display">{{ platform.hotRankCount || 0 }}<span class="text-xs text-slate-400 font-normal ml-0.5">条</span></p>
        </div>
        <div class="bg-slate-50 rounded-lg p-3 text-center border border-slate-100 group-hover:bg-primary/5 transition-colors">
          <p class="text-xs text-slate-500 mb-1">采集任务</p>
          <p class="text-lg font-bold text-slate-800 font-display">{{ platform.keywordTaskCount || 0 }}<span class="text-xs text-slate-400 font-normal ml-0.5">个</span></p>
        </div>
      </div>
      
      <button class="w-full py-2.5 bg-slate-50 hover:bg-primary hover:text-white text-primary border border-slate-200 hover:border-primary text-sm font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-sm">
        <span class="material-symbols-outlined text-[18px]">travel_explore</span>
        进入采集明细
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PlatformSummary } from '../../types/dataCollection'

const props = defineProps<{
  platform: PlatformSummary
}>()

defineEmits<{
  (e: 'click', code: string): void
}>()

const statusText = computed(() => {
  switch (props.platform.status) {
    case 'normal': return '连接正常'
    case 'collecting': return '采集中'
    case 'error': return '接口异常'
    default: return '未知'
  }
})
</script>
