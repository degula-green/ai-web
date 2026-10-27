<template>
  <div class="h-full bg-[#f4f5f7] flex flex-col font-sans text-slate-800 absolute inset-0">
    <div class="bg-white px-8 py-5 flex items-center justify-between shrink-0 shadow-sm z-10 sticky top-0">
      <div>
        <h1 class="text-xl font-bold font-display tracking-tight text-slate-900 flex items-center gap-2">
          品牌产品与资产库
        </h1>
        <p class="text-[13px] text-slate-500 mt-1">沉淀多形态产品档案、视觉资产池与营销禁忌，一次配置多路复用。</p>
      </div>

      <div class="flex gap-3">
        <div class="relative w-64 mr-2">
          <input v-model="searchKeyword" @keyup.enter="loadProductList" type="text" placeholder="检索产品或品牌..." class="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-primary focus:bg-white transition-all">
          <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[18px] text-slate-400">search</span>
        </div>
        <button
          @click="showWizard = true"
          class="px-5 py-2 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-bold shadow-md shadow-primary/20 transition-all flex items-center gap-1.5"
        >
          <span class="material-symbols-outlined text-[18px]">add</span>
          新增产品线
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar p-8">
      <div v-if="initialLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div v-for="i in 4" :key="i" class="h-64 bg-white/50 animate-pulse rounded-2xl w-full border border-slate-100"></div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
        <div
          v-for="item in productList"
          :key="item.id"
          class="bg-white rounded-2xl overflow-hidden border border-slate-200 transition-all duration-300 group flex flex-col cursor-pointer hover:shadow-lg hover:-translate-y-1 hover:border-primary/30"
          @click="handleSelectProduct(item.id)"
        >
          <div class="w-full aspect-[4/3] bg-slate-100 relative overflow-hidden shrink-0">
            <img :src="item.cover" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />

            <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-black/10 opacity-80"></div>

            <div class="absolute top-3 left-3">
              <span class="px-2 py-1 bg-white/20 backdrop-blur-md text-white text-[10px] font-bold rounded shadow-sm border border-white/20 uppercase tracking-widest">
                {{ item.brand }}
              </span>
            </div>

            <div class="absolute inset-0 bg-primary/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[2px]">
              <div class="w-10 h-10 bg-white rounded-full text-primary flex items-center justify-center shadow-lg transform translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
                <span class="material-symbols-outlined text-[20px]">edit</span>
              </div>
            </div>
          </div>

          <div class="p-4 bg-white flex flex-col justify-between flex-1">
            <div class="text-[15px] font-bold text-slate-800 line-clamp-2 leading-snug mb-3 group-hover:text-primary transition-colors">{{ item.name }}</div>

            <div class="flex items-center justify-between mt-auto pt-3 border-t border-slate-50">
              <div class="flex items-center gap-1.5 text-[11px] text-slate-500 font-medium">
                <span class="material-symbols-outlined text-[14px]">imagesmode</span>
                {{ item.assetsCount }} 素材
              </div>
              <div class="flex items-center gap-1.5 text-[11px] text-slate-500 font-medium">
                <span class="material-symbols-outlined text-[14px]">psychiatry</span>
                {{ item.spCount }} 卖点
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <CreateProductWizard v-if="showWizard" @close="showWizard = false" @success="onWizardSuccess" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

import { useRouter } from 'vue-router'
import type { BrandProfile, SellingPointItem, VisualAssetItem } from '../../types/brandInjection'
import {
  listBrandProducts,
  getVisualAssets,
  saveSellingPoints,
  saveBrandProfile,
} from '../../api/brandInjection'

import CreateProductWizard from '../../components/brand-manager/CreateProductWizard.vue'

const router = useRouter()

const initialLoading = ref(true)
const showWizard = ref(false)
const searchKeyword = ref('')

const productList = ref<Array<{
  id: string
  brand: string
  name: string
  cover: string
  assetsCount: number
  spCount: number
}>>([])

onMounted(async () => {
  await loadProductList()
})

async function loadProductList() {
  initialLoading.value = true
  try {
    const data = await listBrandProducts({ keyword: searchKeyword.value, pageNo: 1, pageSize: 100 })
    productList.value = await Promise.all(
      data.list.map(async (item) => {
        let cover = item.coverUrl || ''
        if (!cover && (item.visualAssetsCount ?? 0) > 0) {
          try {
            const assets = await getVisualAssets(item.brandId)
            cover = selectCoverFromAssets(assets)
          } catch {
            cover = ''
          }
        }

        return {
          id: item.brandId,
          brand: item.brandName || '未命名品牌',
          name: item.productName || '未命名资料',
          cover: cover || 'https://images.unsplash.com/photo-1620121692029-d088224ddc74?q=80&w=600&auto=format&fit=crop',
          assetsCount: item.visualAssetsCount ?? 0,
          spCount: item.sellingPointsCount ?? 0,
        }
      }),
    )
  } catch (err) {
    console.error(err)
    alert('加载产品列表失败')
  } finally {
    initialLoading.value = false
  }
}

async function handleSelectProduct(id: string) {
  router.push({ name: 'brand-manager-detail', params: { id } })
}

function selectCoverFromAssets(assets: VisualAssetItem[]): string {
  const coverCandidate = assets.find((item) => item.assetType !== 'video' && item.usableForCover) || assets.find((item) => item.assetType !== 'video')
  return coverCandidate ? (coverCandidate.thumbnail || coverCandidate.assetUrl) : ''
}

async function onWizardSuccess(newProfile: BrandProfile, newPoints?: SellingPointItem[], _newAssets?: VisualAssetItem[]) {
  try {
    const savedBrandId = await saveBrandProfile(newProfile)
    if (newPoints && newPoints.length > 0) {
      const cleanedPoints = newPoints
        .map((point) => ({ ...point, title: point.title.trim() }))
        .filter((point) => point.title.length > 0)
      await saveSellingPoints(savedBrandId, cleanedPoints, [])
    }

    await loadProductList()
    showWizard.value = false
    await handleSelectProduct(savedBrandId)
  } catch (error) {
    console.error(error)
    alert('创建档案失败，请检查后端API')
  }
}
</script>

<style scoped>
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.drawer-enter-active,
.drawer-leave-active {
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(100%);
}
</style>
