<template>
  <div class="h-full bg-[#f4f5f7] flex flex-col font-sans text-slate-800 absolute inset-0">
    <!-- Header -->
    <div class="bg-white px-8 py-5 flex items-center justify-between shrink-0 shadow-sm z-10 sticky top-0 border-b border-slate-200">
      <div class="flex items-center gap-4">
        <button @click="router.push('/brand-manager')" class="w-10 h-10 bg-slate-50 hover:bg-slate-100 text-slate-500 hover:text-slate-700 flex items-center justify-center rounded-full transition-colors border border-slate-200">
          <span class="material-symbols-outlined">arrow_back</span>
        </button>
        <div>
          <div class="flex items-center gap-2 text-[11px] text-slate-400 font-bold uppercase tracking-wider mb-1">
            <span class="material-symbols-outlined text-[14px] text-primary">branding_watermark</span>
            {{ profile?.brandName || '加载中...' }}
          </div>
          <h2 class="text-xl font-bold text-slate-900 font-display">{{ profile?.productName || '加载产品详情...' }}</h2>
        </div>
      </div>
      
      <!-- Actions -->
      <div class="flex items-center gap-3">
        <button @click="handleDelete" :disabled="saving" class="px-3 py-2 text-red-500 hover:bg-red-50 hover:text-red-600 rounded-lg text-sm font-bold transition-all disabled:opacity-50 flex items-center gap-1" title="删除当前档案">
          <span class="material-symbols-outlined text-[18px]">delete</span>
        </button>
        <button @click="handleSave" :disabled="saving" class="px-6 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg text-sm font-bold transition-all disabled:opacity-50 flex items-center gap-2 shadow-sm">
          <span v-if="saving" class="material-symbols-outlined text-[16px] animate-spin">refresh</span>
          <span v-else class="material-symbols-outlined text-[16px]">save</span>
          保存配置
        </button>
      </div>
    </div>

    <!-- Content: CSS Grid layout 1/3 and 2/3 -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-8 relative">
      <div v-if="loading" class="absolute inset-0 bg-slate-50/80 backdrop-blur-sm z-10 flex items-center justify-center">
        <span class="material-symbols-outlined animate-spin text-primary text-4xl">refresh</span>
      </div>

      <div class="max-w-[1600px] mx-auto grid grid-cols-12 gap-8 h-full">
        <!-- Left Column: Base Parameters (4/12) -->
        <div class="col-span-12 xl:col-span-4 flex flex-col sticky top-0 self-start h-max">
          <BrandProfileForm v-model="profile" class="ring-1 ring-slate-200 shadow-xl rounded-2xl border-none bg-white h-max" />
        </div>

        <!-- Right Column: Selling Points & Visual Assets (8/12) -->
        <div class="col-span-12 xl:col-span-8 flex flex-col gap-6 items-start">
          <div class="flex gap-2 w-full">
            <button @click="activeTab = 'selling_points'" class="px-6 py-3 rounded-xl font-bold text-[15px] transition-all flex items-center gap-2" :class="activeTab === 'selling_points' ? 'bg-primary text-white shadow-md shadow-primary/20' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'">
              <span class="material-symbols-outlined text-[20px]">hub</span>
              营销卖点库
            </button>
            <button @click="activeTab = 'visual_assets'" class="px-6 py-3 rounded-xl font-bold text-[15px] transition-all flex items-center gap-2" :class="activeTab === 'visual_assets' ? 'bg-primary text-white shadow-md shadow-primary/20' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'">
              <span class="material-symbols-outlined text-[20px]">collections_bookmark</span>
              视觉素材归集
            </button>
          </div>

          <transition name="fade" mode="out-in">
            <div v-if="activeTab === 'selling_points'" class="w-full">
              <SellingPointPanel
                v-model="sellingPoints"
                :extracting="extracting"
                @extract="handleExtract"
                class="ring-1 ring-slate-200 shadow-xl rounded-2xl border-none h-max"
              >
                <template #feishu-widget>
                  <FeishuConfirmStatus :loading="syncing" @push="handleFeishuPush" class="mb-5 shadow-sm border-slate-200/60 bg-white" />
                </template>
              </SellingPointPanel>
            </div>

            <div v-else-if="activeTab === 'visual_assets'" class="w-full">
              <VisualAssetLibrary
                :assets="visualAssets"
                :uploading="uploadingAsset"
                @upload="handleUploadAsset"
                @view="handleViewAsset"
                @remove="handleRemoveAsset"
                class="ring-1 ring-slate-200 shadow-xl rounded-2xl border-none min-h-[500px] h-max bg-white"
              />
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- Modal for Preview -->
    <transition name="fade">
      <div v-if="previewAssetUrl" class="fixed inset-0 z-[100] bg-black/90 flex items-center justify-center p-8 backdrop-blur-sm" @click="previewAssetUrl = ''">
        <button class="absolute top-6 right-6 text-white hover:text-primary transition-colors bg-white/10 rounded-full w-10 h-10 flex items-center justify-center">
          <span class="material-symbols-outlined text-[24px]">close</span>
        </button>
        <img v-if="previewAssetType === 'image'" :src="previewAssetUrl" class="max-w-full max-h-full object-contain rounded-lg shadow-2xl ring-1 ring-white/10" @click.stop />
        <video v-else :src="previewAssetUrl" controls autoplay class="max-w-full max-h-full object-contain rounded-lg shadow-2xl ring-1 ring-white/10" @click.stop></video>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

