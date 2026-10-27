<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full">
    <div class="px-5 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between shrink-0">
      <div>
        <h2 class="font-bold text-slate-800 flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-[20px]">psychiatry</span>
          智能卖点提取与审计
        </h2>
        <p class="text-xs text-slate-500 mt-1">从左侧基础参数提炼营销爆点，并分发至生成流水线。</p>
      </div>
      <div class="flex gap-2">
        <button 
          @click="addManualPoint"
          class="px-3 py-1.5 bg-white border border-slate-200 text-slate-600 hover:text-primary hover:border-primary/50 text-xs font-bold rounded-lg shadow-sm transition-all flex items-center gap-1"
        >
          <span class="material-symbols-outlined text-[16px]">add_circle</span>
          新增手工卖点
        </button>
        <button 
          @click="$emit('extract')"
          :disabled="extracting"
          class="px-3 py-1.5 border border-primary text-primary hover:bg-primary hover:text-white disabled:bg-primary/20 disabled:text-white disabled:border-transparent text-xs font-bold rounded-lg shadow-sm transition-all flex items-center gap-1"
        >
          <span v-if="extracting" class="material-symbols-outlined text-[16px] animate-spin">refresh</span>
          <span v-else class="material-symbols-outlined text-[16px]">auto_awesome</span>
          AI 提炼卖点
        </button>
      </div>
    </div>

    <!-- Feishu Widget Slot -->
    <div class="px-5 pt-4 shrink-0">
      <slot name="feishu-widget"></slot>
    </div>

    <!-- Selling Points List -->
    <div class="p-5 overflow-y-auto flex-1 custom-scrollbar space-y-4 pt-1">
      <div 
        v-for="(point, idx) in internalPoints" 
        :key="point.id"
        class="border border-slate-200 rounded-xl p-4 bg-white hover:border-primary/30 transition-colors group relative"
      >
        <!-- Header: Title and Type -->
        <div class="flex items-start justify-between mb-2">
          <input 
            v-model="point.title"
            class="font-bold text-sm text-slate-800 bg-transparent border-none focus:ring-0 p-0 w-2/3"
            placeholder="卖点标题..."
          />
          <div class="flex items-center gap-2">
            <span v-if="point.status === 'confirmed'" class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded flex items-center gap-1"><span class="material-symbols-outlined text-[12px]">check_circle</span>已确认</span>
            <span v-else-if="point.status === 'rejected'" class="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded flex items-center gap-1"><span class="material-symbols-outlined text-[12px]">cancel</span>已退回</span>
            <span v-else-if="point.status === 'pending_confirm'" class="text-[10px] font-bold text-orange-600 bg-orange-50 px-2 py-0.5 rounded flex items-center gap-1"><span class="material-symbols-outlined text-[12px]">schedule</span>待确认</span>

            <select 
              v-model="point.type"
              class="text-xs font-bold border-none bg-slate-100 rounded px-2 py-1 pr-6 cursor-pointer outline-none focus:ring-2 focus:ring-primary/30"
              :class="{
                'text-primary': point.type === 'required',
                'text-slate-600': point.type === 'optional',
                'text-red-600': point.type === 'forbidden'
              }"
            >
              <option value="required">🎯 必打卖点</option>
              <option value="optional">✨ 可选卖点</option>
              <option value="forbidden">🚫 禁用表达</option>
            </select>
          </div>
        </div>

        <!-- Description -->
        <textarea 
          v-model="point.description"
          class="w-full text-xs text-slate-500 bg-slate-50 border border-transparent hover:border-slate-200 focus:border-primary rounded-lg p-2.5 outline-none resize-none transition-colors"
          rows="2"
          placeholder="详细描述该卖点在营销时的展开话术..."
        ></textarea>

        <!-- Footer Meta (Weight, Platform) -->
        <div class="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2" title="注入大模型提示词时的注意力权重">
              <span class="text-[10px] font-bold text-slate-400">权重</span>
              <input type="range" v-model.number="point.weight" min="1" max="10" class="w-20 h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary">
              <span class="text-[10px] font-mono text-primary font-bold">{{ point.weight }}</span>
            </div>
            
            <div class="flex items-center gap-1.5 opacity-60 hover:opacity-100 transition-opacity">
              <span class="text-[10px] font-bold text-slate-400">平台过滤</span>
              <div class="flex gap-1">
                <label v-for="p in ['douyin', 'xiaohongshu', 'weibo']" :key="p" class="cursor-pointer">
                  <input type="checkbox" :value="p" v-model="point.platforms" class="peer sr-only">
                  <div class="w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold text-slate-400 bg-slate-100 peer-checked:bg-primary/10 peer-checked:text-primary transition-colors">
                    {{ p === 'douyin' ? '抖' : p === 'xiaohongshu' ? '红' : '微' }}
                  </div>
                </label>
              </div>
            </div>
          </div>

          <button @click="removePoint(idx)" class="w-6 h-6 rounded-md hover:bg-red-50 text-slate-300 hover:text-red-500 flex items-center justify-center transition-colors">
            <span class="material-symbols-outlined text-[16px]">delete</span>
          </button>
        </div>
      </div>
      
      <div v-if="internalPoints.length === 0" class="py-12 flex flex-col items-center justify-center text-slate-400">
        <span class="material-symbols-outlined text-4xl mb-2 opacity-50">data_object</span>
        <p class="text-sm">暂无卖点</p>
        <p class="text-xs mt-1">点击"AI 提炼卖点"自动生成，或手动添加</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { SellingPointItem } from '../../types/brandInjection'

const props = defineProps<{
  modelValue: SellingPointItem[]
  extracting: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: SellingPointItem[]): void
  (e: 'extract'): void
}>()

const internalPoints = ref<SellingPointItem[]>(JSON.parse(JSON.stringify(props.modelValue)))

// Basic prop sync
watch(() => props.modelValue, (newVal) => {
  if (JSON.stringify(newVal) !== JSON.stringify(internalPoints.value)) {
    internalPoints.value = JSON.parse(JSON.stringify(newVal))
  }
}, { deep: true })

watch(internalPoints, (newVal) => {
  emit('update:modelValue', JSON.parse(JSON.stringify(newVal)))
}, { deep: true })

function removePoint(idx: number) {
  internalPoints.value.splice(idx, 1)
}

function addManualPoint() {
  internalPoints.value.unshift({
    id: `manual_${Date.now()}`,
    title: '',
    description: '',
    type: 'optional',
    weight: 5,
    source: 'manual',
    status: 'draft',
    platforms: ['douyin'],
    scenarios: []
  })
}
</script>
