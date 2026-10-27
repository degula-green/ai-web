<template>
  <div class="h-full overflow-y-auto bg-slate-50 p-6 font-sans text-slate-800">
    <div class="mx-auto flex w-full max-w-[1600px] flex-col gap-5">
      <section class="page-header">
        <div>
          <h1 class="page-title">内容创作台</h1>
          <p class="page-subtitle">模特数字人当前只生成图组，到图组展示即完成，不再继续生成视频。</p>
        </div>

        <div class="header-actions">
          <button
            class="draft-library-button"
            type="button"
            @click="openDraftLibrary"
          >
            草稿箱<span v-if="currentSceneDraftCount"> {{ currentSceneDraftCount }}</span>
          </button>

          <div class="mode-switch">
            <button class="mode-switch-button" type="button" @click="toggleModeMenu">
              {{ currentModeLabel }}
            </button>
            <div v-if="showModeMenu" class="mode-switch-menu">
              <button
                class="mode-switch-item"
                :class="{ active: currentMode === 'manual' }"
                type="button"
                @click="selectMode('manual')"
              >
                手动
              </button>
              <button class="mode-switch-item" type="button" disabled>自动</button>
              <button class="mode-switch-item" type="button" disabled>批量</button>
            </div>
          </div>

          <select
            v-model="videoPurposeScene"
            class="header-purpose-select"
            title="成片用途"
          >
            <option value="口播数字人">口播数字人</option>
            <option value="卖货数字人">卖货数字人</option>
            <option value="产品介绍数字人">产品介绍数字人</option>
            <option value="模特数字人">模特数字人</option>
            <option value="视频剪辑数字人">视频剪辑数字人</option>
          </select>
        </div>
      </section>

      <div class="grid-layout">
        <div class="flow-column">
          <section class="panel-card">
            <div class="panel-head">
              <div>
                <span class="panel-step">01</span>
                <h2>产品选择</h2>
              </div>
              <button class="text-link" type="button" :disabled="productsLoading" @click="loadProducts">
                {{ productsLoading ? '加载中...' : '刷新产品' }}
              </button>
            </div>

            <div class="section-stack">
              <input
                v-model.trim="productKeyword"
                class="field-input"
                placeholder="搜索品牌产品"
                @keyup.enter="loadProducts"
              />

              <select v-model="selectedProductId" class="field-input" @change="handleProductChange">
                <option value="">请选择产品</option>
                <option
                  v-for="item in productList"
                  :key="item.brandId"
                  :value="item.brandId"
                >
                  {{ item.productName || '未命名产品' }} / {{ item.brandName || '未命名品牌' }}
                </option>
              </select>

              <div v-if="selectedProductProfile" class="status-card">
                <span class="status-dot"></span>
                <span>已选择：{{ selectedProductProfile.brandName }} / {{ selectedProductProfile.productName }}</span>
              </div>
            </div>

            <template v-if="productImageAssets.length">
              <div class="mini-grid product-asset-mini">
                <div class="product-asset-field">
                  <label class="field-label">产品白底图</label>
                  <button
                    class="product-asset-picker-trigger"
                    type="button"
                    @click="openProductAssetPicker('white')"
                  >
                    <div class="product-asset-picker-thumb">
                      <img
                        v-if="selectedWhiteAsset"
                        :src="selectedWhiteAsset.thumbnail || selectedWhiteAsset.assetUrl"
                        alt=""
                      />
                      <span v-else class="material-symbols-outlined product-asset-picker-placeholder">image</span>
                    </div>
                    <div class="product-asset-picker-meta">
                      <span class="product-asset-picker-title">选择白底图</span>
                      <span class="product-asset-picker-sub">
                        {{ selectedWhiteImageId ? '已选择，点击更换' : '未选择' }}
                      </span>
                    </div>
                    <span class="material-symbols-outlined product-asset-picker-chevron">chevron_right</span>
                  </button>
                </div>

                <div class="product-asset-field">
                  <label class="field-label">产品佩戴图</label>
                  <button
                    class="product-asset-picker-trigger"
                    type="button"
                    @click="openProductAssetPicker('wear')"
                  >
                    <div class="product-asset-picker-thumb">
                      <img
                        v-if="selectedWearAsset"
                        :src="selectedWearAsset.thumbnail || selectedWearAsset.assetUrl"
                        alt=""
                      />
                      <span v-else class="material-symbols-outlined product-asset-picker-placeholder">image</span>
                    </div>
                    <div class="product-asset-picker-meta">
                      <span class="product-asset-picker-title">选择佩戴图</span>
                      <span class="product-asset-picker-sub">
                        {{ selectedWearImageId ? '已选择，点击更换' : '未选择' }}
                      </span>
                    </div>
                    <span class="material-symbols-outlined product-asset-picker-chevron">chevron_right</span>
                  </button>
                </div>
              </div>
            </template>
          </section>

          <section class="panel-card">
            <div class="panel-head">
              <div>
                <span class="panel-step">02</span>
                <h2>数字人素材</h2>
              </div>
            </div>

            <div class="mini-grid">
              <div>
                <div class="panel-subhead">
                  <div>
                    <label class="field-label">数字人图片</label>
                    <p class="field-hint">仅支持图片，不支持视频参考。</p>
                  </div>
                  <button class="text-link" type="button" :disabled="modelImageUploading" @click="openModelImageUpload">
                    {{ modelImageUploading ? '上传中...' : '上传图片' }}
                  </button>
                </div>

                <input
                  ref="modelImageInput"
                  type="file"
                  class="hidden"
                  accept="image/*"
                  @change="handleModelImageChange"
                />

                <div class="upload-box">
                  <template v-if="modelImageUrl">
                    <img :src="modelImageUrl" class="preview-image" />
                  </template>
                  <template v-else>
                    <span class="material-symbols-outlined empty-icon">person</span>
                    <p>上传数字人图</p>
                  </template>
                </div>
              </div>

              <div>
                <div class="panel-subhead">
                  <div>
                    <label class="field-label">场景图</label>
                    <p class="field-hint">不上传时回退使用产品佩戴图。</p>
                  </div>
                  <button class="text-link" type="button" :disabled="sceneImageUploading" @click="openSceneImageUpload">
                    {{ sceneImageUploading ? '上传中...' : '上传场景图' }}
                  </button>
                </div>

                <input
                  ref="sceneImageInput"
                  type="file"
                  class="hidden"
                  accept="image/*"
                  @change="handleSceneImageChange"
                />

                <div class="upload-box">
                  <template v-if="sceneImageUrl">
                    <img :src="sceneImageUrl" class="preview-image" />
                  </template>
                  <template v-else>
                    <span class="material-symbols-outlined empty-icon">landscape</span>
                    <p>上传场景图</p>
                  </template>
                </div>
              </div>
            </div>
          </section>
        </div>

        <div class="preview-column">
          <section class="panel-card">
            <div class="panel-head">
              <div>
                <span class="panel-step">03</span>
                <h2>补充需求</h2>
              </div>
              <button class="text-link" type="button" :disabled="suggestingRequirements" @click="handleSuggestRequirements">
                {{ suggestingRequirements ? '生成中...' : '自动生成要求' }}
              </button>
            </div>

            <div class="toolbar-grid">
              <div>
                <label class="field-label">生成张数</label>
                <select v-model="imageCount" class="field-input">
                  <option v-for="count in imageCountOptions" :key="count" :value="count">
                    {{ count }} 张
                  </option>
                </select>
              </div>
              <div class="count-card">
                <span>图片比例</span>
                <select v-model="aspectRatio" class="field-input compact-select">
                  <option v-for="ratio in aspectRatioOptions" :key="ratio" :value="ratio">
                    {{ ratio }}
                  </option>
                </select>
              </div>
            </div>

            <textarea
              v-model="extraRequirements"
              class="field-area h-[180px]"
              placeholder="例如：第2张夜景，第3张跑动动态模糊，第4张增加合影感。也可以点击右上角自动生成要求。"
            />

            <button class="primary-button" type="button" :disabled="galleryGenerating" @click="generateGallery">
              {{ galleryGenerating ? '生成中...' : '生成展示图列表' }}
            </button>

            <div class="status-card">
              <span class="status-dot"></span>
              <span>{{ galleryTaskStatusLabel }}</span>
            </div>
          </section>

          <section class="panel-card">
            <div class="panel-head">
              <div>
                <span class="panel-step">04</span>
                <h2>图组展示</h2>
              </div>
            </div>

            <div v-if="visibleGalleryImages.length" class="gallery-grid">
              <div
                v-for="(image, index) in visibleGalleryImages"
                :key="`${image.url}-${index}`"
                class="gallery-image-card"
              >
                <button class="gallery-image-button" type="button" @click="openImagePreview(image)">
                  <img :src="image.url" class="gallery-image" />
                </button>
                <div class="gallery-card-footer">
                  <span class="gallery-card-label">第 {{ index + 1 }} 张</span>
                  <div class="gallery-card-actions">
                    <button class="secondary-button" type="button" @click="openImagePreview(image)">查看大图</button>
                    <button class="secondary-button" type="button" @click="downloadGalleryImage(image, index)">下载</button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-gallery">
              先完成前三步，再在这里查看生成好的图片列表。
            </div>
          </section>
        </div>
      </div>
    </div>

    <div
      v-if="productAssetPickerKind"
      class="draft-library-mask"
      role="dialog"
      aria-modal="true"
      @click.self="closeProductAssetPicker"
    >
      <div class="draft-library-dialog product-asset-picker-dialog">
        <div class="draft-library-head">
          <div>
            <h3>{{ productAssetPickerKind === 'white' ? '选择产品白底图' : '选择产品佩戴图' }}</h3>
            <p>点击下方缩略图即可选中并关闭弹窗。</p>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-close" type="button" @click="closeProductAssetPicker">取消</button>
          </div>
        </div>
        <div class="product-asset-picker-grid">
          <button
            v-for="asset in productImageAssets"
            :key="`${productAssetPickerKind}-${asset.id}`"
            type="button"
            class="product-asset-picker-option"
            :class="{
              active:
                productAssetPickerKind === 'white'
                  ? selectedWhiteImageId === asset.id
                  : selectedWearImageId === asset.id,
            }"
            @click="confirmProductAssetPick(asset.id)"
          >
            <img :src="asset.thumbnail || asset.assetUrl" alt="" />
            <span v-if="asset.tags?.length" class="product-asset-picker-tag">{{ asset.tags[0] }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDraftLibrary" class="draft-library-mask" @click.self="closeDraftLibrary">
      <div class="draft-library-dialog">
        <div class="draft-library-head">
          <div>
            <h3>创作草稿</h3>
            <p>草稿会按场景保存当前步骤数据，你可以继续编辑或重新新建一条。</p>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-secondary" type="button" @click="handleCreateNewContent">新建内容</button>
            <button class="draft-library-close" type="button" @click="closeDraftLibrary">关闭</button>
          </div>
        </div>
        <div v-if="draftLibraryLoading" class="draft-library-empty">草稿加载中...</div>
        <div v-else-if="!draftLibraryItems.length" class="draft-library-empty">当前没有可恢复的草稿</div>
        <div v-else class="draft-library-list">
          <div
            v-for="item in draftSummaries"
            :key="item.id"
            class="draft-library-item"
          >
            <button class="draft-library-main" type="button" @click="handleSelectDraft(item.id, item.scene)">
              <strong>{{ item.title }}</strong>
              <span>{{ item.scene }}</span>
              <span>{{ formatDraftTime(item.updatedAt) }}</span>
              <span>{{ item.status }}</span>
            </button>
            <button class="draft-library-delete" type="button" @click="handleDeleteDraft(item.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="previewImage"
      class="draft-library-mask"
      role="dialog"
      aria-modal="true"
      @click.self="closeImagePreview"
    >
      <div class="image-preview-dialog">
        <div class="draft-library-head">
          <div>
            <h3>图片预览</h3>
            <p>可查看大图并下载当前图片。</p>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-secondary" type="button" @click="downloadGalleryImage(previewImage)">下载图片</button>
            <button class="draft-library-close" type="button" @click="closeImagePreview">关闭</button>
          </div>
        </div>
        <div class="image-preview-body">
          <img :src="previewImage.url" class="image-preview-full" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { buildDraftlessQuery } from '../lib/avatarSceneNavigation'
import { authStore } from '../auth/store'
import { request } from '../api/http'
import { getBrandProfile, getVisualAssets, listBrandProducts } from '../api/brandInjection'
import { taskStore, type AsyncTask } from '../data-collection/taskStore'
import type { BrandProductCard, BrandProfile, VisualAssetItem } from '../types/brandInjection'
import type { AvatarPurposeScene } from './creation-avatar-scenes'

interface UploadTicketRead {
  upload_url: string
  file_url: string
}

interface AvatarModelDraftRead {
  draft_id: string
  user_id: number
  title?: string | null
  product_keyword?: string | null
  selected_product_id?: string | null
  selected_product_profile: Record<string, unknown>
  product_assets: Array<Record<string, unknown>>
  selected_white_image_id?: string | null
  selected_wear_image_id?: string | null
  model_image_url?: string | null
  scene_image_url?: string | null
  image_count: number
  aspect_ratio: string
  extra_requirements?: string | null
  gallery_task_id?: string | null
  gallery_task_status?: string | null
  gallery_images: Array<Record<string, unknown>>
  status: string
  created_at: string
  updated_at: string
}

interface AvatarModelDraftListResponse {
  items: AvatarModelDraftRead[]
}

type CreationDraftRead = AvatarModelDraftRead

interface AvatarDraftIndexRead {
  draft_id: string
  user_id: number
  scene_code: 'talk' | 'sales' | 'product' | 'model' | string
  title?: string | null
  status: string
  current_step_code?: string | null
  progress?: number | null
  created_at: string
  updated_at: string
}

interface AvatarDraftIndexListResponse {
  items: AvatarDraftIndexRead[]
}

interface GalleryImageItem {
  url: string
  output_type?: string
  source_url?: string
  persisted?: boolean
}

interface DigitalHumanTaskResponse {
  output?: {
    task_id?: string
    task_status?: string
    results?:
      | Array<{ url?: string; video_url?: string; output_type?: string }>
      | { url?: string; video_url?: string; output_type?: string }
    video_url?: string
  }
}

interface ModelScenePersistedState {
  selected_product_id?: string | null
  selected_product_profile?: BrandProfile | null
  product_assets?: VisualAssetItem[]
  selected_white_image_id?: string | null
  selected_wear_image_id?: string | null
  model_image_url?: string | null
  scene_image_url?: string | null
  image_count?: number | null
  aspect_ratio?: string | null
  extra_requirements?: string | null
  gallery_task_id?: string | null
  gallery_task_status?: string | null
  gallery_images?: GalleryImageItem[]
}

interface DraftSummary {
  id: string
  title: string
  status: string
  updatedAt: string
  scene: AvatarPurposeScene
}

const copywritingApiBaseUrl = (
  import.meta.env.VITE_REMIX_AGENT_API_BASE_URL
  ?? import.meta.env.VITE_AGENT_API_BASE_URL
  ?? 'http://localhost:8002'
).replace(/\/$/, '')

const route = useRoute()
const router = useRouter()

const normalizedSceneCodePurposeMap: Record<string, AvatarPurposeScene> = {
  talk: '口播数字人',
  sales: '卖货数字人',
  product: '产品介绍数字人',
  model: '模特数字人',
  clip: '视频剪辑数字人',
}

const normalizedPurposeSceneRouteMap: Record<AvatarPurposeScene, string> = {
  '口播数字人': '/content-creation/digital-human/talk',
  '卖货数字人': '/content-creation/digital-human/sales',
  '产品介绍数字人': '/content-creation/digital-human/product',
  '模特数字人': '/content-creation/digital-human/model',
  '视频剪辑数字人': '/content-creation/digital-human/clip',
}

const sceneCodePurposeMap: Record<string, AvatarPurposeScene> = {
  talk: '口播数字人',
  sales: '卖货数字人',
  product: '产品介绍数字人',
  model: '模特数字人',
  clip: '视频剪辑数字人',
}

const purposeSceneRouteMap: Record<AvatarPurposeScene, string> = {
  '口播数字人': '/content-creation/digital-human/talk',
  '卖货数字人': '/content-creation/digital-human/sales',
  '产品介绍数字人': '/content-creation/digital-human/product',
  '模特数字人': '/content-creation/digital-human/model',
  '视频剪辑数字人': '/content-creation/digital-human/clip',
}

const imageCountOptions = [4, 5, 6, 8, 10, 12]
const aspectRatioOptions = ['1:1', '3:4', '9:16']

const productKeyword = ref('')
const productsLoading = ref(false)
const productList = ref<BrandProductCard[]>([])
const selectedProductId = ref('')
const selectedProductProfile = ref<BrandProfile | null>(null)
const productAssets = ref<VisualAssetItem[]>([])
const selectedWhiteImageId = ref('')
const selectedWearImageId = ref('')
const productAssetPickerKind = ref<'white' | 'wear' | null>(null)

const modelImageInput = ref<HTMLInputElement | null>(null)
const modelImageUploading = ref(false)
const modelImageUrl = ref('')

const sceneImageInput = ref<HTMLInputElement | null>(null)
const sceneImageUploading = ref(false)
const sceneImageUrl = ref('')

const draftId = ref('')
const draftLibraryLoading = ref(false)
const showDraftLibrary = ref(false)
const draftLibraryItems = ref<AvatarDraftIndexRead[]>([])
const hydratingDraft = ref(false)
const currentMode = ref<'manual' | 'auto' | 'batch'>('manual')
const showModeMenu = ref(false)
const switchingScene = ref(false)
const videoPurposeScene = ref<AvatarPurposeScene>('模特数字人')
videoPurposeScene.value = '模特数字人'
let draftSaveTimer: ReturnType<typeof setTimeout> | null = null

const imageCount = ref(8)
const aspectRatio = ref('3:4')
const extraRequirements = ref('')
const suggestingRequirements = ref(false)
const galleryGenerating = ref(false)
const galleryTaskId = ref('')
const galleryTaskStatus = ref('')
const galleryImages = ref<GalleryImageItem[]>([])
const previewImage = ref<GalleryImageItem | null>(null)
const galleryPollErrorCount = ref(0)
let galleryPollTimer: ReturnType<typeof setTimeout> | null = null
const finalizedGalleryTaskNo = ref('')

const productImageAssets = computed(() => productAssets.value.filter((item) => item.assetType !== 'video'))
const selectedWhiteAsset = computed(() => productAssets.value.find((item) => item.id === selectedWhiteImageId.value) || null)
const selectedWearAsset = computed(() => productAssets.value.find((item) => item.id === selectedWearImageId.value) || null)
const galleryTaskStatusLabel = computed(() => {
  if (galleryTaskStatus.value.startsWith('QUERY_RETRY_')) return '查询重试中...'
  return galleryTaskStatus.value || '待生成'
})
const visibleGalleryImages = computed(() => normalizeGalleryImages(galleryImages.value))
const draftSummaries = computed<DraftSummary[]>(() => (
  draftLibraryItems.value.map((item) => ({
    id: item.draft_id,
    title: item.title || '未命名草稿',
    status: item.status,
    updatedAt: item.updated_at,
    scene: sceneCodeToPurposeScene(item.scene_code),
  }))
))
const currentSceneDraftCount = computed(() => (
  draftLibraryItems.value.length
))
const currentModeLabel = computed(() => {
  if (currentMode.value === 'manual') return '手动模式'
  if (currentMode.value === 'auto') return '自动模式'
  return '批量模式'
})
const draftTitle = computed(() => {
  const productName = selectedProductProfile.value?.productName?.trim()
  if (productName) return `${productName} - ${videoPurposeScene.value}`
  return '模特数字人草稿'
})

function isValidPurposeScene(value: string): value is AvatarPurposeScene {
  return value in normalizedPurposeSceneRouteMap
}

function sceneCodeToPurposeScene(sceneCode?: string | null): AvatarPurposeScene {
  const scene = sceneCode ? normalizedSceneCodePurposeMap[sceneCode] : null
  if (scene && isValidPurposeScene(scene)) {
    return scene
  }
  return '模特数字人'
  return scene && isValidPurposeScene(scene) ? scene : '模特数字人'
}

async function ensureDraftSceneMatchesCurrentPage(id: string) {
  const summary = await request<AvatarDraftIndexRead>(`/api/v1/avatar-drafts/${id}`)
  const draftScene = sceneCodeToPurposeScene(summary.scene_code)
  if (draftScene === '模特数字人') {
    return true
  }
  await router.replace({
    path: normalizedPurposeSceneRouteMap[draftScene],
    query: {
      ...route.query,
      draftId: id,
    },
  })
  return false
  if (draftScene === '模特数字人') {
    return true
  }

  await router.replace({
    path: purposeSceneRouteMap[draftScene],
    query: {
      ...route.query,
      draftId: id,
    },
  })
  return false
}

function getDraftPurposeScene(draft: CreationDraftRead): AvatarPurposeScene {
  const digitalParams = draft.digital_human_params || {}
  const scene = String(
    digitalParams.video_purpose
    || draft.content_info?.purpose_scene
    || '模特数字人',
  )
  return isValidPurposeScene(scene) ? scene : '模特数字人'
}

function buildHeaders() {
  const headers = new Headers({ 'Content-Type': 'application/json' })
  const token = authStore.state.session?.accessToken
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return headers
}

async function parseJsonSafely(response: Response) {
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) return null
  return response.json()
}

function formatDraftTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return `${date.getMonth() + 1}-${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

async function loadProducts() {
  productsLoading.value = true
  try {
    const data = await listBrandProducts({ keyword: productKeyword.value, pageNo: 1, pageSize: 100 })
    productList.value = data.list
  } finally {
    productsLoading.value = false
  }
}

async function selectProduct(brandId: string) {
  if (!brandId) {
    selectedProductId.value = ''
    selectedProductProfile.value = null
    productAssets.value = []
    selectedWhiteImageId.value = ''
    selectedWearImageId.value = ''
    return
  }
  selectedProductId.value = brandId
  selectedProductProfile.value = await getBrandProfile(brandId)
  productAssets.value = await getVisualAssets(brandId)
  const firstImage = productImageAssets.value[0]
  selectedWhiteImageId.value = firstImage?.id || ''
  selectedWearImageId.value = productImageAssets.value[1]?.id || firstImage?.id || ''
  scheduleDraftSave()
}

async function handleProductChange() {
  await selectProduct(selectedProductId.value)
}

function selectWhiteAsset(id: string) {
  selectedWhiteImageId.value = id
  scheduleDraftSave()
}

function selectWearAsset(id: string) {
  selectedWearImageId.value = id
  scheduleDraftSave()
}

function openProductAssetPicker(kind: 'white' | 'wear') {
  productAssetPickerKind.value = kind
}

function closeProductAssetPicker() {
  productAssetPickerKind.value = null
}

function confirmProductAssetPick(id: string) {
  if (productAssetPickerKind.value === 'white') selectWhiteAsset(id)
  else if (productAssetPickerKind.value === 'wear') selectWearAsset(id)
  closeProductAssetPicker()
}

function openModelImageUpload() {
  if (modelImageUploading.value) return
  modelImageInput.value?.click()
}

function openSceneImageUpload() {
  if (sceneImageUploading.value) return
  sceneImageInput.value?.click()
}

async function uploadFileToObjectStorage(file: File, moduleName: string, mediaType: string, currentDraftId?: string) {
  const ticket = await request<UploadTicketRead>('/api/v1/uploads/ticket', {
    method: 'POST',
    body: {
      module: moduleName,
      file_name: file.name,
      content_type: file.type || 'application/octet-stream',
      media_type: mediaType,
      draft_id: currentDraftId || draftId.value || undefined,
    },
  })
  const response = await fetch(ticket.upload_url, {
    method: 'PUT',
    headers: {
      'Content-Type': file.type || 'application/octet-stream',
    },
    body: file,
  })
  if (!response.ok) throw new Error('文件上传失败')
  return ticket.file_url
}

function inferImageExtension(contentType: string, fallbackUrl: string) {
  const normalizedType = contentType.toLowerCase()
  if (normalizedType.includes('png')) return 'png'
  if (normalizedType.includes('webp')) return 'webp'
  if (normalizedType.includes('jpeg') || normalizedType.includes('jpg')) return 'jpg'
  const urlWithoutQuery = fallbackUrl.split('?')[0] || ''
  const matched = urlWithoutQuery.match(/\.([a-zA-Z0-9]+)$/)
  return matched?.[1]?.toLowerCase() || 'png'
}

async function persistRemoteGalleryImage(image: GalleryImageItem, index: number) {
  const response = await fetch(image.url)
  if (!response.ok) {
    throw new Error(`第 ${index + 1} 张图片下载失败`)
  }
  const blob = await response.blob()
  const extension = inferImageExtension(blob.type || response.headers.get('content-type') || '', image.url)
  const file = new File([blob], `model-gallery-${Date.now()}-${index + 1}.${extension}`, {
    type: blob.type || 'image/png',
  })
  const persistedUrl = await uploadFileToObjectStorage(file, 'digital_human', 'image', draftId.value)
  return {
    ...image,
    url: persistedUrl,
    source_url: image.url,
    persisted: true,
  } as GalleryImageItem
}

async function persistGalleryImages(items: GalleryImageItem[]) {
  const persistedItems: GalleryImageItem[] = []
  for (let index = 0; index < items.length; index += 1) {
    const item = items[index]
    if (item.persisted) {
      persistedItems.push(item)
      continue
    }
    persistedItems.push(await persistRemoteGalleryImage(item, index))
  }
  return persistedItems
}

function normalizeGalleryImages(items: GalleryImageItem[], expectedCount: number = Number(imageCount.value) || 0) {
  const cleaned = items.filter((item) => Boolean(item?.url))
  if (expectedCount > 0 && cleaned.length > expectedCount) {
    return cleaned.slice(0, expectedCount)
  }
  return cleaned
}

function findMatchingGalleryTask() {
  const byTaskNo = galleryTaskId.value.trim()
  const byDraftId = draftId.value.trim()
  return (
    taskStore.findTask(byTaskNo)
    || [...taskStore.activeTasks, ...taskStore.recentTasks].find((task) => (
      task.taskDomain === 'avatar_gallery'
      && Boolean(byDraftId)
      && task.draftId === byDraftId
    ))
    || null
  )
}

async function finalizeGalleryTask(task: AsyncTask) {
  if (task.status !== 'completed' || finalizedGalleryTaskNo.value === task.taskNo) {
    return
  }
  const items = normalizeGalleryImages((task.resultUrls || []).map((url) => ({ url, output_type: 'image' })))
  if (!items.length) {
    return
  }
  finalizedGalleryTaskNo.value = task.taskNo
  try {
    galleryImages.value = normalizeGalleryImages(await persistGalleryImages(items))
    galleryTaskId.value = task.taskNo
    galleryTaskStatus.value = task.taskStatus || 'SUCCEEDED'
    galleryGenerating.value = false
    await saveDraftNow()
  } catch (error) {
    finalizedGalleryTaskNo.value = ''
    console.error('Failed to finalize gallery task', error)
  }
}

function syncGalleryTaskState() {
  const task = findMatchingGalleryTask()
  if (!task || task.taskDomain !== 'avatar_gallery') return

  galleryTaskId.value = task.taskNo

  if (task.status === 'running') {
    galleryGenerating.value = true
    if (task.taskStatus) {
      galleryTaskStatus.value = task.taskStatus
    }
    return
  }

  if (task.status === 'failed') {
    galleryGenerating.value = false
    galleryTaskStatus.value = task.taskStatus || 'FAILED'
    return
  }

  void finalizeGalleryTask(task)
}

async function handleImageUpload(
  event: Event,
  setter: typeof modelImageUrl,
  uploading: typeof modelImageUploading,
  errorMessage: string,
) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    window.alert('请上传图片文件')
    return
  }
  uploading.value = true
  try {
    setter.value = await uploadFileToObjectStorage(file, 'digital_human', 'image')
    scheduleDraftSave()
  } catch (error) {
    window.alert(error instanceof Error ? error.message : errorMessage)
  } finally {
    uploading.value = false
  }
}

async function handleModelImageChange(event: Event) {
  await handleImageUpload(event, modelImageUrl, modelImageUploading, '数字人图片上传失败')
}

async function handleSceneImageChange(event: Event) {
  await handleImageUpload(event, sceneImageUrl, sceneImageUploading, '场景图上传失败')
}

async function handleSuggestRequirements() {
  if (!selectedProductProfile.value || !selectedWhiteAsset.value || !selectedWearAsset.value || !modelImageUrl.value) {
    window.alert('请先完成产品选择、白底图/佩戴图选择和数字人图上传')
    return
  }
  suggestingRequirements.value = true
  try {
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/digital-human/model-image-gallery/suggest-requirements`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({
        product_name: selectedProductProfile.value.productName,
        brand_name: selectedProductProfile.value.brandName,
        product_white_image_url: selectedWhiteAsset.value.assetUrl,
        product_wear_image_url: selectedWearAsset.value.assetUrl,
        model_image_url: modelImageUrl.value,
        scene_image_url: sceneImageUrl.value || null,
        image_count: imageCount.value,
      }),
    })
    const data = await parseJsonSafely(response) as { requirement_text?: string; detail?: string } | null
    if (!response.ok) {
      throw new Error(typeof data?.detail === 'string' ? data.detail : '自动生成要求失败')
    }
    extraRequirements.value = String(data?.requirement_text || '')
    scheduleDraftSave()
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '自动生成要求失败')
  } finally {
    suggestingRequirements.value = false
  }
}

