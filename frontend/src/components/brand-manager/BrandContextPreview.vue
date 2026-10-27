<template>
  <div class="bg-slate-800 rounded-xl shadow-sm border border-slate-700 overflow-hidden flex flex-col h-full font-mono text-xs">
    <div class="px-5 py-3 border-b border-slate-700 bg-slate-900 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full bg-red-500"></span>
        <span class="w-3 h-3 rounded-full bg-yellow-500"></span>
        <span class="w-3 h-3 rounded-full bg-green-500"></span>
        <span class="font-bold text-slate-300 ml-2 font-sans text-sm">品牌上下文载荷预览</span>
      </div>
      <span class="text-[10px] text-green-400 bg-green-400/10 px-2 py-0.5 rounded">实时装配中...</span>
    </div>

    <!-- Payload Abstract View -->
    <div class="p-5 overflow-y-auto flex-1 custom-scrollbar text-slate-300 space-y-4">
      
      <div>
        <span class="text-blue-400">"brandName"</span>: <span class="text-green-300">"{{ payload.brandProfile.brandName || '未命名' }}"</span>,
      </div>

      <div>
        <span class="text-blue-400">"targetAudience"</span>: <span class="text-green-300">"{{ payload.brandProfile.targetAudience }}"</span>,
      </div>
      
      <div>
        <span class="text-blue-400">"forbiddenRules"</span>: [
        <div class="pl-4">
           <div v-for="(rule, idx) in payload.forbiddenPhrases" :key="idx">
             <span class="text-orange-300">"{{ rule }}"</span><span v-if="idx !== payload.forbiddenPhrases.length - 1">,</span>
           </div>
           <div class="text-slate-500 italic" v-if="!payload.forbiddenPhrases.length">// 无敏感词限制</div>
        </div>
        ],
      </div>

      <div>
        <span class="text-blue-400">"requiredSellingPoints"</span>: [
        <div class="pl-4">
           <div v-for="rp in requiredPoints" :key="rp.id" class="flex gap-2">
             <span class="text-slate-500">{</span>
             <span class="text-blue-400 min-w-16">title:</span>
             <span class="text-green-300 truncate max-w-[120px]">"{{ rp.title }}"</span>,
             <span class="text-blue-400">W:</span>
             <span class="text-purple-300">{{ rp.weight }}</span>
             <span class="text-slate-500">}</span><span v-if="rp !== requiredPoints[requiredPoints.length-1]">,</span>
           </div>
           <div class="text-slate-500 italic" v-if="!requiredPoints.length">// 未配置必打卖点</div>
        </div>
        ],
      </div>
      
      <div>
        <span class="text-blue-400">"visualAssetsAllocated"</span>: <span class="text-purple-300">{{ payload.selectedAssets.length }}</span> <span class="text-slate-500">items</span>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { BrandContextPayload } from '../../types/brandInjection'

const props = defineProps<{
  payload: BrandContextPayload
}>()

const requiredPoints = computed(() => props.payload.requiredSellingPoints)
</script>
