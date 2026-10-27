<template>
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-6 overflow-y-auto">
    <div 
      class="bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col transform transition-all outline-none my-auto"
      :class="step === 'fill_form' ? 'w-[800px]' : 'w-[600px]'"
    >
      
      <!-- Header -->
      <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-white shrink-0">
        <h3 class="font-bold text-slate-800 flex items-center gap-2">
          <span class="material-symbols-outlined text-primary">add_circle</span>
          新建产品线档案
        </h3>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1.5 rounded-full transition-colors flex items-center justify-center">
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>
      
      <!-- Mode Selection -->
      <div v-if="step === 'select_mode'" class="p-8 space-y-4">
        <p class="text-sm text-slate-600 font-medium mb-4 text-center">请选择构建产品初期档案的方式</p>
        
        <div class="grid grid-cols-2 gap-5">
          <button 
            @click="selectMode('manual')"
            class="group p-6 border border-slate-200 hover:border-slate-800 hover:shadow-lg rounded-2xl text-left transition-all relative overflow-hidden bg-white"
          >
            <div class="w-12 h-12 bg-slate-50 group-hover:bg-slate-100 rounded-full flex items-center justify-center mb-5 transition-colors">
              <span class="material-symbols-outlined text-slate-600 group-hover:text-slate-900">edit_document</span>
            </div>
            <h4 class="font-bold text-slate-800 text-lg mb-2">手动创建</h4>
            <p class="text-[13px] text-slate-500 leading-relaxed">提供一份完整的空白表单供您录入。参数越详细，后续模型生成的匹配度越高。</p>
          </button>
          
          <button 
            @click="selectMode('auto')"
            class="group p-6 border-2 border-transparent hover:border-primary/20 rounded-2xl text-left transition-all shadow-md hover:shadow-xl relative overflow-hidden bg-gradient-to-br from-blue-50 to-indigo-50/50"
          >
            <div class="absolute -right-4 -top-4 w-24 h-24 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-colors"></div>
            <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center mb-5 transition-transform group-hover:scale-110 shadow-sm">
              <span class="material-symbols-outlined text-primary">travel_explore</span>
            </div>
            <div class="flex items-center gap-2 mb-2">
              <h4 class="font-bold text-slate-800 text-lg">AI 联网生成</h4>
              <span class="text-[10px] bg-gradient-to-r from-red-500 to-orange-500 text-white px-2 py-0.5 rounded-full font-bold shadow-sm">推荐</span>
            </div>
            <p class="text-[13px] text-slate-600 leading-relaxed">提供产品名称或大致描述，AI 将自主联网搜索并总结相关营销资料。</p>
          </button>
        </div>
      </div>
      
      <!-- Auto Search Input -->
      <div v-if="step === 'auto_input'" class="p-8">
        <label class="block text-sm font-bold text-slate-700 mb-3">产品名称 / 搜索意图关键字</label>
        <div class="relative mb-5">
          <input 
            v-model="searchQuery" 
            @keyup.enter="startScraping"
            type="text" 
            class="w-full bg-white border-2 border-slate-200 rounded-2xl pl-12 pr-4 py-4 text-sm focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all font-sans shadow-sm"
            placeholder="例如: 某某牌 2024最新款纯电车 / 最新款极简风大衣..."
            :disabled="scanning"
          >
          <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[22px] text-slate-400">psychiatry</span>
        </div>
        
        <div class="bg-indigo-50/50 border border-indigo-100 rounded-xl p-4 mb-8 flex gap-3 text-indigo-800 text-sm">
           <span class="material-symbols-outlined text-indigo-500 shrink-0">tips_and_updates</span>
           <p class="leading-relaxed">提供品名或宽泛描述后，大语言模型将联网检索该产品最新的知识百科、新闻报道与舆情，为您自动交叉总结受众群体与核心卖点矩阵。</p>
        </div>
        
        <!-- Status Tracker during Scan -->
        <div v-if="scanning" class="bg-white border-2 border-primary/20 rounded-2xl p-6 mb-4 relative overflow-hidden">
           <div class="absolute inset-0 bg-primary/5 animate-pulse"></div>
           <div class="relative flex items-center gap-4 mb-5">
             <div class="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center text-primary shrink-0 relative">
               <span class="material-symbols-outlined animate-spin text-[20px]">donut_large</span>
               <div class="absolute inset-0 border border-primary/30 rounded-full animate-ping"></div>
             </div>
             <div>
               <div class="font-bold text-base text-slate-800 mb-1">正在重构品牌知识图谱...</div>
               <div class="text-[11px] text-primary font-mono bg-primary/10 px-2 py-0.5 rounded-md inline-block">
                 STEP {{ scanProgress }}/3: {{ scanMessage }}
               </div>
             </div>
           </div>
           <!-- Progress bar -->
           <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden relative">
             <div class="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full" style="transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1)" :style="{ width: (scanProgress/3*100) + '%' }"></div>
           </div>
        </div>
        
        <div class="flex justify-between items-center mt-8">
          <button @click="step = 'select_mode'" class="text-sm font-bold text-slate-400 hover:text-slate-800 transition-colors px-4 py-2" :disabled="scanning">返回重选</button>
          <button 
            @click="startScraping"
            :disabled="scanning || !searchQuery.trim()"
            class="px-6 py-3 bg-primary hover:bg-primary-hover disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl text-sm font-bold shadow-lg shadow-primary/20 transition-all flex items-center gap-2"
          >
            请求 AI 联网检索
            <span class="material-symbols-outlined text-[18px]">search</span>
          </button>
        </div>
      </div>
      
      <!-- Fill Form Mode (Manual or Post-Scrape) -->
      <div v-if="step === 'fill_form'" class="flex flex-col max-h-[85vh]">
         <div class="p-6 bg-slate-50 border-b border-slate-100 flex items-center gap-3 shrink-0">
            <div class="w-10 h-10 bg-white rounded-lg shadow-sm border border-slate-200 flex items-center justify-center text-xl font-display font-bold text-slate-400 uppercase">
              {{ draftProfile.productName ? draftProfile.productName.charAt(0) : 'P' }}
            </div>
            <div>
               <div class="text-sm font-bold text-slate-800">完善产品资料档案</div>
               <div class="text-[11px] text-slate-500">请核对并填写核心资料。完成后将收录至左侧归因列表。</div>
            </div>
         </div>
         
         <div class="flex-1 overflow-y-auto custom-scrollbar p-6">
            <BrandProfileForm v-model="draftProfile" class="shadow-none border-none ring-0 !" />
            <!-- Note: You can add an image uploader widget here later for the specific cover. -->
         </div>
         
         <div class="p-4 border-t border-slate-100 bg-white flex justify-end gap-3 shrink-0">
            <button @click="$emit('close')" class="px-5 py-2.5 rounded-xl font-bold text-sm text-slate-500 hover:bg-slate-100 transition-colors">取消</button>
            <button 
              @click="submitForm"
              class="px-6 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-xl font-bold text-sm shadow-md shadow-primary/20 transition-all flex items-center gap-2"
            >
              完成并创建档案
              <span class="material-symbols-outlined text-[18px]">check_circle</span>
            </button>
         </div>
      </div>
      
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import BrandProfileForm from './BrandProfileForm.vue'
import type { BrandProfile, SellingPointItem, VisualAssetItem } from '../../types/brandInjection'

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'success', profile: BrandProfile, points?: SellingPointItem[], assets?: VisualAssetItem[]): void
}>()