import type { BrandProfile, SellingPointItem, VisualAssetItem } from '../../types/brandInjection'
import {
  getBrandProfile,
  getSellingPoints,
  getVisualAssets,
  uploadVisualAsset,
  deleteVisualAsset,
  saveSellingPoints,
  deleteBrandProfile,
  extractAISellingPoints,
  syncFeishuApproval,
  saveBrandProfile,
} from '../../api/brandInjection'

import BrandProfileForm from '../../components/brand-manager/BrandProfileForm.vue'
import SellingPointPanel from '../../components/brand-manager/SellingPointPanel.vue'
import FeishuConfirmStatus from '../../components/brand-manager/FeishuConfirmStatus.vue'
import VisualAssetLibrary from '../../components/brand-manager/VisualAssetLibrary.vue'

const router = useRouter()
const route = useRoute()
const brandId = route.params.id as string

const loading = ref(true)
const activeTab = ref<'selling_points'|'visual_assets'>('selling_points')
const extracting = ref(false)
const syncing = ref(false)
const saving = ref(false)
const uploadingAsset = ref(false)
const loadedSellingPointIds = ref<string[]>([])

const profile = ref<BrandProfile>({
  brandId: 'new',
  brandName: '',
  productName: '',
  positioning: '',
  targetAudience: '',
  scenarios: '',
  tone: '',
  forbiddenPhrases: [],
  coverUrl: '',
})
const sellingPoints = ref<SellingPointItem[]>([])
const visualAssets = ref<VisualAssetItem[]>([])

onMounted(async () => {
  if (brandId) {
    await loadDetails(brandId)
  } else {
    router.push('/brand-manager')
  }
})

function selectCoverFromAssets(assets: VisualAssetItem[]): string {
  const coverCandidate = assets.find((item) => item.assetType !== 'video' && item.usableForCover) || assets.find((item) => item.assetType !== 'video')
  return coverCandidate ? (coverCandidate.thumbnail || coverCandidate.assetUrl) : ''
}

async function loadDetails(id: string) {
  loading.value = true
  try {
    const [p, sp, va] = await Promise.all([getBrandProfile(id), getSellingPoints(id), getVisualAssets(id)])
    profile.value = p
    sellingPoints.value = sp
    visualAssets.value = va
    
    if (!profile.value.coverUrl) {
      profile.value.coverUrl = selectCoverFromAssets(va)
    }
    loadedSellingPointIds.value = sp.map((item) => item.id)
  } catch (err) {
    console.error(err)
    alert('加载产品详情失败')
    router.push('/brand-manager')
  } finally {
    loading.value = false
  }
}