function buildPersistedModelState(): ModelScenePersistedState {
  return {
    selected_product_id: selectedProductId.value || null,
    selected_product_profile: selectedProductProfile.value,
    product_assets: productAssets.value,
    selected_white_image_id: selectedWhiteImageId.value || null,
    selected_wear_image_id: selectedWearImageId.value || null,
    model_image_url: modelImageUrl.value || null,
    scene_image_url: sceneImageUrl.value || null,
    image_count: imageCount.value,
    aspect_ratio: aspectRatio.value,
    extra_requirements: extraRequirements.value.trim() || null,
    gallery_task_id: galleryTaskId.value || null,
    gallery_task_status: galleryTaskStatus.value || null,
    gallery_images: visibleGalleryImages.value,
  }
}

function buildDraftPayload(sceneOverride: AvatarPurposeScene = videoPurposeScene.value) {
  void sceneOverride
  return {
    title: draftTitle.value,
    product_keyword: productKeyword.value.trim() || null,
    selected_product_id: selectedProductId.value || null,
    selected_product_profile: selectedProductProfile.value || {},
    product_assets: productAssets.value,
    selected_white_image_id: selectedWhiteImageId.value || null,
    selected_wear_image_id: selectedWearImageId.value || null,
    model_image_url: modelImageUrl.value || null,
    scene_image_url: sceneImageUrl.value || null,
    image_count: imageCount.value,
    aspect_ratio: aspectRatio.value,
    extra_requirements: extraRequirements.value.trim() || null,
    gallery_task_id: galleryTaskId.value || null,
    gallery_task_status: galleryTaskStatus.value || null,
    gallery_images: visibleGalleryImages.value,
    status: visibleGalleryImages.value.length ? 'gallery_generated' : 'draft',
  }
  return {
    title: draftTitle.value,
    source_url: null,
    platform: null,
    content_id: selectedProductId.value || null,
    content_info: {
      purpose_scene: sceneOverride,
      product_keyword: productKeyword.value.trim() || null,
      product_assets: productAssets.value,
    },
    transcript: {},
    extracted_copy: null,
    rewrite_instruction: extraRequirements.value.trim() || null,
    rewritten_copy: null,
    voice_params: {},
    digital_human_params: {
      human_type: 'image',
      template: '模特数字人',
      scene: '模特场景',
      video_purpose: sceneOverride,
      image_url: modelImageUrl.value || null,
      video_url: null,
      generated_video_url: null,
      generated_video_source_url: null,
      task_id: galleryTaskId.value || null,
      task_status: galleryTaskStatus.value || null,
      model_scene: buildPersistedModelState(),
    },
    clip_params: {},
    status: visibleGalleryImages.value.length ? 'gallery_generated' : 'draft',
  }
}

