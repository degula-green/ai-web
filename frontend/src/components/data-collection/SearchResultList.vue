<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div v-for="i in 8" :key="i" class="bg-white rounded-xl border border-slate-200 overflow-hidden animate-pulse flex flex-col h-[320px]">
        <div class="h-40 bg-slate-200 w-full shrink-0"></div>
        <div class="p-4 flex-1 flex flex-col">
          <div class="h-5 bg-slate-200 rounded w-full mb-2"></div>
          <div class="h-5 bg-slate-200 rounded w-2/3 mb-4"></div>
          <div class="mt-auto flex justify-between">
            <div class="w-16 h-4 bg-slate-200 rounded"></div>
            <div class="w-12 h-4 bg-slate-200 rounded"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!data || data.length === 0" class="bg-white rounded-xl border border-slate-200 py-20 px-6 text-center shadow-sm">
      <div class="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-100">
        <span class="material-symbols-outlined text-4xl text-slate-300">manage_search</span>
      </div>
      <h3 class="text-base font-bold text-slate-700 mb-1">无搜索结果</h3>
      <p class="text-sm text-slate-500 max-w-sm mx-auto">未找到与关键词匹配的内容，请尝试更换关键词或放宽时间范围。</p>
    </div>

    <!-- List State -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      <div
        v-for="item in data"
        :key="item.id"
        class="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-card-hover hover:border-primary/30 transition-all flex flex-col overflow-hidden group cursor-pointer relative"
        :class="{ 'ring-2 ring-primary border-transparent': selectedIds?.includes(item.id) }"
        @click="$emit('view-detail', item)"
      >
        <!-- Selection Checkbox -->
        <div
          v-if="stagingMode && !isSaved(item.id)"
          class="absolute top-0 right-0 z-20 p-3"
          @click.stop="toggleSelection(item.id)"
        >
          <div
            class="w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all shadow-sm"
            :class="selectedIds?.includes(String(item.id))
              ? 'bg-primary border-primary text-white scale-110'
              : 'bg-white/90 backdrop-blur-sm border-slate-300 text-transparent hover:border-primary hover:bg-white'"
          >
            <span class="material-symbols-outlined text-[18px] font-black pointer-events-none">check</span>
          </div>
        </div>

        <div class="h-40 bg-slate-100 relative overflow-hidden shrink-0">
          <img v-if="item.cover" :src="item.cover" :alt="item.title" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy" />
          <div v-else class="w-full h-full flex items-center justify-center text-slate-300">
            <span class="material-symbols-outlined text-4xl">image</span>
          </div>
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
          <div class="absolute top-3 left-3 flex items-center gap-2">
            <span class="bg-white/90 text-slate-700 text-[10px] font-bold px-2 py-1 rounded backdrop-blur-sm shadow-sm flex items-center gap-1 border border-slate-200">
              <span class="material-symbols-outlined text-[12px]">{{ item.contentKind === 'video' ? 'movie' : 'image' }}</span>
              {{ item.contentKind === 'video' ? '视频' : '图文' }}
            </span>
          </div>
          <div class="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white text-xs drop-shadow-md">
            <div class="flex gap-2">
              <span class="font-medium flex items-center gap-0.5"><span class="material-symbols-outlined text-[14px]">favorite</span> {{ formatNumber(item.likes || 0) }}</span>
              <span class="font-medium flex items-center gap-0.5"><span class="material-symbols-outlined text-[14px]">star</span> {{ formatNumber(item.collects || 0) }}</span>
            </div>
            <span>{{ item.publishTime }}</span>
          </div>
        </div>
        
        <div class="p-4 flex flex-col">
          <h3
            class="font-bold text-slate-800 text-sm line-clamp-2 group-hover:text-primary transition-colors leading-snug"
            :class="cardSummary(item) ? 'mb-2' : 'mb-1'"
            :title="item.title"
          >
            {{ item.title }}
          </h3>
          <p v-if="cardSummary(item)" class="text-xs text-slate-500 line-clamp-2 mb-3 leading-relaxed">
            {{ cardSummary(item) }}
          </p>
          
          <div class="mt-3 flex items-center justify-between border-t border-slate-100 pt-2.5">
            <div class="flex items-center gap-2">
              <div class="w-5 h-5 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-bold text-slate-500 shrink-0">
                {{ item.author.charAt(0) }}
              </div>
              <span class="text-xs text-slate-600 font-medium truncate max-w-[100px]">{{ item.author }}</span>
            </div>
            <button 
              v-if="stagingMode"
              @click.stop="$emit('save', item)"
              :disabled="isSaved(item.id) || savingIds?.includes(item.id)"
              class="px-2 py-1 rounded text-[11px] font-semibold transition-colors flex items-center gap-1"
              :class="isSaved(item.id) ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : (savingIds?.includes(item.id) ? 'bg-primary/5 text-primary/60 cursor-wait' : 'text-primary bg-primary/10 hover:bg-primary hover:text-white')"
            >
              <template v-if="savingIds?.includes(item.id)">
                <span class="w-3 h-3 border-2 border-primary/30 border-t-primary rounded-full animate-spin"></span>
                入库中...
              </template>
              <template v-else>
                {{ isSaved(item.id) ? '已保留' : '保留入库' }}
              </template>
            </button>
            <button 
              v-else
              class="text-primary bg-primary/10 hover:bg-primary hover:text-white px-2 py-1 rounded text-[11px] font-semibold transition-colors"
            >
              解析
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SearchResultItem } from '../../types/dataCollection'

const props = defineProps<{
  data: SearchResultItem[]
  loading: boolean
  stagingMode?: boolean
  savedIds?: string[]
  savingIds?: string[] // 正在入库的 ID 列表
  selectedIds?: string[] // 当前选中的 ID 列表
}>()

const emits = defineEmits<{
  (e: 'view-detail', item: SearchResultItem): void
  (e: 'save', item: SearchResultItem): void
  (e: 'update:selectedIds', ids: string[]): void
}>()

function isSaved(id: string) {
  return props.savedIds?.includes(id)
}

function toggleSelection(id: string | number) {
  const targetId = String(id)
  const current = [...(props.selectedIds || [])]
  const idx = current.indexOf(targetId)
  if (idx === -1) {
    current.push(targetId)
  } else {
    current.splice(idx, 1)
  }
  emits('update:selectedIds', current)
}

function cardSummary(item: SearchResultItem) {
  const title = String(item.title || '').trim()
  const summary = String(item.summary || '').trim()
  if (!summary) return ''

  const normalizedTitle = normalizeContentText(title)
  const normalizedSummary = normalizeContentText(summary)
  if (!normalizedSummary || normalizedSummary === normalizedTitle) return ''
  if (normalizedTitle && normalizedSummary.startsWith(normalizedTitle)) {
    const rest = summary.slice(title.length).trim()
    return rest && normalizeContentText(rest) !== normalizedTitle ? rest : ''
  }
  return summary
}

function normalizeContentText(value: string) {
  return value.replace(/\s+/g, '').replace(/[，。,.!！?？#]/g, '').toLowerCase()
}

function formatNumber(num?: number) {
  if (num === undefined || num === null) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}
</script>
