<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm text-slate-600">
        <thead class="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
          <tr>
            <th class="px-6 py-4 w-16 text-center">排名</th>
            <th class="px-6 py-4">内容信息</th>
            <th class="px-6 py-4 w-32">作者</th>
            <th class="px-6 py-4 w-48">互动数据</th>
            <th class="px-6 py-4 w-32 text-right">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <!-- Loading State (Skeleton) -->
          <template v-if="loading">
            <tr v-for="i in 5" :key="i" class="animate-pulse">
              <td class="px-6 py-4 text-center">
                <div class="w-6 h-6 bg-slate-200 rounded-md mx-auto"></div>
              </td>
              <td class="px-6 py-4">
                <div class="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
                <div class="h-3 bg-slate-200 rounded w-1/2 mb-2"></div>
                <div class="flex gap-2">
                  <div class="w-12 h-4 bg-slate-200 rounded"></div>
                  <div class="w-12 h-4 bg-slate-200 rounded"></div>
                </div>
              </td>
              <td class="px-6 py-4"><div class="h-4 bg-slate-200 rounded w-20"></div></td>
              <td class="px-6 py-4">
                <div class="grid grid-cols-2 gap-2">
                  <div class="h-3 bg-slate-200 rounded"></div>
                  <div class="h-3 bg-slate-200 rounded"></div>
                </div>
              </td>
              <td class="px-6 py-4 text-right"><div class="h-8 bg-slate-200 rounded w-16 ml-auto"></div></td>
            </tr>
          </template>

          <!-- Empty State -->
          <tr v-else-if="!data || data.length === 0">
            <td colspan="5" class="px-6 py-16 text-center text-slate-500">
              <span class="material-symbols-outlined text-4xl text-slate-300 mb-2">search_off</span>
              <p>暂无热榜数据</p>
            </td>
          </tr>

          <!-- Data Rows -->
          <tr v-else v-for="item in data" :key="item.id" class="hover:bg-slate-50/50 transition-colors group">
            <td class="px-6 py-4 text-center">
              <div class="font-display font-bold text-lg"
                :class="{
                  'text-red-500': item.rank === 1,
                  'text-orange-500': item.rank === 2,
                  'text-amber-500': item.rank === 3,
                  'text-slate-400': item.rank > 3
                }">
                {{ item.rank }}
              </div>
            </td>
            <td class="px-6 py-4">
              <a href="#" @click.prevent="$emit('view-detail', item)" class="font-bold text-slate-800 hover:text-primary transition-colors text-base line-clamp-1 mb-1">
                {{ item.title }}
              </a>
              <p class="text-xs text-slate-500 line-clamp-1 mb-2">{{ item.summary }}</p>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="tag in item.tags" :key="tag" class="px-2 py-0.5 bg-slate-100 text-slate-500 text-[10px] rounded border border-slate-200">
                  #{{ tag }}
                </span>
              </div>
            </td>
            <td class="px-6 py-4">
              <div class="text-sm font-semibold text-slate-700">{{ item.author }}</div>
              <div class="text-[11px] text-slate-400 mt-0.5">{{ item.publishTime }}</div>
            </td>
            <td class="px-6 py-4">
              <div class="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-slate-500">
                <template v-if="item.hotValue">
                  <div class="flex items-center gap-1 col-span-2 text-red-500 font-medium"><span class="material-symbols-outlined text-[13px]">local_fire_department</span> 热度 {{ formatNumber(item.hotValue) }}</div>
                </template>
                <template v-else>
                  <div class="flex items-center gap-1"><span class="material-symbols-outlined text-[13px]">favorite</span> {{ formatNumber(item.likes || 0) }}</div>
                  <div class="flex items-center gap-1"><span class="material-symbols-outlined text-[13px]">chat_bubble</span> {{ formatNumber(item.comments || 0) }}</div>
                  <div class="flex items-center gap-1"><span class="material-symbols-outlined text-[13px]">share</span> {{ formatNumber(item.shares || 0) }}</div>
                  <div class="flex items-center gap-1"><span class="material-symbols-outlined text-[13px]">visibility</span> {{ formatNumber(item.views || 0) }}</div>
                </template>
              </div>
            </td>
            <td class="px-6 py-4 text-right whitespace-nowrap">
              <button 
                @click="$emit('view-detail', item)"
                class="px-3 py-1.5 bg-white border border-slate-200 text-slate-600 hover:text-primary hover:border-primary/50 text-xs font-medium rounded shadow-sm transition-all"
              >
                详情
              </button>
              <button class="px-3 py-1.5 ml-2 bg-primary/10 text-primary hover:bg-primary hover:text-white border border-transparent text-xs font-medium rounded shadow-sm transition-all">
                仿写
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { HotRankItem } from '../../types/dataCollection'

defineProps<{
  data: HotRankItem[]
  loading: boolean
}>()

defineEmits<{
  (e: 'view-detail', item: HotRankItem): void
}>()

function formatNumber(num?: number) {
  if (num === undefined || num === null) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}
</script>