function hasPersistableContent() {
  return Boolean(
    selectedProductId.value
    || modelImageUrl.value
    || sceneImageUrl.value
    || extraRequirements.value.trim()
    || visibleGalleryImages.value.length
    || draftId.value,
  )
}

async function syncDraftRoute(id: string) {
  if (!id || route.query.draftId === id) return
  await router.replace({
    query: {
      ...route.query,
      draftId: id,
    },
  })
}

async function saveDraftNow(sceneOverride: AvatarPurposeScene = videoPurposeScene.value) {
  if (hydratingDraft.value || !hasPersistableContent()) return
  try {
    const payload = buildDraftPayload(sceneOverride)
    let saved: AvatarModelDraftRead
    if (draftId.value) {
      saved = await request<AvatarModelDraftRead>(`/api/v1/avatar-model-drafts/${draftId.value}`, {
        method: 'PATCH',
        body: payload,
      })
    } else {
      saved = await request<AvatarModelDraftRead>('/api/v1/avatar-model-drafts', {
        method: 'POST',
        body: payload,
      })
    }
    draftId.value = saved.draft_id
    await syncDraftRoute(saved.draft_id)
  } catch (error) {
    console.error('Failed to persist model draft', error)
  }
}

function scheduleDraftSave() {
  if (draftSaveTimer) clearTimeout(draftSaveTimer)
  draftSaveTimer = setTimeout(() => {
    void saveDraftNow()
  }, 500)
}