async function handleExtract() {
  try {
    if (extracting.value) return
    extracting.value = true
    await extractAISellingPoints(profile.value.brandId, profile.value)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'AI提炼失败'
    alert(message)
  } finally {
    extracting.value = false
  }
}

async function handleFeishuPush() {
  try {
    if (syncing.value) return
    syncing.value = true
    await syncFeishuApproval(sellingPoints.value.map((p) => p.id))
  } catch (error) {
    const message = error instanceof Error ? error.message : '飞书推送失败'
    alert(message)
  } finally {
    syncing.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const savedBrandId = await saveBrandProfile(profile.value)
    profile.value.brandId = savedBrandId

    const cleanedPoints = sellingPoints.value
      .map((point) => ({ ...point, title: point.title.trim() }))
      .filter((point) => point.title.length > 0)

    if (cleanedPoints.length !== sellingPoints.value.length) {
      alert('存在未填写标题的卖点，请补充完整或删除后再保存。')
      saving.value = false
      return
    }

    sellingPoints.value = cleanedPoints

    await saveSellingPoints(savedBrandId, cleanedPoints, loadedSellingPointIds.value)

    const latestSellingPoints = await getSellingPoints(savedBrandId)
    sellingPoints.value = latestSellingPoints
    loadedSellingPointIds.value = latestSellingPoints.map((item) => item.id)

    alert('保存成功')
  } catch (error) {
    console.error(error)
    alert('保存失败，请检查后端API')
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (confirm('确定删除此档案及相关卖点和素材吗？此操作无法撤销。')) {
    try {
      await deleteBrandProfile(profile.value.brandId)
      alert('已删除')
      router.push('/brand-manager')
    } catch (error) {
      console.error(error)
      alert('删除失败，请检查后端API')
    }
  }
}

function inferAssetType(file: File): VisualAssetItem['assetType'] {
  if (file.type.startsWith('video/')) return 'video'
  if (file.type.startsWith('image/')) return 'promo'
  return 'promo'
}

async function handleUploadAsset(file: File) {
  if (uploadingAsset.value) return

  const bid = profile.value.brandId
  if (!/^\d+$/.test(bid)) {
    alert('请先保存档案再上传素材')
    return
  }

  uploadingAsset.value = true
  try {
    const assetType = inferAssetType(file)
    const uploaded = await uploadVisualAsset(
      file,
      {
        assetType,
        tags: ['new'],
        platforms: [],
        scenarios: [],
        relatedSellingPointIds: [],
        usableForCover: assetType !== 'video',
        usableForVideo: assetType === 'video',
      },
      bid,
    )

    visualAssets.value = await getVisualAssets(bid)

    if (assetType !== 'video') {
      profile.value.coverUrl = uploaded.thumbnail || uploaded.assetUrl
      await saveBrandProfile(profile.value)
    }

    alert('上传成功')
  } catch (error) {
    console.error(error)
    alert('上传失败，请检查后端或MinIO配置')
  } finally {
    uploadingAsset.value = false
  }
}

const previewAssetUrl = ref('')
const previewAssetType = ref<'image' | 'video'>('image')

function handleViewAsset(asset: VisualAssetItem) {
  const url = asset.assetUrl || asset.thumbnail
  if (!url) return
  previewAssetUrl.value = url
  previewAssetType.value = asset.assetType === 'video' ? 'video' : 'image'
}

async function handleRemoveAsset(asset: VisualAssetItem) {
  if (!confirm('确定删除此素材吗？')) return

  try {
    await deleteVisualAsset(asset.id)
    const latest = await getVisualAssets(profile.value.brandId)
    visualAssets.value = latest

    const removedCoverUrl = profile.value.coverUrl || ''
    const removedAssetUrl = asset.assetUrl || ''
    const removedThumbUrl = asset.thumbnail || ''
    if (removedCoverUrl && (removedCoverUrl === removedAssetUrl || removedCoverUrl === removedThumbUrl)) {
      profile.value.coverUrl = selectCoverFromAssets(latest)
      await saveBrandProfile(profile.value)
    }
  } catch (error) {
    console.error(error)
    alert('删除素材失败，请检查后端API')
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
</style>