const step = ref<'select_mode' | 'auto_input' | 'fill_form'>('select_mode')
const searchQuery = ref('')
const scanning = ref(false)
const scanProgress = ref(1)
const scanMessage = ref('初始化 AI 检索代理引擎...')

const draftProfile = ref<BrandProfile>({
  brandId: `draft_${Date.now()}`,
  brandName: '',
  productName: '',
  positioning: '',
  targetAudience: '',
  scenarios: '',
  tone: '',
  forbiddenPhrases: []
})

const draftPoints = ref<SellingPointItem[]>([])
const draftAssets = ref<VisualAssetItem[]>([])

function selectMode(mode: 'manual' | 'auto') {
  if (mode === 'manual') {
    draftProfile.value = {
      brandId: `draft_${Date.now()}`,
      brandName: '',
      productName: '',
      positioning: '',
      targetAudience: '',
      scenarios: '',
      tone: '',
      forbiddenPhrases: []
    }
    step.value = 'fill_form'
  } else {
    step.value = 'auto_input'
  }
}

async function startScraping() {
  if (!searchQuery.value.trim() || scanning.value) return
  alert('当前版本未开放 AI 联网建档接口，请使用“手动创建”方式。')
}

function submitForm() {
  emit('success', draftProfile.value, draftPoints.value, draftAssets.value)
}
</script>