async function handleSceneSwitch(targetScene: AvatarPurposeScene, sourceScene: AvatarPurposeScene) {
  if (!targetScene || targetScene === sourceScene || switchingScene.value) return
  const targetPath = normalizedPurposeSceneRouteMap[targetScene]
  if (!targetPath) return

  switchingScene.value = true
  try {
    await router.push({
      path: targetPath,
      query: buildDraftlessQuery(route.query),
    })
  } catch (error) {
    videoPurposeScene.value = sourceScene
    console.error('Failed to switch model scene', error)
  } finally {
    switchingScene.value = false
  }
}

async function restoreProductContext(brandId: string, persistedState: ModelScenePersistedState) {
  if (!brandId) return
  if (!selectedProductProfile.value) {
    selectedProductProfile.value = await getBrandProfile(brandId)
  }
  if (Array.isArray(persistedState.product_assets) && persistedState.product_assets.length) {
    productAssets.value = persistedState.product_assets
    return
  }
  productAssets.value = await getVisualAssets(brandId)
}

async function applyDraftToView(draft: CreationDraftRead) {
  hydratingDraft.value = true
  try {
    if ('selected_product_id' in draft) {
      const modelDraft = draft as AvatarModelDraftRead
      const modelScene = {
        selected_product_id: modelDraft.selected_product_id,
        selected_product_profile: modelDraft.selected_product_profile as BrandProfile | null,
        product_assets: modelDraft.product_assets as VisualAssetItem[],
        selected_white_image_id: modelDraft.selected_white_image_id,
        selected_wear_image_id: modelDraft.selected_wear_image_id,
        model_image_url: modelDraft.model_image_url,
        scene_image_url: modelDraft.scene_image_url,
        image_count: modelDraft.image_count,
        aspect_ratio: modelDraft.aspect_ratio,
        extra_requirements: modelDraft.extra_requirements,
        gallery_task_id: modelDraft.gallery_task_id,
        gallery_task_status: modelDraft.gallery_task_status,
        gallery_images: modelDraft.gallery_images as GalleryImageItem[],
      } as ModelScenePersistedState

      draftId.value = modelDraft.draft_id
      productKeyword.value = String(modelDraft.product_keyword || '')
      videoPurposeScene.value = '模特数字人'
      selectedProductId.value = String(modelDraft.selected_product_id || '')
      selectedProductProfile.value = (modelDraft.selected_product_profile || null) as BrandProfile | null
      productAssets.value = Array.isArray(modelDraft.product_assets) ? (modelDraft.product_assets as VisualAssetItem[]) : []
      selectedWhiteImageId.value = String(modelDraft.selected_white_image_id || '')
      selectedWearImageId.value = String(modelDraft.selected_wear_image_id || '')
      modelImageUrl.value = String(modelDraft.model_image_url || '')
      sceneImageUrl.value = String(modelDraft.scene_image_url || '')
      imageCount.value = Number(modelDraft.image_count || 8)
      aspectRatio.value = String(modelDraft.aspect_ratio || '3:4')
      extraRequirements.value = String(modelDraft.extra_requirements || '')
      galleryTaskId.value = String(modelDraft.gallery_task_id || '')
      galleryTaskStatus.value = String(modelDraft.gallery_task_status || '')
      galleryImages.value = normalizeGalleryImages(
        Array.isArray(modelDraft.gallery_images) ? (modelDraft.gallery_images as GalleryImageItem[]) : [],
        Number(modelDraft.image_count || 0) || Number(imageCount.value) || 0,
      )
      if (selectedProductId.value) {
        await restoreProductContext(selectedProductId.value, modelScene)
      }
      return
    }

    draftId.value = draft.draft_id
    productKeyword.value = String(draft.content_info?.product_keyword || '')
    const digitalParams = draft.digital_human_params || {}
    const modelScene = (digitalParams.model_scene || {}) as ModelScenePersistedState

    videoPurposeScene.value = '模特数字人'
    selectedProductId.value = String(modelScene.selected_product_id || draft.content_id || '')
    selectedProductProfile.value = (modelScene.selected_product_profile || null) as BrandProfile | null
    productAssets.value = Array.isArray(modelScene.product_assets) ? modelScene.product_assets : []
    selectedWhiteImageId.value = String(modelScene.selected_white_image_id || '')
    selectedWearImageId.value = String(modelScene.selected_wear_image_id || '')
    modelImageUrl.value = String(modelScene.model_image_url || digitalParams.image_url || '')
    sceneImageUrl.value = String(modelScene.scene_image_url || '')
    imageCount.value = Number(modelScene.image_count || 8)
    aspectRatio.value = String(modelScene.aspect_ratio || '3:4')
    extraRequirements.value = String(modelScene.extra_requirements || draft.rewrite_instruction || '')
    galleryTaskId.value = String(modelScene.gallery_task_id || '')
    galleryTaskStatus.value = String(modelScene.gallery_task_status || '')
    galleryImages.value = normalizeGalleryImages(
      Array.isArray(modelScene.gallery_images) ? modelScene.gallery_images : [],
      Number(modelScene.image_count || 0) || Number(imageCount.value) || 0,
    )

    if (selectedProductId.value) {
      await restoreProductContext(selectedProductId.value, modelScene)
    }
  } finally {
    hydratingDraft.value = false
  }
}

