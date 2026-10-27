<template>
  <section class="space-y-4 font-sans transition-all duration-300">
    <div class="flex items-center justify-between border-b border-border pb-2">
      <h4 class="text-sm font-bold text-text-main flex items-center gap-2">
        <span class="material-symbols-outlined text-[18px] text-primary">brand_awareness</span>
        4. 附加品牌上下文 <span class="text-xs text-text-secondary font-normal">(Brand Context)</span>
      </h4>
      <span class="text-xs text-text-tertiary font-medium">可选 (Optional)</span>
    </div>
    
    <div>
      <label class="block text-xs font-bold text-text-secondary mb-1.5">预载入品牌知识库</label>
      <div class="relative">
        <select 
          v-model="selectedProductId"
          @change="handleProductChange"
          class="w-full appearance-none bg-surface-secondary border border-border rounded-xl pl-3 pr-8 py-2.5 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 text-text-main font-medium transition-all cursor-pointer"
        >
          <option value="">-- 当前不挂载任何品牌参数 --</option>
          <option v-for="item in productOptions" :key="item.brandId" :value="item.brandId">{{ item.brandName }} - {{ item.productName }}</option>
        </select>
        <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-[18px] text-text-tertiary pointer-events-none">expand_more</span>
      </div>
    </div>

    <!-- Details only if a brand is selected -->
    <div v-if="selectedBrand" class="p-4 bg-surface-secondary border border-border rounded-xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
      
      <!-- 禁用词和约束 -->
      <div class="flex items-start gap-3">
        <div class="p-1.5 rounded-lg bg-red-50 text-red-500 border border-red-100 flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-[18px]">block</span>
        </div>
        <div>
          <div class="text-xs font-bold text-text-main">系统已自动应用红线禁用词</div>
          <div class="text-[11px] text-text-secondary mt-1 leading-relaxed">{{ selectedBrand.forbiddenPhrases.join('，') }}</div>
        </div>
      </div>

      <!-- 营销参数选择 -->
      <div class="pt-2 border-t border-border/50">
        <div class="flex items-center justify-between mb-3 border-t-border mt-1">
          <label class="block text-xs font-bold text-text-main">按需投喂营销卖点 <span class="text-text-tertiary font-normal">({{ activePoints.length }}/{{ sellingPoints.length }})</span></label>
          <button @click="selectAllPoints" class="text-xs text-primary hover:underline font-medium">全选可用</button>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <label 
            v-for="sp in sellingPoints" 
            :key="sp.id"
            class="flex items-start gap-2 p-2.5 rounded-xl border cursor-pointer transition-colors"
            :class="activePoints.includes(sp.id) ? 'bg-primary/5 border-primary/40' : 'bg-surface border-border hover:border-primary/30'"
          >
            <div class="flex items-center h-4 mt-0.5">
              <input type="checkbox" :value="sp.id" v-model="activePoints" class="w-3.5 h-3.5 accent-primary rounded bg-white">
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-bold text-text-main flex items-center flex-wrap gap-1">
                <span class="truncate">{{ sp.title }}</span>
                <span v-if="sp.type === 'required'" class="text-[9px] text-red-600 font-bold border border-red-200 bg-red-50 px-1 py-0.5 rounded leading-none shrink-0">必录</span>
              </div>
            </div>
          </label>
        </div>
      </div>

      <!-- 视觉资产预载 -->
      <div class="pt-2 border-t border-border/50">
         <div class="flex items-center justify-between mb-3 border-t-border mt-1">
          <label class="block text-xs font-bold text-text-main">绑定视觉生成资产 <span class="text-text-tertiary font-normal">({{ activeAssets.length }}/{{ visualAssets.length }})</span></label>
        </div>
        <div class="flex gap-2.5 overflow-x-auto pb-1 custom-scrollbar">
           <label 
            v-for="asset in visualAssets" 
            :key="asset.id"
            class="relative cursor-pointer group shrink-0"
          >
            <input type="checkbox" :value="asset.id" v-model="activeAssets" class="sr-only peer">
            <div class="w-16 h-16 rounded-xl border-2 overflow-hidden peer-checked:border-primary border-border opacity-70 peer-checked:opacity-100 transition-all hover:border-primary/50 bg-surface">
              <img :src="asset.thumbnail" class="w-full h-full object-cover">
            </div>
            <div class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-primary rounded-full flex items-center justify-center opacity-0 peer-checked:opacity-100 transition-opacity z-10 scale-0 peer-checked:scale-100 shadow-sm border-2 border-surface">
              <span class="material-symbols-outlined text-[12px] text-white font-bold">check</span>
            </div>
          </label>
        </div>
      </div>

    </div>
    
    <div v-else-if="selectedProductId" class="py-12 flex justify-center">
      <div class="w-8 h-8 border-4 border-surface-secondary border-t-primary rounded-full animate-spin"></div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getBrandProfile, getSellingPoints, getVisualAssets, listBrandProducts } from '../../api/brandInjection'
import type { BrandProfile, SellingPointItem, VisualAssetItem } from '../../types/brandInjection'
const selectedProductId = ref('')
const productOptions = ref<Array<{ brandId: string; brandName: string; productName: string }>>([])

const selectedBrand = ref<BrandProfile | null>(null)
const sellingPoints = ref<SellingPointItem[]>([])
const visualAssets = ref<VisualAssetItem[]>([])

const activePoints = ref<string[]>([])
const activeAssets = ref<string[]>([])

onMounted(async () => {
  try {
    const data = await listBrandProducts({ pageNo: 1, pageSize: 100 })
    productOptions.value = data.list.map((item) => ({
      brandId: item.brandId,
      brandName: item.brandName,
      productName: item.productName,
    }))
  } catch (err) {
    console.error(err)
  }
})

async function handleProductChange() {
  if (!selectedProductId.value) {
    selectedBrand.value = null
    sellingPoints.value = []
    visualAssets.value = []
    activePoints.value = []
    activeAssets.value = []
    return
  }
  
  selectedBrand.value = null
  sellingPoints.value = []
  visualAssets.value = []
  activePoints.value = []
  activeAssets.value = []
  
  try {
    const pId = selectedProductId.value
    const [p, sp, va] = await Promise.all([
      getBrandProfile(pId),
      getSellingPoints(pId),
      getVisualAssets(pId)
    ])
    selectedBrand.value = p
    sellingPoints.value = sp
    visualAssets.value = va
    
    // Auto check required points
    activePoints.value = sp.filter(item => item.type === 'required').map(item => item.id)
  } catch (err) {
    console.error(err)
  }
}

function selectAllPoints() {
  if (activePoints.value.length === sellingPoints.value.length) {
    activePoints.value = []
  } else {
    activePoints.value = sellingPoints.value.map(sp => sp.id)
  }
}
</script>
