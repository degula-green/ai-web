<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full">
    <div class="px-5 py-4 border-b border-slate-100 bg-slate-50 shrink-0">
      <h2 class="font-bold text-slate-800 flex items-center gap-2">
        <span class="material-symbols-outlined text-primary text-[20px]">storefront</span>
        品牌基础信息区
      </h2>
      <p class="text-xs text-slate-500 mt-1">请填写并确认将作为后续生成指令约束的品牌基调参数。</p>
    </div>

    <!-- Forms Area -->
    <div class="p-5 overflow-y-auto flex-1 custom-scrollbar space-y-5">
      <!-- 品牌/产品基本信息 -->
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1.5 focus-within:text-primary transition-colors">品牌名称</label>
          <input 
            v-model="internalProfile.brandName"
            type="text" 
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm transition-all"
            placeholder="如：智创网络"
          >
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1.5 focus-within:text-primary transition-colors">产品名称</label>
          <input 
            v-model="internalProfile.productName"
            type="text" 
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm transition-all"
            placeholder="如：智创内容自动化系统 v3"
          >
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1.5 focus-within:text-primary transition-colors">产品定位</label>
          <textarea 
            v-model="internalProfile.positioning"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm transition-all resize-none h-20"
            placeholder="描述这款产品在市场中的定位..."
          ></textarea>
        </div>
      </div>

      <hr class="border-slate-100">

      <!-- 细分人群场景 -->
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1.5 focus-within:text-primary transition-colors">目标人群 (Target Audience)</label>
          <textarea 
            v-model="internalProfile.targetAudience"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm transition-all resize-none h-16"
            placeholder="主要销售或推广给哪些群体？"
          ></textarea>
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1.5 focus-within:text-primary transition-colors">适用场景 (Scenarios)</label>
          <textarea 
            v-model="internalProfile.scenarios"
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm transition-all resize-none h-16"
            placeholder="如：日常通勤、办公室办公、节日送礼等"
          ></textarea>
        </div>
      </div>

      <hr class="border-slate-100">

      <!-- 品牌核心指令 -->
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1.5 focus-within:text-primary transition-colors">整体调性 (Tone & Voice)</label>
          <input 
            v-model="internalProfile.tone"
            type="text" 
            class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm transition-all"
            placeholder="如：专业、活泼、充满科技感"
          >
        </div>
        <div>
          <label class="block text-xs font-bold text-red-600 mb-1.5">禁用表达 / 风险词 (Forbidden)</label>
          <div class="flex gap-2 mb-2">
            <input 
              v-model="newForbiddenWord"
              @keyup.enter="addForbidden"
              type="text" 
              class="flex-1 px-3 py-1.5 bg-red-50 border border-red-200 rounded-lg focus:outline-none focus:border-red-400 focus:ring-1 focus:ring-red-400 text-sm transition-all placeholder:text-red-300 text-red-800"
              placeholder="添加禁用词语并回车"
            >
            <button 
              @click="addForbidden"
              class="px-3 py-1.5 bg-red-100 text-red-600 hover:bg-red-200 hover:text-red-700 font-bold rounded-lg text-xs transition-colors shrink-0"
            >
              添加
            </button>
          </div>
          <div class="flex flex-wrap gap-2">
            <span v-for="(word, idx) in internalProfile.forbiddenPhrases" :key="idx" class="px-2.5 py-1 bg-red-100 border border-red-200 text-red-700 text-xs font-medium rounded flex items-center gap-1 group">
              {{ word }}
              <button @click="removeForbidden(idx)" class="w-4 h-4 rounded-full hover:bg-red-200 flex items-center justify-center text-red-500 opacity-60 group-hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined text-[12px]">close</span>
              </button>
            </span>
          </div>
          <p class="text-[10px] text-slate-400 mt-2 flex items-center gap-1">
            <span class="material-symbols-outlined text-[14px]">info</span>
            AI在撰写内容时将被明确指令避开以上表达。
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { BrandProfile } from '../../types/brandInjection'

const props = defineProps<{
  modelValue: BrandProfile
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: BrandProfile): void
}>()

// Deep clone to avoid mutating prop directly from v-model before manual sync (or just let it sync via deep watch)
const internalProfile = ref<BrandProfile>(JSON.parse(JSON.stringify(props.modelValue)))

watch(() => props.modelValue, (newVal) => {
  // Only override if brandId changes to prevent overriding typing
  if (newVal.brandId !== internalProfile.value.brandId) {
    internalProfile.value = JSON.parse(JSON.stringify(newVal))
  }
}, { deep: true })

// Sync out
watch(internalProfile, (newVal) => {
  emit('update:modelValue', JSON.parse(JSON.stringify(newVal)))
}, { deep: true })

const newForbiddenWord = ref('')

function addForbidden() {
  const w = newForbiddenWord.value.trim()
  if (w && !internalProfile.value.forbiddenPhrases.includes(w)) {
    internalProfile.value.forbiddenPhrases.push(w)
  }
  newForbiddenWord.value = ''
}

function removeForbidden(idx: number) {
  internalProfile.value.forbiddenPhrases.splice(idx, 1)
}
</script>