async function loadDraft(id: string) {
  const matched = await ensureDraftSceneMatchesCurrentPage(id)
  if (!matched) return
  const draft = await request<AvatarModelDraftRead>(`/api/v1/avatar-model-drafts/${id}`)
  await applyDraftToView(draft)
}

async function loadDraftLibrary() {
  draftLibraryLoading.value = true
  try {
    const data = await request<AvatarDraftIndexListResponse>('/api/v1/avatar-drafts?scene=model&limit=20&offset=0')
    draftLibraryItems.value = data.items || []
  } finally {
    draftLibraryLoading.value = false
  }
}

function openDraftLibrary() {
  showDraftLibrary.value = true
  void loadDraftLibrary()
}

function closeDraftLibrary() {
  showDraftLibrary.value = false
}

function toggleModeMenu() {
  showModeMenu.value = !showModeMenu.value
}

function selectMode(mode: 'manual' | 'auto' | 'batch') {
  currentMode.value = mode
  showModeMenu.value = false
}

async function handleSelectDraft(id: string, scene?: AvatarPurposeScene) {
  const targetScene = scene || '模特数字人'
  const targetPath = purposeSceneRouteMap[targetScene]
  if (targetPath && route.path !== targetPath) {
    closeDraftLibrary()
    await router.push({
      path: targetPath,
      query: {
        ...route.query,
        draftId: id,
      },
    })
    return
  }
  await loadDraft(id)
  closeDraftLibrary()
}

async function handleDeleteDraft(id: string) {
  if (!window.confirm('确定删除这条草稿吗？')) return
  await request(`/api/v1/avatar-model-drafts/${id}`, { method: 'DELETE' })
  if (draftId.value === id) {
    await handleCreateNewContent()
  } else {
    await loadDraftLibrary()
  }
}

async function handleCreateNewContent() {
  hydratingDraft.value = true
  try {
    draftId.value = ''
    productKeyword.value = ''
    selectedProductId.value = ''
    selectedProductProfile.value = null
    productAssets.value = []
    selectedWhiteImageId.value = ''
    selectedWearImageId.value = ''
    modelImageUrl.value = ''
    sceneImageUrl.value = ''
    imageCount.value = 8
    aspectRatio.value = '3:4'
    extraRequirements.value = ''
    galleryTaskId.value = ''
    galleryTaskStatus.value = ''
    galleryImages.value = []
    previewImage.value = null
    galleryPollErrorCount.value = 0
    videoPurposeScene.value = '模特数字人'

    if (route.query.draftId) {
      await router.replace({ query: buildDraftlessQuery(route.query) })
    }
  } finally {
    hydratingDraft.value = false
  }
  await loadDraftLibrary()
  closeDraftLibrary()
}

function stopGalleryPolling() {
  if (galleryPollTimer) {
    clearTimeout(galleryPollTimer)
    galleryPollTimer = null
  }
}

function openImagePreview(image: GalleryImageItem) {
  previewImage.value = image
}

function closeImagePreview() {
  previewImage.value = null
}

async function downloadGalleryImage(image: GalleryImageItem, index = 0) {
  try {
    const response = await fetch(image.url)
    if (!response.ok) {
      throw new Error('图片下载失败')
    }
    const blob = await response.blob()
    const extension = inferImageExtension(blob.type || response.headers.get('content-type') || '', image.url)
    const objectUrl = window.URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = `${draftTitle.value || 'model-gallery'}-${index + 1}.${extension}`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    window.URL.revokeObjectURL(objectUrl)
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '图片下载失败')
  }
}

async function pollRunningHubTask(taskId: string) {
  const response = await fetch(`${copywritingApiBaseUrl}/api/v1/digital-human/runninghub/tasks/${taskId}`, {
    method: 'POST',
    headers: buildHeaders(),
  })
  const data = (await parseJsonSafely(response)) as DigitalHumanTaskResponse | { detail?: string } | null
  if (!response.ok) {
    const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : '任务查询失败'
    throw new Error(typeof detail === 'string' ? detail : '任务查询失败')
  }

  const output = data?.output || {}
  const status = String(output.task_status || '')
  galleryTaskStatus.value = status

  const rawResults = output.results
  const results = Array.isArray(rawResults) ? rawResults : rawResults ? [rawResults] : []
  const items = normalizeGalleryImages(results
    .map((item) => ({
      url: String(item.url || item.video_url || ''),
      output_type: String(item.output_type || ''),
    }))
    .filter((item) => item.url && !['mp4', 'mov', 'webm', 'mkv'].includes(item.output_type.toLowerCase()))
  )

  if (['SUCCESS', 'SUCCEEDED'].includes(status.toUpperCase())) {
    galleryImages.value = normalizeGalleryImages(await persistGalleryImages(items))
    galleryGenerating.value = false
    await saveDraftNow()
    return
  }

  if (['FAILED', 'CANCELED', 'CANCELLED'].includes(status.toUpperCase())) {
    throw new Error(`任务失败: ${status}`)
  }

  galleryPollTimer = setTimeout(() => {
    void pollGalleryTask(taskId)
  }, 5000)
}

async function generateGallery() {
  if (!selectedProductProfile.value || !selectedWhiteAsset.value || !selectedWearAsset.value || !modelImageUrl.value) {
    window.alert('请先完成产品选择、产品图选择和数字人图上传')
    return
  }

  galleryGenerating.value = true
  galleryImages.value = []
  previewImage.value = null
  galleryPollErrorCount.value = 0

  try {
    await saveDraftNow()
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/digital-human/model-image-gallery/submit`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({
        product_name: selectedProductProfile.value.productName,
        product_white_image_url: selectedWhiteAsset.value.assetUrl,
        product_wear_image_url: selectedWearAsset.value.assetUrl,
        model_image_url: modelImageUrl.value,
        scene_image_url: sceneImageUrl.value || null,
        image_count: imageCount.value,
        aspect_ratio: aspectRatio.value,
        extra_requirements: extraRequirements.value.trim() || null,
      }),
    })
    const data = await parseJsonSafely(response) as { job?: { output?: { task_id?: string; task_status?: string } }; detail?: string } | null
    if (!response.ok) {
      throw new Error(typeof data?.detail === 'string' ? data.detail : '展示图任务创建失败')
    }
    galleryTaskId.value = String(data?.job?.output?.task_id || '')
    galleryTaskStatus.value = String(data?.job?.output?.task_status || 'RUNNING')
    if (!galleryTaskId.value) throw new Error('未返回 task_id')
    finalizedGalleryTaskNo.value = ''
    await saveDraftNow()
    taskStore.addTask({
      taskNo: galleryTaskId.value,
      keyword: draftTitle.value,
      platformCode: 'digital_human',
      taskKind: 'avatar_gallery',
      taskDomain: 'avatar_gallery',
      draftId: draftId.value,
      sourceRoutePath: route.path,
      hideWhileOnSource: true,
      purposeScene: videoPurposeScene.value,
      humanType: 'image',
      title: draftTitle.value,
      taskStatus: galleryTaskStatus.value,
    })
  } catch (error) {
    galleryGenerating.value = false
    window.alert(error instanceof Error ? error.message : '展示图生成失败')
  }
}

async function pollGalleryTask(taskId: string) {
  try {
    await pollRunningHubTask(taskId)
    galleryPollErrorCount.value = 0
  } catch (error) {
    galleryPollErrorCount.value += 1
    if (galleryPollErrorCount.value <= 3) {
      galleryTaskStatus.value = `QUERY_RETRY_${galleryPollErrorCount.value}`
      galleryPollTimer = setTimeout(() => {
        void pollGalleryTask(taskId)
      }, 5000)
      return
    }
    galleryGenerating.value = false
    window.alert(error instanceof Error ? error.message : '展示图任务查询失败')
  }
}

onMounted(() => {
  void loadProducts()
  void loadDraftLibrary()
  const rawDraftId = route.query.draftId
  if (typeof rawDraftId === 'string' && rawDraftId.trim()) {
    void loadDraft(rawDraftId.trim())
  }
  syncGalleryTaskState()
})

onBeforeUnmount(() => {
  stopGalleryPolling()
  if (draftSaveTimer) {
    clearTimeout(draftSaveTimer)
    draftSaveTimer = null
  }
})

watch(videoPurposeScene, async (scene, previous) => {
  if (!scene || !previous || scene === previous || hydratingDraft.value || switchingScene.value) return
  await handleSceneSwitch(scene, previous)
})

watch(
  () => [
    draftId.value,
    galleryTaskId.value,
    taskStore.activeTasks.map((task) => `${task.taskNo}:${task.status}:${task.taskStatus}`).join('|'),
    taskStore.recentTasks.map((task) => `${task.taskNo}:${task.status}:${task.taskStatus}`).join('|'),
  ],
  () => {
    syncGalleryTaskState()
  },
)

watch(
  [
    productKeyword,
    selectedProductId,
    selectedWhiteImageId,
    selectedWearImageId,
    modelImageUrl,
    sceneImageUrl,
    imageCount,
    aspectRatio,
    extraRequirements,
    galleryTaskStatus,
    () => galleryImages.value.map((item) => item.url).join('|'),
  ],
  () => {
    if (!hydratingDraft.value) {
      scheduleDraftSave()
    }
  },
)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 0 rgba(148, 163, 184, 0.08);
  margin: -24px -24px 0;
  padding: 16px 28px 15px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.page-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: #64748b;
}

.draft-library-button,
.mode-switch-button,
.header-purpose-select {
  min-height: 38px;
  border-radius: 999px;
  border: 1px solid #bfdbfe;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 700;
}

.draft-library-button,
.mode-switch-button {
  background: #fff;
  color: #2563eb;
  cursor: pointer;
}

.header-purpose-select {
  background: #eff6ff;
  color: #1d4ed8;
  outline: none;
}

.mode-switch {
  position: relative;
}

.mode-switch-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  min-width: 120px;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: #fff;
  padding: 8px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.12);
}

.mode-switch-item {
  min-height: 36px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: #334155;
  text-align: left;
  padding: 0 12px;
  cursor: pointer;
}

.mode-switch-item.active {
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.mode-switch-item:disabled {
  color: #94a3b8;
  cursor: not-allowed;
}

.grid-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(360px, 1fr));
  gap: 22px;
  align-items: start;
}

.flow-column,
.preview-column {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.panel-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-radius: 26px;
  border: 1px solid #dbeafe;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  padding: 20px;
  box-shadow: 0 10px 28px rgba(148, 163, 184, 0.08);
}

.panel-head,
.panel-subhead {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.panel-head h2 {
  margin: 8px 0 0;
  font-size: 18px;
  line-height: 1.2;
  color: #0f172a;
}

.panel-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.text-link,
.primary-button {
  border: 0;
  font-weight: 700;
  cursor: pointer;
}

.text-link {
  min-height: 36px;
  border-radius: 14px;
  padding: 0 12px;
  background: transparent;
  color: #2563eb;
}

.primary-button {
  min-height: 44px;
  border-radius: 16px;
  padding: 0 18px;
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: #fff;
}

.section-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-label {
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748b;
}

.field-hint {
  margin: 2px 0 0;
  font-size: 12px;
  color: #64748b;
}

.field-input,
.field-area {
  width: 100%;
  border-radius: 18px;
  border: 1px solid #dbeafe;
  background: #fff;
  color: #0f172a;
}

.field-input {
  min-height: 46px;
  padding: 0 16px;
  font-size: 14px;
  outline: none;
}

.field-area {
  resize: vertical;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.75;
  outline: none;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 20px;
  border: 1px solid #dbeafe;
  background: rgba(255, 255, 255, 0.92);
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #22c55e;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 0.7fr);
  gap: 12px;
}

.count-card,
.summary-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  border-radius: 18px;
  border: 1px solid #dbeafe;
  background: #fff;
  padding: 14px 16px;
}

.count-card span,
.summary-card span {
  font-size: 12px;
  color: #64748b;
}

.count-card strong,
.summary-card strong {
  font-size: 14px;
  color: #0f172a;
}

.mini-grid,
.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.upload-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  border-radius: 24px;
  border: 1px dashed rgba(59, 130, 246, 0.3);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(239, 246, 255, 0.82));
  text-align: center;
  padding: 24px;
}

.preview-image {
  width: auto;
  max-width: 100%;
  max-height: 360px;
  object-fit: contain;
  border-radius: 18px;
}

.empty-icon {
  font-size: 38px;
  color: rgba(37, 99, 235, 0.65);
}

.asset-grid,
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.asset-card,
.gallery-image-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid #dbeafe;
  border-radius: 18px;
  background: #fff;
  padding: 10px;
  text-align: left;
  cursor: pointer;
}

.gallery-image-button {
  display: block;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.asset-card.active {
  border-color: rgba(59, 130, 246, 0.42);
  box-shadow: 0 12px 20px rgba(37, 99, 235, 0.08);
}

.asset-card-image,
.gallery-image {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 12px;
  background: #e2e8f0;
}

.gallery-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.gallery-card-label {
  font-size: 12px;
  color: #64748b;
}

.gallery-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.secondary-button {
  min-height: 34px;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  padding: 0 12px;
  font-size: 12px;
  cursor: pointer;
}

.empty-gallery {
  padding: 32px 20px;
  border-radius: 18px;
  border: 1px dashed #bfdbfe;
  color: #64748b;
  text-align: center;
}

.product-asset-mini {
  align-items: stretch;
}

.product-asset-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.product-asset-picker-trigger {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  text-align: left;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: #fff;
  padding: 10px 12px;
  cursor: pointer;
  color: #0f172a;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.product-asset-picker-trigger:hover {
  border-color: rgba(59, 130, 246, 0.35);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.06);
}

.product-asset-picker-thumb {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 12px;
  overflow: hidden;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-asset-picker-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-asset-picker-placeholder {
  font-size: 26px;
  color: #94a3b8;
}

.product-asset-picker-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.product-asset-picker-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.product-asset-picker-sub {
  font-size: 12px;
  color: #64748b;
}

.product-asset-picker-chevron {
  flex-shrink: 0;
  font-size: 22px;
  color: #94a3b8;
}

.product-asset-picker-dialog {
  width: min(560px, 100%);
}

.product-asset-picker-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 10px;
  max-height: min(52vh, 420px);
  overflow: auto;
  padding: 16px 20px 20px;
}

.product-asset-picker-option {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: #fff;
  cursor: pointer;
  text-align: center;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.product-asset-picker-option:hover {
  border-color: rgba(59, 130, 246, 0.35);
}

.product-asset-picker-option.active {
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.1);
}

.product-asset-picker-option img {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 10px;
  background: #e2e8f0;
}

.product-asset-picker-tag {
  font-size: 11px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.draft-library-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.42);
  padding: 24px;
}

.draft-library-dialog {
  width: min(720px, 100%);
  max-height: min(70vh, 760px);
  overflow: hidden;
  border-radius: 24px;
  border: 1px solid #dbeafe;
  background: #fff;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.18);
}

.draft-library-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 20px 14px;
  border-bottom: 1px solid #e2e8f0;
}

.draft-library-head h3 {
  margin: 0;
  font-size: 18px;
}

.draft-library-head p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #64748b;
}

.draft-library-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.draft-library-secondary,
.draft-library-close {
  min-height: 38px;
  border-radius: 12px;
  padding: 0 14px;
  cursor: pointer;
}

.draft-library-secondary {
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

.draft-library-close {
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
}

.draft-library-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: calc(70vh - 96px);
  overflow: auto;
  padding: 16px 20px 20px;
}

.draft-library-item {
  display: flex;
  align-items: stretch;
  gap: 10px;
}

.draft-library-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  flex: 1;
  border: 1px solid #dbeafe;
  border-radius: 18px;
  padding: 14px 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  color: #334155;
  text-align: left;
  cursor: pointer;
}

.draft-library-main strong {
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.draft-library-main span {
  font-size: 12px;
  color: #64748b;
}

.draft-library-delete {
  min-width: 72px;
  border: 1px solid #fecaca;
  border-radius: 18px;
  background: #fff5f5;
  color: #dc2626;
  cursor: pointer;
}

.draft-library-empty {
  padding: 28px 20px;
  font-size: 14px;
  color: #64748b;
}

.image-preview-dialog {
  width: min(1080px, 100%);
  max-height: min(88vh, 980px);
  overflow: hidden;
  border-radius: 24px;
  border: 1px solid #dbeafe;
  background: #fff;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.18);
}

.image-preview-body {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: #f8fafc;
  max-height: calc(88vh - 88px);
}

.image-preview-full {
  width: auto;
  max-width: 100%;
  max-height: calc(88vh - 128px);
  object-fit: contain;
  border-radius: 18px;
  background: #e2e8f0;
}

@media (max-width: 1200px) {
  .grid-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .toolbar-grid,
  .mini-grid,
  .summary-grid,
  .asset-grid,
  .gallery-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
