<template>
  <div class="clip-scroll-page bg-slate-50 p-6 font-sans text-slate-800">
    <div class="mx-auto flex w-full max-w-[1600px] flex-col gap-5">
      <section class="page-header">
        <div>
          <h1 class="page-title">视频剪辑数字人</h1>
          <p v-if="!reviewMode" class="page-subtitle">选择产品，进入审核，执行剪辑后回到预览。</p>
        </div>

        <div class="header-actions">
          <template v-if="!reviewMode">
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
            <div class="draft-badge">
              <select v-model="selectedScene" class="header-purpose-select">
                <option value="口播数字人">口播数字人</option>
                <option value="卖货数字人">卖货数字人</option>
                <option value="产品介绍数字人">产品介绍数字人</option>
                <option value="模特数字人">模特数字人</option>
                <option value="视频剪辑数字人">视频剪辑数字人</option>
              </select>
            </div>
          </template>
        </div>
      </section>

      <section v-if="reviewMode" class="review-frame-shell">
        <iframe
          ref="reviewFrame"
          class="review-frame"
          :srcdoc="reviewSrcdoc"
          title="视频审核工作台"
          @load="handleReviewFrameLoad"
        />
      </section>

      <div v-else class="grid-layout">
        <div class="flow-column">
        <section class="panel-card panel-accent clip-step-product">
          <div class="panel-head">
            <div>
              <span class="panel-step">01</span>
              <h2>选择产品</h2>
            </div>
            <span class="panel-tag">主控区</span>
          </div>

          <label class="field-block">
            <span>品牌产品</span>
            <select v-model="selectedProductId" class="field-input" :disabled="productsLoading" @change="handleProductChange">
              <option value="">请选择已有产品</option>
              <option v-for="item in productOptions" :key="item.brandId" :value="item.brandId">
                {{ item.brandName }} - {{ item.productName }}
              </option>
            </select>
          </label>

          <div v-if="productsError" class="empty-state">{{ productsError }}</div>
          <div v-else-if="!productsLoading && !productOptions.length" class="empty-state">
            当前账号下还没有可用产品，请先去产品库创建。
          </div>

          <div class="section-head">
            <strong>视频素材</strong>
            <span>主视频 {{ selectedClipAssetId ? '1' : '0' }} / {{ videoAssets.length }}</span>
          </div>

          <div class="asset-grid">
            <button
              v-for="asset in videoAssets"
              :key="asset.id"
              type="button"
              class="asset-card"
              :class="{ active: selectedClipAssetId === asset.id }"
              @click="requestSelectClipAsset(asset.id)"
            >
              <video :src="asset.assetUrl" muted playsinline preload="metadata" class="asset-media" />
              <div class="asset-meta">
                <strong>{{ `视频素材 ${asset.id}` }}</strong>
                <span>{{ asset.assetType }}</span>
              </div>
            </button>
            <div v-if="!videoAssets.length" class="empty-state">当前产品还没有可用视频素材。</div>
          </div>

          <div class="step-footer">
            <div v-if="primaryVideoAsset" class="inline-summary">
              <span>主素材：</span>
              <strong>{{ `视频素材 ${primaryVideoAsset.id}` }}</strong>
            </div>
            <button class="primary-button full-width" type="button" :disabled="!canAnalyze || analysisLoading" @click="handleAnalyze">
              {{ analysisLoading ? '分析中...' : '进行剪辑' }}
            </button>
          </div>
        </section>
        </div>

        <div class="studio-column">
        <section class="panel-card clip-step-review">
          <div class="panel-head">
            <div>
              <span class="panel-step">02</span>
              <h2>审核摘要</h2>
            </div>
            <span class="panel-tag">摘要区</span>
          </div>

          <div v-if="!reviewUnits.length" class="empty-stage">
            <div class="empty-stage-icon">02</div>
            <strong>审核摘要</strong>
            <p>先在左侧选择产品和视频，并执行“进行剪辑”，这里再展示 AI 检测结果。</p>
          </div>

          <template v-else>
            <div class="summary-grid">
              <div class="summary-card">
                <span>总片段</span>
                <strong>{{ reviewUnits.length }}</strong>
              </div>
              <div class="summary-card">
                <span>AI 建议删减</span>
                <strong>{{ suggestedDeleteCount }}</strong>
              </div>
              <div class="summary-card">
                <span>静音片段</span>
                <strong>{{ silentGapCount }}</strong>
              </div>
              <div class="summary-card">
                <span>已选删除</span>
                <strong>{{ confirmedDeleteCount }}</strong>
              </div>
              <div class="summary-card">
                <span>预计删减时长</span>
                <strong>{{ deletedDurationLabel }}</strong>
              </div>
              <div class="summary-card">
                <span>状态</span>
                <strong>{{ clippedPreviewUrl ? '已生成成片' : '待审核' }}</strong>
              </div>
            </div>

            <div class="summary-actions">
              <button class="primary-button full-width" type="button" @click="openReviewAndSelfTestClip">
                审核并执行剪辑
              </button>
            </div>
          </template>
        </section>

        <section class="panel-card digital-human-card">
          <div class="panel-head">
            <div>
              <span class="panel-step">03</span>
              <h2>数字人形象</h2>
            </div>
            <div class="segmented-control">
              <button
                class="segmented-option"
                :class="{ active: avatarSourceMode === 'image' }"
                type="button"
                @click="avatarSourceMode = 'image'"
              >
                图片数字人
              </button>
              <button
                class="segmented-option"
                :class="{ active: avatarSourceMode === 'video' }"
                type="button"
                @click="avatarSourceMode = 'video'"
              >
                视频数字人
              </button>
            </div>
          </div>

          <div class="digital-human-body">
            <div class="digital-human-pane">
              <div class="pane-title">素材区</div>
              <label class="upload-dropzone" :style="avatarPreviewFrameStyle">
                <input
                  class="hidden"
                  type="file"
                  :accept="avatarSourceMode === 'image' ? 'image/*' : 'video/*'"
                  @change="handleClipAvatarUpload"
                />
                <template v-if="avatarSourceMode === 'image' && avatarImagePreviewUrl">
                  <img :src="avatarImagePreviewUrl" alt="数字人图片预览" class="avatar-upload-preview" />
                </template>
                <template v-else-if="avatarSourceMode === 'video' && avatarVideoPreviewUrl">
                  <video :src="avatarVideoPreviewUrl" muted playsinline controls class="avatar-upload-preview"></video>
                </template>
                <template v-else>
                  <span class="material-symbols-outlined upload-icon">upload</span>
                  <strong>{{ avatarSourceMode === 'image' ? '上传数字人图片' : '上传数字人视频' }}</strong>
                </template>
              </label>
            </div>

            <div class="digital-human-pane">
              <div class="pane-title">生成效果</div>
              <div class="digital-result-box" :style="avatarPreviewFrameStyle">
                <template v-if="generatedAvatarVideoUrl">
                  <video :src="generatedAvatarVideoUrl" playsinline controls class="avatar-result-preview"></video>
                </template>
                <template v-else-if="avatarSourceMode === 'image' && avatarImagePreviewUrl">
                  <img :src="avatarImagePreviewUrl" alt="数字人生成效果预览" class="avatar-result-preview" />
                </template>
                <template v-else-if="avatarSourceMode === 'video' && avatarVideoPreviewUrl">
                  <video :src="avatarVideoPreviewUrl" muted playsinline controls class="avatar-result-preview"></video>
                </template>
                <template v-else>
                  <span class="material-symbols-outlined upload-icon">person</span>
                  <strong>数字人形象预览</strong>
                </template>
              </div>
            </div>
          </div>

          <button
            class="primary-button full-width"
            type="button"
            :disabled="avatarUploading || generatingAvatarVideo"
            @click="handleGenerateClipAvatarVideo"
          >
            {{ avatarUploading ? '素材上传中...' : generatingAvatarVideo ? `生成中 ${avatarVideoTaskStatus || ''}` : '生成数字人视频' }}
          </button>
        </section>
        </div>

        <div class="preview-column">
        <section class="panel-card avatar-effect-card">
          <div class="panel-head">
            <div>
              <span class="panel-step">04</span>
              <h2>数字人效果</h2>
            </div>
          </div>

          <div class="avatar-effect-body">
            <div class="effect-controls">
              <div class="effect-row">
                <span class="effect-label">位置</span>
                <div class="effect-chip-row">
                  <button
                    v-for="item in avatarPositionOptions"
                    :key="item.value"
                    class="effect-chip"
                    :class="{ active: avatarOverlayPosition === item.value }"
                    type="button"
                    @click="avatarOverlayPosition = item.value"
                  >
                    {{ item.label }}
                  </button>
                </div>
              </div>

              <div class="effect-row">
                <span class="effect-label">大小</span>
                <div class="effect-slider-wrap">
                  <input v-model="avatarOverlaySize" class="effect-slider" type="range" min="20" max="50" />
                  <strong>{{ avatarOverlaySize }}%</strong>
                </div>
              </div>

              <div class="effect-row">
                <span class="effect-label">样式</span>
                <div class="effect-chip-row">
                  <button
                    v-for="item in avatarShapeOptions"
                    :key="item.value"
                    class="effect-chip"
                    :class="{ active: avatarOverlayShape === item.value }"
                    type="button"
                    @click="avatarOverlayShape = item.value"
                  >
                    {{ item.label }}
                  </button>
                </div>
              </div>

              <label class="effect-switch-row">
                <span>边框</span>
                <input v-model="avatarOverlayBorder" type="checkbox" />
              </label>
              <label class="effect-switch-row">
                <span>阴影</span>
                <input v-model="avatarOverlayShadow" type="checkbox" />
              </label>
              <label class="effect-switch-row">
                <span>底板</span>
                <input v-model="avatarOverlayPlate" type="checkbox" />
              </label>
            </div>

            <div class="layout-preview-pane">
              <div class="pane-title">布局预览</div>
              <div class="avatar-layout-preview" :style="layoutPreviewFrameStyle">
                <video
                  v-if="layoutBasePreviewUrl"
                  :src="layoutBasePreviewUrl"
                  class="avatar-layout-base"
                  muted
                  playsinline
                  loop
                  autoplay
                  @loadedmetadata="handleLayoutBaseMetadata"
                ></video>
                <div v-else class="avatar-layout-placeholder">底视频预览</div>
                <div
                  class="avatar-layout-pip"
                  :class="[`position-${avatarOverlayPosition}`, `shape-${avatarOverlayShape}`, {
                    bordered: avatarOverlayBorder,
                    shadowed: avatarOverlayShadow,
                    plated: avatarOverlayPlate,
                  }]"
                  :style="{ width: `${avatarOverlaySize}%` }"
                >
                  <video
                    v-if="layoutAvatarPreviewUrl"
                    :src="layoutAvatarPreviewUrl"
                    class="avatar-layout-video"
                    muted
                    playsinline
                    loop
                    autoplay
                  ></video>
                  <img
                    v-else-if="avatarImagePreviewUrl"
                    :src="avatarImagePreviewUrl"
                    class="avatar-layout-video"
                    alt="数字人布局预览"
                  />
                  <span v-else>数字人</span>
                </div>
              </div>
            </div>
          </div>

          <button
            class="primary-button full-width"
            type="button"
            :disabled="mergingAvatarClip"
            @click="handleGenerateMergedClip"
          >
            {{ mergingAvatarClip ? '融合生成中...' : '生成融合成片' }}
          </button>
        </section>

        <section ref="previewSection" class="panel-card preview-card">
          <div class="panel-head">
            <div>
              <span class="panel-step">05</span>
              <h2>预览</h2>
            </div>
            <span class="panel-tag">成片区</span>
          </div>

          <div class="preview-stage">
            <div class="preview-screen" :class="{ 'preview-screen-static': Boolean(previewVideoUrl) }">
              <template v-if="previewVideoUrl">
                <video
                  :src="previewVideoUrl"
                  controls
                  playsinline
                  class="preview-video"
                />
                <strong class="mt-3 text-[24px] font-semibold text-slate-800">剪辑预览</strong>
                <p class="mt-2 text-sm text-slate-500">
                  {{ clippedPreviewUrl ? '当前显示的是执行剪辑后的成片。' : '当前显示的是待剪原始素材，可继续执行审核剪辑。' }}
                </p>
              </template>
              <template v-else>
                <span class="material-symbols-outlined text-[46px] text-primary/70">play_circle</span>
                <strong class="mt-3 text-[24px] font-semibold text-slate-800">预览区域</strong>
                <p class="mt-2 text-sm text-slate-500">先完成素材选择并执行剪辑，这里会显示当前视频预览。</p>
              </template>
            </div>
          </div>

        </section>
        </div>
      </div>
    </div>

    <div v-if="showDraftLibrary" class="draft-library-mask" @click.self="closeDraftLibrary">
      <div class="draft-library-dialog">
        <div class="draft-library-head">
          <div>
            <h3>草稿箱</h3>
            <p>默认打开新草稿，你可以从这里回到之前的版本。</p>
          </div>
          <div class="draft-library-actions">
            <button class="draft-library-secondary" type="button" @click="handleCreateNewContent">新建内容</button>
            <button class="draft-library-close" type="button" @click="closeDraftLibrary">关闭</button>
          </div>
        </div>
        <div v-if="draftLibraryLoading" class="draft-library-empty">草稿加载中...</div>
        <div v-else-if="!draftLibraryItems.length" class="draft-library-empty">当前没有可恢复的草稿</div>
        <div v-else class="draft-library-list">
          <div v-for="item in draftSummaries" :key="item.id" class="draft-library-item">
            <button class="draft-library-main" type="button" @click="handleSelectDraft(item.id)">
              <strong>{{ item.title }}</strong>
              <span>{{ item.scene }}</span>
              <span>{{ formatDraftTime(item.updatedAt) }}</span>
              <span>{{ item.status }}</span>
            </button>
            <button
              class="draft-library-publish"
              type="button"
              @click="handlePublishDraft(item.id)"
            >
              上传
            </button>
            <button class="draft-library-delete" type="button" @click="handleDeleteDraft(item.id)">删除</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authStore } from '../auth/store'
import { getBrandProfile, getVisualAssets, listBrandProducts } from '../api/brandInjection'
import { getApiBaseUrl, request } from '../api/http'
import { taskStore } from '../data-collection/taskStore'
import { buildDraftlessQuery } from '../lib/avatarSceneNavigation'
import type { BrandProductCard, BrandProfile, VisualAssetItem } from '../types/brandInjection'
import reviewTemplateHtml from '../legacy/review-template.html?raw'

type SceneValue = '口播数字人' | '卖货数字人' | '产品介绍数字人' | '模特数字人' | '视频剪辑数字人'

interface ReviewUnit {
  id: string
  start: number
  end: number
  text: string
  isGap: boolean
  suggestedDelete: boolean
  selectedDelete: boolean
}

interface TranscriptSegment {
  start: number
  end: number
  text: string
}

interface TranscriptWord {
  text: string
  start: number
  end: number
}

interface ReviewClipVideoResponse {
  clip_id: string
  playback_path: string
  playback_requires_auth: boolean
  audio_playback_path?: string | null
  audio_playback_requires_auth?: boolean
  original_duration: number
  new_duration: number
  deleted_duration: number
  saved_percent: number
}

interface ReviewBridgeMessage {
  type: string
  payload?: ReviewClipVideoResponse & { delete_segments?: Array<{ start: number; end: number }> }
}

interface UploadTicketRead {
  module: string
  media_type: string
  object_name: string
  upload_method: string
  upload_url: string
  file_url: string
  content_type: string
  expires_in_seconds: number
}

interface AvatarClipDraftRead {
  draft_id: string
  user_id: number
  title?: string | null
  selected_product_id?: string | null
  selected_product_profile: Record<string, unknown>
  product_assets: Array<Record<string, unknown>>
  selected_clip_asset_ids: string[]
  review_units: Array<Record<string, unknown>>
  delete_segments: Array<Record<string, unknown>>
  cut_summary: Record<string, unknown>
  clipped_video_url?: string | null
  clipped_audio_url?: string | null
  avatar_source_mode: 'image' | 'video' | string
  avatar_image_url?: string | null
  avatar_video_url?: string | null
  generated_avatar_video_url?: string | null
  generated_avatar_source_url?: string | null
  avatar_task_id?: string | null
  avatar_task_status?: string | null
  overlay_position: string
  overlay_size_percent: number
  overlay_shape: string
  overlay_border: boolean
  overlay_shadow: boolean
  overlay_plate: boolean
  output_url?: string | null
  current_step: string
  status: string
  created_at: string
  updated_at: string
}

interface AvatarDraftIndexRead {
  draft_id: string
  title?: string | null
  status: string
  current_step_code?: string | null
  progress?: number | null
  updated_at: string
}

interface AvatarDraftIndexListResponse {
  items: AvatarDraftIndexRead[]
}

interface DigitalHumanSubmitResponse {
  job?: {
    output?: {
      task_id?: string
      task_status?: string
    }
  }
}

interface DigitalHumanTaskResponse {
  output?: {
    task_status?: string
    results?: Array<{ url?: string; video_url?: string }> | { url?: string; video_url?: string }
    video_url?: string
  }
  raw?: {
    errorMessage?: string
    errorCode?: string
    failedReason?: {
      exception_message?: string
      exception_type?: string
      node_name?: string
    }
  }
}

const copywritingApiBaseUrl = (
  import.meta.env.VITE_REMIX_AGENT_API_BASE_URL
  ?? import.meta.env.VITE_AGENT_API_BASE_URL
  ?? 'http://localhost:8002'
).replace(/\/$/, '')

const router = useRouter()
const route = useRoute()

const selectedScene = ref<SceneValue>('视频剪辑数字人')
const switchingScene = ref(false)
const currentMode = ref<'manual' | 'auto' | 'batch'>('manual')
const showModeMenu = ref(false)
const reviewMode = ref(false)
const draftId = ref('')
const showDraftLibrary = ref(false)
const draftLibraryLoading = ref(false)
const draftLibraryItems = ref<AvatarDraftIndexRead[]>([])
const hydratingDraft = ref(false)
let draftSaveTimer: ReturnType<typeof setTimeout> | null = null

const selectedProductId = ref('')
const productsLoading = ref(false)
const productOptions = ref<BrandProductCard[]>([])
const productsError = ref('')
const selectedBrand = ref<BrandProfile | null>(null)
const videoAssets = ref<VisualAssetItem[]>([])
const selectedClipAssetId = ref('')
const analysisLoading = ref(false)
const reviewUnits = ref<ReviewUnit[]>([])

const reviewFrame = ref<HTMLIFrameElement | null>(null)
const previewSection = ref<HTMLElement | null>(null)
const clippedPreviewUrl = ref('')
const clipBlobUrl = ref<string | null>(null)
const mergedPreviewUrl = ref('')
const mergedBlobUrl = ref<string | null>(null)
const reviewMediaBlobUrl = ref<string | null>(null)
const reviewMediaBlob = ref<Blob | null>(null)
const lastCutSummary = ref<ReviewClipVideoResponse | null>(null)
const clippedAudioUrl = ref('')
const baseVideoAspectRatio = ref(16 / 9)
const avatarSourceMode = ref<'image' | 'video'>('image')
const avatarImagePreviewUrl = ref('')
const avatarVideoPreviewUrl = ref('')
const avatarImageUrl = ref('')
const avatarVideoUrl = ref('')
const avatarMediaAspectRatio = ref(16 / 9)
const avatarUploading = ref(false)
const generatedAvatarVideoUrl = ref('')
const generatedAvatarVideoSourceUrl = ref('')
const generatingAvatarVideo = ref(false)
const avatarVideoTaskId = ref('')
const avatarVideoTaskStatus = ref('')
const mergingAvatarClip = ref(false)
const avatarOverlayPosition = ref<'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'>('bottom-right')
const avatarOverlaySize = ref('30')
const avatarOverlayShape = ref<'square' | 'rounded' | 'circle'>('square')
const avatarOverlayBorder = ref(false)
const avatarOverlayShadow = ref(false)
const avatarOverlayPlate = ref(false)

const avatarPositionOptions = [
  { value: 'bottom-right', label: '右下' },
  { value: 'bottom-left', label: '左下' },
  { value: 'top-right', label: '右上' },
  { value: 'top-left', label: '左上' },
] as const

const avatarShapeOptions = [
  { value: 'square', label: '方框' },
  { value: 'rounded', label: '圆角框' },
  { value: 'circle', label: '圆形框' },
] as const

const sceneRouteMap: Record<SceneValue, string> = {
  '口播数字人': '/content-creation/digital-human/talk',
  '卖货数字人': '/content-creation/digital-human/sales',
  '产品介绍数字人': '/content-creation/digital-human/product',
  '模特数字人': '/content-creation/digital-human/model',
  '视频剪辑数字人': '/content-creation/digital-human/clip',
}

const routeSceneMap = Object.fromEntries(
  Object.entries(sceneRouteMap).map(([scene, path]) => [path, scene as SceneValue]),
) as Record<string, SceneValue>

const primaryVideoAsset = computed(() => (
  videoAssets.value.find((asset) => String(asset.id) === selectedClipAssetId.value) ?? null
))

const previewVideoUrl = computed(() => mergedPreviewUrl.value || clippedPreviewUrl.value || primaryVideoAsset.value?.assetUrl || '')
const layoutBasePreviewUrl = computed(() => clippedPreviewUrl.value || primaryVideoAsset.value?.assetUrl || '')
const layoutAvatarPreviewUrl = computed(() => generatedAvatarVideoUrl.value || avatarVideoPreviewUrl.value || '')
const avatarPreviewFrameStyle = computed(() => ({
  aspectRatio: String(avatarMediaAspectRatio.value || 16 / 9),
}))
const layoutPreviewFrameStyle = computed(() => ({
  aspectRatio: String(baseVideoAspectRatio.value || 16 / 9),
}))
const canAnalyze = computed(() => Boolean(selectedBrand.value && primaryVideoAsset.value))
const confirmedDeleteSegments = computed(() => (
  reviewUnits.value
    .filter((item) => item.selectedDelete)
    .map((item) => ({ start: item.start, end: item.end }))
))
const confirmedDeleteCount = computed(() => confirmedDeleteSegments.value.length)
const suggestedDeleteCount = computed(() => reviewUnits.value.filter((item) => item.suggestedDelete).length)
const silentGapCount = computed(() => reviewUnits.value.filter((item) => item.isGap).length)
const deletedDurationSeconds = computed(() => (
  confirmedDeleteSegments.value.reduce((sum, item) => sum + Math.max(0, item.end - item.start), 0)
))
const deletedDurationLabel = computed(() => formatDuration(deletedDurationSeconds.value))
const draftSummaries = computed(() => draftLibraryItems.value.map((item) => ({
  id: item.draft_id,
  title: item.title || '未命名剪辑草稿',
  scene: '视频剪辑数字人',
  updatedAt: item.updated_at,
  status: item.status || 'draft',
})))
const currentModeLabel = computed(() => {
  if (currentMode.value === 'manual') return '手动模式'
  if (currentMode.value === 'auto') return '自动模式'
  return '批量模式'
})
const currentSceneDraftCount = computed(() => draftLibraryItems.value.length)

const reviewSrcdoc = computed(() => buildReviewSrcdoc())

function resolveCurrentStep() {
  if (mergedPreviewUrl.value) return 'preview'
  if (generatedAvatarVideoUrl.value) return 'layout'
  if (clippedPreviewUrl.value || reviewUnits.value.length) return 'avatar'
  if (selectedClipAssetId.value) return 'review'
  return 'product'
}

function normalizePersistedMediaUrl(value: unknown) {
  const url = String(value || '')
  return url.startsWith('blob:') ? '' : url
}

function buildDraftPayload() {
  const currentStep = resolveCurrentStep()
  return {
    title: selectedBrand.value?.productName || selectedBrand.value?.brandName || '视频剪辑数字人草稿',
    content_id: selectedProductId.value || undefined,
    selected_product_id: selectedProductId.value || undefined,
    selected_product_profile: selectedBrand.value || {},
    product_assets: videoAssets.value,
    selected_clip_asset_ids: selectedClipAssetId.value ? [selectedClipAssetId.value] : [],
    review_units: reviewUnits.value,
    delete_segments: confirmedDeleteSegments.value,
    cut_summary: lastCutSummary.value || {},
    clipped_video_url: clippedPreviewUrl.value || undefined,
    clipped_audio_url: clippedAudioUrl.value || undefined,
    avatar_source_mode: avatarSourceMode.value,
    avatar_image_url: avatarImageUrl.value || undefined,
    avatar_video_url: avatarVideoUrl.value || undefined,
    generated_avatar_video_url: generatedAvatarVideoUrl.value || undefined,
    generated_avatar_source_url: generatedAvatarVideoSourceUrl.value || undefined,
    avatar_task_id: avatarVideoTaskId.value || undefined,
    avatar_task_status: avatarVideoTaskStatus.value || undefined,
    overlay_position: avatarOverlayPosition.value,
    overlay_size_percent: Number(avatarOverlaySize.value) || 30,
    overlay_shape: avatarOverlayShape.value,
    overlay_border: avatarOverlayBorder.value,
    overlay_shadow: avatarOverlayShadow.value,
    overlay_plate: avatarOverlayPlate.value,
    output_url: mergedPreviewUrl.value || undefined,
    current_step: currentStep,
    status: currentStep === 'preview' ? 'completed' : 'draft',
  }
}

function hasPersistableContent() {
  return Boolean(
    selectedProductId.value
    || selectedClipAssetId.value
    || reviewUnits.value.length
    || avatarImageUrl.value
    || avatarVideoUrl.value
    || generatedAvatarVideoUrl.value
    || mergedPreviewUrl.value,
  )
}

async function saveDraftNow() {
  if (hydratingDraft.value || !hasPersistableContent()) return
  const payload = buildDraftPayload()
  try {
    const saved = draftId.value
      ? await request<AvatarClipDraftRead>(`/api/v1/avatar-clip-drafts/${draftId.value}`, { method: 'PATCH', body: payload })
      : await request<AvatarClipDraftRead>('/api/v1/avatar-clip-drafts', { method: 'POST', body: payload })
    draftId.value = saved.draft_id
    if (route.query.draftId !== saved.draft_id) {
      await router.replace({ path: route.path, query: { ...route.query, draftId: saved.draft_id } })
    }
  } catch (error) {
    console.error('Failed to persist clip draft', error)
  }
}

function scheduleDraftSave() {
  if (draftSaveTimer) clearTimeout(draftSaveTimer)
  draftSaveTimer = setTimeout(() => {
    void saveDraftNow()
  }, 500)
}

async function loadDraft(id: string) {
  hydratingDraft.value = true
  try {
    const draft = await request<AvatarClipDraftRead>(`/api/v1/avatar-clip-drafts/${id}`)
    draftId.value = draft.draft_id
    selectedProductId.value = String(draft.selected_product_id || '')
    selectedBrand.value = (draft.selected_product_profile || null) as BrandProfile | null
    videoAssets.value = Array.isArray(draft.product_assets) ? draft.product_assets as VisualAssetItem[] : []
    const ids = Array.isArray(draft.selected_clip_asset_ids) ? draft.selected_clip_asset_ids.map(String) : []
    selectedClipAssetId.value = ids[0] || ''
    reviewUnits.value = Array.isArray(draft.review_units) ? draft.review_units as unknown as ReviewUnit[] : []
    clippedPreviewUrl.value = normalizePersistedMediaUrl(draft.clipped_video_url)
    clippedAudioUrl.value = normalizePersistedMediaUrl(draft.clipped_audio_url)
    avatarSourceMode.value = draft.avatar_source_mode === 'video' ? 'video' : 'image'
    avatarImageUrl.value = normalizePersistedMediaUrl(draft.avatar_image_url)
    avatarVideoUrl.value = normalizePersistedMediaUrl(draft.avatar_video_url)
    avatarImagePreviewUrl.value = avatarImageUrl.value
    avatarVideoPreviewUrl.value = avatarVideoUrl.value
    generatedAvatarVideoUrl.value = normalizePersistedMediaUrl(draft.generated_avatar_video_url)
    generatedAvatarVideoSourceUrl.value = normalizePersistedMediaUrl(draft.generated_avatar_source_url)
    avatarVideoTaskId.value = String(draft.avatar_task_id || '')
    avatarVideoTaskStatus.value = String(draft.avatar_task_status || '')
    const rawPos = String(draft.overlay_position || 'bottom-right')
    avatarOverlayPosition.value = (
      rawPos === 'bottom-left' || rawPos === 'top-right' || rawPos === 'top-left'
        ? rawPos
        : 'bottom-right'
    )
    avatarOverlaySize.value = String(draft.overlay_size_percent || 30)
    avatarOverlayShape.value = (draft.overlay_shape || 'square') as typeof avatarOverlayShape.value
    avatarOverlayBorder.value = Boolean(draft.overlay_border)
    avatarOverlayShadow.value = Boolean(draft.overlay_shadow)
    avatarOverlayPlate.value = Boolean(draft.overlay_plate)
    mergedPreviewUrl.value = normalizePersistedMediaUrl(draft.output_url)
    lastCutSummary.value = Object.keys(draft.cut_summary || {}).length ? draft.cut_summary as unknown as ReviewClipVideoResponse : null
    if (!mergedPreviewUrl.value && String(draft.output_url || '').startsWith('blob:') && lastCutSummary.value?.playback_path) {
      try {
        mergedPreviewUrl.value = await persistReviewClipVideo(lastCutSummary.value.playback_path, 'merged_avatar_clip')
        await saveDraftNow()
      } catch (error) {
        console.warn('Failed to recover merged clip from transient draft URL', error)
      }
    }
  } finally {
    hydratingDraft.value = false
  }
}

async function loadDraftLibrary() {
  draftLibraryLoading.value = true
  try {
    const data = await request<AvatarDraftIndexListResponse>('/api/v1/avatar-drafts?scene=clip&limit=20&offset=0')
    draftLibraryItems.value = data.items || []
  } finally {
    draftLibraryLoading.value = false
  }
}

function openDraftLibrary() {
  showModeMenu.value = false
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

function handlePublishDraft(id: string) {
  window.postMessage({
    type: 'openNewPlanModal',
    mode: 'avatarOnly',
    draftId: id,
  }, '*')
  closeDraftLibrary()
}

async function handleSelectDraft(id: string) {
  await loadDraft(id)
  closeDraftLibrary()
  await router.replace({ path: route.path, query: { ...route.query, draftId: id } })
}

async function handleDeleteDraft(id: string) {
  if (!window.confirm('确定删除这条剪辑草稿吗？')) return
  await request(`/api/v1/avatar-clip-drafts/${id}`, { method: 'DELETE' })
  if (draftId.value === id) {
    await handleCreateNewContent()
  } else {
    await loadDraftLibrary()
  }
}

async function handleCreateNewContent() {
  draftId.value = ''
  selectedProductId.value = ''
  selectedBrand.value = null
  videoAssets.value = []
  selectedClipAssetId.value = ''
  reviewUnits.value = []
  lastCutSummary.value = null
  clippedAudioUrl.value = ''
  clippedPreviewUrl.value = ''
  generatedAvatarVideoUrl.value = ''
  generatedAvatarVideoSourceUrl.value = ''
  avatarVideoTaskId.value = ''
  avatarVideoTaskStatus.value = ''
  avatarImageUrl.value = ''
  avatarVideoUrl.value = ''
  mergedPreviewUrl.value = ''
  closeDraftLibrary()
  await router.replace({ path: route.path, query: buildDraftlessQuery(route.query) })
}

function formatDraftTime(value: string) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function buildHeaders() {
  const headers = new Headers({ 'Content-Type': 'application/json' })
  const token = authStore.state.session?.accessToken
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return headers
}

function buildMediaFetchHeaders() {
  const headers = new Headers()
  const token = authStore.state.session?.accessToken
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return headers
}

async function uploadFileToObjectStorage(file: File, module: string, mediaType: 'image' | 'video' | 'audio') {
  const ticket = await request<UploadTicketRead>('/api/v1/uploads/ticket', {
    method: 'POST',
    body: {
      module,
      media_type: mediaType,
      file_name: file.name,
      content_type: file.type || 'application/octet-stream',
      draft_id: null,
    },
  })

  const response = await fetch(ticket.upload_url, {
    method: ticket.upload_method || 'PUT',
    headers: {
      'Content-Type': file.type || ticket.content_type || 'application/octet-stream',
    },
    body: file,
  })
  if (!response.ok) {
    throw new Error('文件上传失败')
  }
  return ticket.file_url
}

async function uploadBlobToObjectStorage(blob: Blob, module: string, mediaType: 'image' | 'video' | 'audio', fileName: string) {
  const file = new File([blob], fileName, {
    type: blob.type || (mediaType === 'audio' ? 'audio/mp4' : mediaType === 'image' ? 'image/png' : 'video/mp4'),
  })
  return uploadFileToObjectStorage(file, module, mediaType)
}

async function fetchProtectedBlobData(path: string) {
  const response = await fetch(`${getApiBaseUrl()}${path}`, { headers: buildMediaFetchHeaders() })
  if (!response.ok) throw new Error('文件拉取失败')
  return response.blob()
}

async function fetchBlobFromUrl(url: string, headers?: HeadersInit) {
  const response = await fetch(url, headers ? { headers } : undefined)
  if (!response.ok) throw new Error('视频文件拉取失败')
  return response.blob()
}

async function persistReviewClipAudio(path?: string | null) {
  if (!path) {
    clippedAudioUrl.value = ''
    return
  }
  const blob = await fetchProtectedBlobData(path)
  const file = new File([blob], `review_clip_audio_${Date.now()}.m4a`, {
    type: blob.type || 'audio/mp4',
  })
  clippedAudioUrl.value = await uploadFileToObjectStorage(file, 'digital_human', 'audio')
}

async function persistReviewClipVideo(path?: string | null, filePrefix = 'review_clip_video') {
  if (!path) return ''
  const blob = await fetchProtectedBlobData(path)
  return uploadBlobToObjectStorage(blob, 'digital_human', 'video', `${filePrefix}_${Date.now()}.mp4`)
}

async function uploadRemoteVideoToObjectStorage(sourceUrl: string) {
  const response = await fetch(sourceUrl)
  if (!response.ok) {
    throw new Error('数字人成片下载失败')
  }

  const blob = await response.blob()
  const contentType = blob.type || 'video/mp4'
  const extension = contentType.includes('quicktime')
    ? 'mov'
    : contentType.includes('webm')
      ? 'webm'
      : 'mp4'
  const file = new File([blob], `clip_digital_human_${Date.now()}.${extension}`, { type: contentType })
  return uploadFileToObjectStorage(file, 'digital_human', 'video')
}

async function handleSceneSwitch(targetScene: SceneValue, sourceScene: SceneValue) {
  if (!targetScene || targetScene === sourceScene || switchingScene.value) return
  const targetPath = sceneRouteMap[targetScene]
  if (!targetPath) return

  switchingScene.value = true
  try {
    await router.push({
      path: targetPath,
      query: buildDraftlessQuery(route.query),
    })
  } catch (error) {
    selectedScene.value = sourceScene
    console.error('Failed to switch clip scene', error)
  } finally {
    switchingScene.value = false
  }
}

function normalizeTime(value: unknown) {
  const num = Number(value)
  if (!Number.isFinite(num)) return NaN
  return num > 1000 ? num / 1000 : num
}

function parseResponseSegments(payload: unknown): TranscriptSegment[] {
  const root = payload && typeof payload === 'object' ? payload as Record<string, unknown> : {}
  const data = root.data && typeof root.data === 'object' ? root.data as Record<string, unknown> : {}
  const candidates = Array.isArray(root.segments)
    ? root.segments
    : Array.isArray(data.segments)
      ? data.segments
      : []

  return candidates
    .map((item) => {
      if (!item || typeof item !== 'object') return null
      const raw = item as Record<string, unknown>
      const start = normalizeTime(raw.start ?? raw.start_time)
      const end = normalizeTime(raw.end ?? raw.end_time)
      const text = String(raw.text ?? raw.sentence ?? raw.content ?? '').trim()
      if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null
      return { start, end, text }
    })
    .filter((item): item is TranscriptSegment => Boolean(item))
}

function parseResponseWords(payload: unknown): TranscriptWord[] {
  const root = payload && typeof payload === 'object' ? payload as Record<string, unknown> : {}
  const data = root.data && typeof root.data === 'object' ? root.data as Record<string, unknown> : {}
  const utterances = Array.isArray(root.utterances)
    ? root.utterances
    : Array.isArray(data.utterances)
      ? data.utterances
      : []

  const words: TranscriptWord[] = []
  utterances.forEach((utterance) => {
    if (!utterance || typeof utterance !== 'object') return
    const rawUtterance = utterance as Record<string, unknown>
    const rawWords = Array.isArray(rawUtterance.words) ? rawUtterance.words : []
    rawWords.forEach((item) => {
      if (!item || typeof item !== 'object') return
      const raw = item as Record<string, unknown>
      const start = normalizeTime(raw.start ?? raw.start_time)
      const end = normalizeTime(raw.end ?? raw.end_time)
      const text = String(raw.text ?? raw.word ?? '').trim()
      if (!text || !Number.isFinite(start) || !Number.isFinite(end) || end <= start) return
      words.push({ text, start, end })
    })
  })
  return words
}

function fillerPattern() {
  return /^(嗯+|啊+|然后|就是|那个|这个|呃+|好)$/
}

function buildReviewUnitsFromWords(words: TranscriptWord[]) {
  const result: ReviewUnit[] = []
  let lastEnd = 0

  words.forEach((word, index) => {
    const gapDuration = Number((word.start - lastEnd).toFixed(3))
    if (gapDuration > 0.1) {
      if (gapDuration > 0.5) {
        let gapStart = lastEnd
        let gapIndex = 0
        while (gapStart < word.start) {
          const gapEnd = Math.min(gapStart + 1, word.start)
          result.push({
            id: `gap-${index}-${gapIndex}`,
            text: '',
            start: roundTo2(gapStart),
            end: roundTo2(gapEnd),
            isGap: true,
            suggestedDelete: gapEnd - gapStart >= 0.2,
            selectedDelete: gapEnd - gapStart >= 0.2,
          })
          gapStart = gapEnd
          gapIndex += 1
        }
      } else {
        result.push({
          id: `gap-${index}`,
          text: '',
          start: roundTo2(lastEnd),
          end: roundTo2(word.start),
          isGap: true,
          suggestedDelete: gapDuration >= 0.2,
          selectedDelete: gapDuration >= 0.2,
        })
      }
    }

    result.push({
      id: `word-${index}`,
      text: word.text,
      start: word.start,
      end: word.end,
      isGap: false,
      suggestedDelete: fillerPattern().test(word.text),
      selectedDelete: fillerPattern().test(word.text),
    })
    lastEnd = word.end
  })

  return result
}

function buildReviewUnitsFromSegments(segments: TranscriptSegment[]) {
  const result: ReviewUnit[] = []
  let previousEnd = 0

  segments.forEach((segment, index) => {
    const gap = Number((segment.start - previousEnd).toFixed(3))
    if (gap >= 0.45) {
      result.push({
        id: `gap-${index}`,
        start: previousEnd,
        end: segment.start,
        text: '',
        isGap: true,
        suggestedDelete: true,
        selectedDelete: true,
      })
    }

    const text = segment.text || '[空白]'
    const chars = Array.from(text).filter((char) => char.trim().length > 0)
    const duration = segment.end - segment.start
    if (!chars.length || duration <= 0) {
      previousEnd = segment.end
      return
    }
    const step = duration / chars.length
    chars.forEach((char, charIndex) => {
      const start = segment.start + (step * charIndex)
      const end = charIndex === chars.length - 1 ? segment.end : (segment.start + (step * (charIndex + 1)))
      const suggestedDelete = fillerPattern().test(char)
      result.push({
        id: `char-${index}-${charIndex}`,
        start,
        end,
        text: char,
        isGap: false,
        suggestedDelete,
        selectedDelete: suggestedDelete,
      })
    })
    previousEnd = segment.end
  })

  return result
}

function buildReviewWords() {
  return reviewUnits.value.map((segment) => ({
    text: segment.text,
    start: segment.start,
    end: segment.end,
    isGap: segment.isGap,
  }))
}

function buildReviewSrcdoc() {
  const mediaUrl = reviewMediaBlobUrl.value || primaryVideoAsset.value?.assetUrl || ''
  const token = authStore.state.session?.accessToken ?? ''
  const wordsJson = JSON.stringify(buildReviewWords())
  const autoSelectedIndexes = reviewUnits.value
    .map((segment, index) => (segment.suggestedDelete ? index : -1))
    .filter((index) => index >= 0)
  const autoSelectedJson = JSON.stringify(autoSelectedIndexes)
  const configJson = JSON.stringify({
    apiBaseUrl: getApiBaseUrl(),
    mediaUrl,
    token,
  })

  let html = reviewTemplateHtml
  html = html.replace('src="video.mp4"', `src="${escapeHtmlAttribute(mediaUrl)}"`)
  html = html.replace(
    '<div class="buttons">',
    '<div class="buttons"><div class="toolbar-main">',
  )
  html = html.replace(
    '<span id="time">00:00 / 00:00</span>',
    `<span id="time">00:00 / 00:00</span></div><button id="systemExitButton" class="system-exit">退出</button>`,
  )
  html = html.replace(
    '.buttons {\n      display: flex;\n      gap: 10px;\n      align-items: center;\n      flex-wrap: wrap;\n    }',
    `.buttons {
      display: flex;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: nowrap;
      width: 100%;
    }

    .toolbar-main {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      min-width: 0;
      flex: 1;
    }

    .system-exit {
      margin-left: auto;
      background: #555;
      color: #fff;
      flex-shrink: 0;
    }

    .system-exit:hover { background: #666; }`,
  )
  html = html.replace(
    /const words = [\s\S]*?const autoSelected = new Set\([\s\S]*?\);\s*const selected = new Set\(autoSelected\);/,
    `const words = ${wordsJson};
    const autoSelected = new Set(${autoSelectedJson});
    const selected = new Set(autoSelected);`,
  )

  const configScript = `
  <script>
    window.__SYSTEM_REVIEW_CONFIG__ = ${configJson};
  <\\/script>
  `

  return html.replace('</body>', `${configScript}</body>`)
}

async function loadProducts() {
  productsLoading.value = true
  productsError.value = ''
  try {
    const data = await listBrandProducts()
    productOptions.value = data.list
  } catch (error) {
    productsError.value = error instanceof Error ? error.message : '产品列表加载失败'
  } finally {
    productsLoading.value = false
  }
}

async function handleProductChange() {
  reviewMode.value = false
  reviewUnits.value = []
  selectedClipAssetId.value = ''
  selectedBrand.value = null
  videoAssets.value = []
  lastCutSummary.value = null
  clippedAudioUrl.value = ''
  revokeClipBlobUrl()
  revokeMergedBlobUrl()
  revokeReviewMediaBlobUrl()
  clippedPreviewUrl.value = ''

  if (!selectedProductId.value) return

  try {
    const [profile, assets] = await Promise.all([
      getBrandProfile(selectedProductId.value),
      getVisualAssets(selectedProductId.value),
    ])
    selectedBrand.value = profile
    videoAssets.value = assets.filter((item) => item.assetType === 'video' || item.usableForVideo)
    if (videoAssets.value.length) {
      selectedClipAssetId.value = String(videoAssets.value[0].id)
    }
    scheduleDraftSave()
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '产品素材加载失败')
  }
}

function resetClipPipelineForPrimaryVideoChange() {
  reviewMode.value = false
  reviewUnits.value = []
  lastCutSummary.value = null
  clippedAudioUrl.value = ''
  revokeClipBlobUrl()
  revokeMergedBlobUrl()
  revokeReviewMediaBlobUrl()
  clippedPreviewUrl.value = ''
  mergedPreviewUrl.value = ''
  generatedAvatarVideoUrl.value = ''
  generatedAvatarVideoSourceUrl.value = ''
  avatarVideoTaskId.value = ''
  avatarVideoTaskStatus.value = ''
  avatarImageUrl.value = ''
  avatarVideoUrl.value = ''
  revokeAvatarPreviewUrl()
}

function clipPrimarySwitchNeedsConfirm(nextId: string): boolean {
  if (!selectedClipAssetId.value || nextId === selectedClipAssetId.value) return false
  return Boolean(
    draftId.value
    || reviewUnits.value.length > 0
    || clippedPreviewUrl.value
    || mergedPreviewUrl.value
    || generatedAvatarVideoUrl.value,
  )
}

function applySelectedClipAsset(nextId: string) {
  selectedClipAssetId.value = nextId
  resetClipPipelineForPrimaryVideoChange()
  scheduleDraftSave()
}

function requestSelectClipAsset(assetId: string | number) {
  const nextId = String(assetId)
  if (nextId === selectedClipAssetId.value) return
  if (clipPrimarySwitchNeedsConfirm(nextId)) {
    const ok = window.confirm(
      '切换主视频将清空当前审核、剪辑成片与数字人等相关进度，并会更新草稿。确定继续？',
    )
    if (!ok) return
  }
  applySelectedClipAsset(nextId)
}

async function handleAnalyze() {
  if (!primaryVideoAsset.value) return

  analysisLoading.value = true
  try {
    await ensureReviewMediaBlobUrl(primaryVideoAsset.value.assetUrl)
    const response = await fetch(`${copywritingApiBaseUrl}/api/v1/copywriting/transcribe-media-url`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({ media_url: primaryVideoAsset.value.assetUrl }),
    })
    const payload = await parseJsonSafely(response)
    if (!response.ok) {
      const detail = payload && typeof payload === 'object' && 'detail' in payload
        ? (payload as Record<string, unknown>).detail
        : null
      throw new Error(typeof detail === 'string' ? detail : '剪辑分析失败')
    }

    const words = parseResponseWords(payload)
    if (words.length) {
      reviewUnits.value = buildReviewUnitsFromWords(words)
    } else {
      const segments = parseResponseSegments(payload)
      if (!segments.length) throw new Error('未拿到可审核的转录片段')
      reviewUnits.value = buildReviewUnitsFromSegments(segments)
    }
    lastCutSummary.value = null
    clippedAudioUrl.value = ''
    revokeClipBlobUrl()
    revokeMergedBlobUrl()
    clippedPreviewUrl.value = ''
    scheduleDraftSave()
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '剪辑分析失败')
  } finally {
    analysisLoading.value = false
  }
}

function openReviewWorkspace() {
  if (!reviewUnits.value.length || !primaryVideoAsset.value) return
  reviewMode.value = true
}

async function openReviewAndSelfTestClip() {
  openReviewWorkspace()
  if (!reviewMode.value) return

  await nextTick()
  const frame = reviewFrame.value
  if (!frame) return

  await new Promise<void>((resolve) => {
    const armAndContinue = () => {
      handleReviewFrameLoad()
      queueMicrotask(resolve)
    }
    if (frame.contentDocument?.readyState === 'complete') {
      armAndContinue()
    } else {
      frame.addEventListener('load', armAndContinue, { once: true })
    }
  })

  const win = frame.contentWindow as Window & { __executeReviewCut?: () => unknown }
  if (typeof win.__executeReviewCut !== 'function') {
    window.alert('审核页未就绪，请在详情工具栏中点击「执行剪辑」。')
    return
  }
  void win.__executeReviewCut()
}

function exitReviewWorkspace() {
  reviewMode.value = false
}

function revokeAvatarPreviewUrl(kind?: 'image' | 'video') {
  if ((!kind || kind === 'image') && avatarImagePreviewUrl.value) {
    URL.revokeObjectURL(avatarImagePreviewUrl.value)
    avatarImagePreviewUrl.value = ''
  }
  if ((!kind || kind === 'video') && avatarVideoPreviewUrl.value) {
    URL.revokeObjectURL(avatarVideoPreviewUrl.value)
    avatarVideoPreviewUrl.value = ''
  }
}

function normalizeAspectRatio(width: number, height: number) {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return 16 / 9
  }
  return Math.min(Math.max(width / height, 1 / 3), 3)
}

function readImageAspectRatio(url: string) {
  return new Promise<number>((resolve) => {
    const image = new Image()
    image.onload = () => resolve(normalizeAspectRatio(image.naturalWidth, image.naturalHeight))
    image.onerror = () => resolve(16 / 9)
    image.src = url
  })
}

function readVideoAspectRatio(url: string) {
  return new Promise<number>((resolve) => {
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.muted = true
    video.playsInline = true
    video.onloadedmetadata = () => resolve(normalizeAspectRatio(video.videoWidth, video.videoHeight))
    video.onerror = () => resolve(16 / 9)
    video.src = url
  })
}

function resolveRunningHubResolutionByAspectRatio(aspectRatio: number) {
  if (aspectRatio < 0.85) return '1080x1920 (9:16) (竖屏)'
  if (aspectRatio > 1.2) return '1920x1080 (16:9) (横屏)'
  return '1024x1024 (1:1) (方形)'
}

function resolveAspectRatioLabel(aspectRatio: number) {
  if (aspectRatio < 0.85) return '9:16'
  if (aspectRatio > 1.2) return '16:9'
  return '1:1'
}

function handleLayoutBaseMetadata(event: Event) {
  const video = event.currentTarget as HTMLVideoElement
  baseVideoAspectRatio.value = normalizeAspectRatio(video.videoWidth, video.videoHeight)
}

async function handleClipAvatarUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  const expectImage = avatarSourceMode.value === 'image'
  if (expectImage && !file.type.startsWith('image/')) {
    window.alert('请选择图片文件')
    return
  }
  if (!expectImage && !file.type.startsWith('video/')) {
    window.alert('请选择视频文件')
    return
  }
  const url = URL.createObjectURL(file)
  if (avatarSourceMode.value === 'image') {
    revokeAvatarPreviewUrl('image')
    avatarImagePreviewUrl.value = url
    avatarMediaAspectRatio.value = await readImageAspectRatio(url)
  } else {
    revokeAvatarPreviewUrl('video')
    avatarVideoPreviewUrl.value = url
    avatarMediaAspectRatio.value = await readVideoAspectRatio(url)
  }
  avatarUploading.value = true
  try {
    const fileUrl = await uploadFileToObjectStorage(file, 'digital_human', expectImage ? 'image' : 'video')
    if (expectImage) {
      avatarImageUrl.value = fileUrl
    } else {
      avatarVideoUrl.value = fileUrl
    }
    generatedAvatarVideoUrl.value = ''
    generatedAvatarVideoSourceUrl.value = ''
    scheduleDraftSave()
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '数字人素材上传失败')
  } finally {
    avatarUploading.value = false
  }
}

async function pollClipAvatarVideoTask(taskId: string, type: 'image' | 'video') {
  try {
    const endpoint = type === 'video'
      ? `${copywritingApiBaseUrl}/api/v1/digital-human/videoretalk/tasks/${taskId}`
      : `${copywritingApiBaseUrl}/api/v1/digital-human/s2v/tasks/${taskId}`
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: buildHeaders(),
    })
    const data = (await parseJsonSafely(response)) as DigitalHumanTaskResponse | { detail?: string } | null
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : null
      throw new Error(typeof detail === 'string' ? detail : '数字人任务查询失败')
    }

    const output = data?.output || {}
    avatarVideoTaskStatus.value = String(output.task_status || avatarVideoTaskStatus.value || '')
    const results = output.results
    const resultUrl = output.video_url
      || (Array.isArray(results) ? results[0]?.video_url || results[0]?.url : results?.video_url || results?.url)
      || ''
    if (resultUrl) {
      generatedAvatarVideoSourceUrl.value = resultUrl
      generatedAvatarVideoUrl.value = await uploadRemoteVideoToObjectStorage(resultUrl)
      generatingAvatarVideo.value = false
      await saveDraftNow()
      taskStore.updateTaskStatus(taskId, {
        status: 'completed',
        taskStatus: avatarVideoTaskStatus.value,
        resultUrl,
      })
      return
    }

    if (['FAILED', 'CANCELED', 'CANCELLED'].includes(avatarVideoTaskStatus.value.toUpperCase())) {
      const failedReason = data?.raw?.failedReason
      const detail = failedReason?.exception_message
        || data?.raw?.errorMessage
        || avatarVideoTaskStatus.value
      generatingAvatarVideo.value = false
      taskStore.updateTaskStatus(taskId, {
        status: 'failed',
        taskStatus: avatarVideoTaskStatus.value,
        lastError: `数字人视频生成失败：${detail}`,
      })
      window.alert(`数字人视频生成失败：${detail}`)
      return
    }

    taskStore.updateTaskStatus(taskId, {
      taskStatus: avatarVideoTaskStatus.value,
    })

    window.setTimeout(() => {
      void pollClipAvatarVideoTask(taskId, type)
    }, 5000)
  } catch (error) {
    generatingAvatarVideo.value = false
    taskStore.updateTaskStatus(taskId, {
      status: 'failed',
      lastError: error instanceof Error ? error.message : '数字人任务查询失败',
    })
    window.alert(error instanceof Error ? error.message : '数字人任务查询失败')
  }
}

async function handleGenerateClipAvatarVideo() {
  if (generatingAvatarVideo.value) return
  if (avatarUploading.value) {
    window.alert('数字人素材仍在上传，请稍后再生成')
    return
  }
  const hasAvatar = avatarSourceMode.value === 'image'
    ? Boolean(avatarImageUrl.value)
    : Boolean(avatarVideoUrl.value)
  if (!hasAvatar) {
    window.alert(avatarSourceMode.value === 'image' ? '请先上传数字人图片' : '请先上传数字人视频')
    return
  }

  generatingAvatarVideo.value = true
  avatarVideoTaskStatus.value = 'PREPARING_AUDIO'
  generatedAvatarVideoUrl.value = ''
  generatedAvatarVideoSourceUrl.value = ''
  try {
    await ensureClippedAudioForAvatar()
    avatarVideoTaskStatus.value = 'SUBMITTING'
    const type = avatarSourceMode.value
    const endpoint = type === 'video'
      ? `${copywritingApiBaseUrl}/api/v1/digital-human/videoretalk/submit`
      : `${copywritingApiBaseUrl}/api/v1/digital-human/s2v/submit`
    const avatarAspectRatio = avatarMediaAspectRatio.value || 16 / 9
    const aspectRatioLabel = resolveAspectRatioLabel(avatarAspectRatio)
    const payload = type === 'video'
      ? {
          video_url: avatarVideoUrl.value,
          audio_url: clippedAudioUrl.value,
          video_extension: true,
          aspect_ratio: aspectRatioLabel,
          resolution: aspectRatioLabel,
        }
      : {
          image_url: avatarImageUrl.value,
          audio_url: clippedAudioUrl.value,
          script_text: reviewUnits.value.filter((item) => !item.selectedDelete && !item.isGap).map((item) => item.text).join(''),
          aspect_ratio: aspectRatioLabel,
          resolution: resolveRunningHubResolutionByAspectRatio(avatarAspectRatio),
          style: 'speech',
          skip_detect: false,
          purpose_scene: '视频剪辑数字人',
        }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    })
    const data = (await parseJsonSafely(response)) as DigitalHumanSubmitResponse | { detail?: string } | null
    if (!response.ok) {
      const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : null
      throw new Error(typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : '数字人视频生成失败')
    }

    const taskId = String(data?.job?.output?.task_id || '')
    if (!taskId) {
      throw new Error('数字人任务创建成功但未返回 task_id')
    }
    avatarVideoTaskId.value = taskId
    avatarVideoTaskStatus.value = String(data?.job?.output?.task_status || 'PENDING')
    scheduleDraftSave()
    taskStore.addTask({
      taskNo: taskId,
      keyword: selectedBrand.value?.productName || selectedBrand.value?.brandName || '视频剪辑数字人',
      platformCode: 'digital_human',
      taskKind: 'avatar_video',
      taskDomain: 'avatar_video',
      sourceRoutePath: route.path,
      hideWhileOnSource: true,
      purposeScene: '视频剪辑数字人',
      humanType: type,
      title: selectedBrand.value?.productName || '视频剪辑数字人',
      taskStatus: avatarVideoTaskStatus.value,
    })
    void pollClipAvatarVideoTask(taskId, type)
  } catch (error) {
    generatingAvatarVideo.value = false
    window.alert(error instanceof Error ? error.message : '数字人视频生成失败')
  }
}
async function executeMergeViaBackend(baseBlob: Blob, avatarBlob: Blob) {
  const formData = new FormData()
  formData.append('base_file', baseBlob, 'clip-base.mp4')
  formData.append('avatar_file', avatarBlob, 'clip-avatar.mp4')
  formData.append('overlay_position', avatarOverlayPosition.value)
  formData.append('overlay_size_percent', avatarOverlaySize.value)
  formData.append('overlay_shape', avatarOverlayShape.value)

  const headers = new Headers()
  const token = authStore.state.session?.accessToken
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${getApiBaseUrl()}/api/v1/review/merge-avatar-video-upload`, {
    method: 'POST',
    headers,
    body: formData,
  })

  const payload = await parseJsonSafely(response)
  if (!response.ok || !payload || typeof payload !== 'object' || !('data' in payload)) {
    const detail = payload && typeof payload === 'object'
      ? String((payload as Record<string, unknown>).message ?? (payload as Record<string, unknown>).msg ?? '融合成片生成失败')
      : '融合成片生成失败'
    throw new Error(detail)
  }

  return (payload as { data: ReviewClipVideoResponse }).data
}

async function handleGenerateMergedClip() {
  if (mergingAvatarClip.value) return
  const baseUrl = clippedPreviewUrl.value || primaryVideoAsset.value?.assetUrl || ''
  if (!baseUrl) {
    window.alert('请先完成视频选择或剪辑')
    return
  }
  if (!generatedAvatarVideoUrl.value) {
    window.alert('请先完成第 03 步数字人视频生成')
    return
  }

  mergingAvatarClip.value = true
  try {
    const baseHeaders = clippedPreviewUrl.value ? undefined : buildMediaFetchHeaders()
    const [baseBlob, avatarBlob] = await Promise.all([
      fetchBlobFromUrl(baseUrl, baseHeaders),
      fetchBlobFromUrl(generatedAvatarVideoUrl.value),
    ])
    const result = await executeMergeViaBackend(baseBlob, avatarBlob)
    revokeMergedBlobUrl()
    mergedPreviewUrl.value = await persistReviewClipVideo(result.playback_path, 'merged_avatar_clip')
    lastCutSummary.value = result
    await saveDraftNow()
    await nextTick()
    previewSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    window.alert('融合成片生成完成，已更新到第 05 步预览')
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '融合成片生成失败')
  } finally {
    mergingAvatarClip.value = false
  }
}
async function fetchProtectedBlob(path: string) {
  const response = await fetch(`${getApiBaseUrl()}${path}`, { headers: buildHeaders() })
  if (!response.ok) throw new Error('成片预览拉取失败')
  const blob = await response.blob()
  return URL.createObjectURL(blob)
}

async function executeClipViaBackend(deleteSegments: Array<{ start: number; end: number }>) {
  const sourceBlob = reviewMediaBlob.value
  if (!sourceBlob) {
    throw new Error('缺少可上传的原视频文件')
  }

  const formData = new FormData()
  formData.append('delete_segments', JSON.stringify(deleteSegments))
  formData.append('source_file', sourceBlob, 'review-source.mp4')

  const headers = new Headers()
  const token = authStore.state.session?.accessToken
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${getApiBaseUrl()}/api/v1/review/clip-video-upload`, {
    method: 'POST',
    headers,
    body: formData,
  })

  const payload = await parseJsonSafely(response)
  if (!response.ok || !payload || typeof payload !== 'object' || !('data' in payload)) {
    const detail = payload && typeof payload === 'object'
      ? String((payload as Record<string, unknown>).message ?? (payload as Record<string, unknown>).msg ?? '执行剪辑失败')
      : '执行剪辑失败'
    throw new Error(detail)
  }

  return (payload as { data: ReviewClipVideoResponse }).data
}

async function ensureClippedAudioForAvatar() {
  if (clippedAudioUrl.value) return
  const sourceUrl = primaryVideoAsset.value?.assetUrl || ''
  if (!sourceUrl) {
    throw new Error('请先选择底视频素材')
  }
  if (!reviewMediaBlob.value) {
    await ensureReviewMediaBlobUrl(sourceUrl)
  }
  const result = await executeClipViaBackend(confirmedDeleteSegments.value)
  revokeClipBlobUrl()
  revokeMergedBlobUrl()
  clippedPreviewUrl.value = await persistReviewClipVideo(result.playback_path, 'review_clipped_video')
  lastCutSummary.value = result
  await persistReviewClipAudio(result.audio_playback_path)
  if (!clippedAudioUrl.value) {
    throw new Error('当前视频没有可用音频，无法驱动数字人')
  }
  await saveDraftNow()
}

async function ensureReviewMediaBlobUrl(sourceUrl: string) {
  const trimmed = sourceUrl.trim()
  if (!trimmed) throw new Error('缺少原视频地址')
  revokeReviewMediaBlobUrl()
  const response = await fetch(trimmed, {
    headers: buildMediaFetchHeaders(),
  })
  if (!response.ok) {
    throw new Error('原视频拉取失败，无法进入带声音的审核模式')
  }
  const blob = await response.blob()
  reviewMediaBlob.value = blob
  reviewMediaBlobUrl.value = URL.createObjectURL(blob)
}

function applyDeleteSegments(deleteSegments: Array<{ start: number; end: number }>) {
  reviewUnits.value = reviewUnits.value.map((segment) => {
    const selectedDelete = deleteSegments.some((item) => (
      Math.abs(item.start - segment.start) < 0.06 && Math.abs(item.end - segment.end) < 0.06
    ))
    return { ...segment, selectedDelete }
  })
}

async function handleReviewBridgeMessage(event: MessageEvent<ReviewBridgeMessage>) {
  const frameWindow = reviewFrame.value?.contentWindow
  if (!frameWindow || event.source !== frameWindow) return
  if (event.data?.type === 'review-exit') {
    exitReviewWorkspace()
    return
  }
  if (event.data?.type !== 'review-cut-success' || !event.data.payload) return

  try {
    const payload = event.data.payload
    if (payload.delete_segments) {
      applyDeleteSegments(payload.delete_segments)
    }
    revokeClipBlobUrl()
    revokeMergedBlobUrl()
    clippedPreviewUrl.value = await persistReviewClipVideo(payload.playback_path, 'review_clipped_video')
    lastCutSummary.value = payload
    await persistReviewClipAudio(payload.audio_playback_path)
    await saveDraftNow()
    reviewMode.value = false
    await nextTick()
    previewSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    window.alert('执行剪辑完成，已更新到第 3 步预览。')
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '执行剪辑完成，但预览加载失败')
  }
}

function handleReviewFrameLoad() {
  const frameWindow = reviewFrame.value?.contentWindow
  const frameDocument = reviewFrame.value?.contentDocument
  if (!frameWindow || !frameDocument) return

  const config = {
    apiBaseUrl: getApiBaseUrl(),
    mediaUrl: primaryVideoAsset.value?.assetUrl ?? '',
    token: authStore.state.session?.accessToken ?? '',
  }
  ;(frameWindow as Window & { __SYSTEM_REVIEW_CONFIG__?: unknown }).__SYSTEM_REVIEW_CONFIG__ = config

  const buttons = frameDocument.querySelector('.buttons')
  let exitButton = frameDocument.getElementById('systemExitButton') as HTMLButtonElement | null
  if (!exitButton && buttons) {
    exitButton = frameDocument.createElement('button')
    exitButton.id = 'systemExitButton'
    exitButton.className = 'system-exit'
    exitButton.type = 'button'
    exitButton.textContent = '退出'
    buttons.appendChild(exitButton)
  }
  if (exitButton) {
    exitButton.onclick = () => {
      exitReviewWorkspace()
    }
  }

  frameWindow.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string'
      ? input
      : input instanceof URL
        ? input.toString()
        : input.url

    if (url === '/api/cut') {
      const rawBody = typeof init?.body === 'string' ? init.body : '[]'
      let deleteSegments: Array<{ start: number; end: number }> = []
      try {
        deleteSegments = JSON.parse(rawBody)
      } catch (error) {
        deleteSegments = []
      }

      try {
        const result = await executeClipViaBackend(deleteSegments)
        applyDeleteSegments(deleteSegments)
        revokeClipBlobUrl()
        revokeMergedBlobUrl()
        clippedPreviewUrl.value = await persistReviewClipVideo(result.playback_path, 'review_clipped_video')
        lastCutSummary.value = result
        await persistReviewClipAudio(result.audio_playback_path)
        await saveDraftNow()
        reviewMode.value = false
        await nextTick()
        previewSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })

        return new frameWindow.Response(JSON.stringify({
          success: true,
          output: '系统内预览',
          originalDuration: result.original_duration,
          newDuration: result.new_duration,
          deletedDuration: result.deleted_duration,
          savedPercent: result.saved_percent,
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      } catch (error) {
        const message = error instanceof Error ? error.message : '执行剪辑失败'
        return new frameWindow.Response(JSON.stringify({ success: false, error: message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        })
      }
    }

    return fetch(input, init)
  }
}

function revokeClipBlobUrl() {
  if (clipBlobUrl.value) {
    URL.revokeObjectURL(clipBlobUrl.value)
    clipBlobUrl.value = null
  }
}

function revokeMergedBlobUrl() {
  if (mergedBlobUrl.value) {
    URL.revokeObjectURL(mergedBlobUrl.value)
    mergedBlobUrl.value = null
  }
  mergedPreviewUrl.value = ''
}

function revokeReviewMediaBlobUrl() {
  if (reviewMediaBlobUrl.value) {
    URL.revokeObjectURL(reviewMediaBlobUrl.value)
    reviewMediaBlobUrl.value = null
  }
  reviewMediaBlob.value = null
}

function formatDuration(value: number) {
  if (!Number.isFinite(value) || value <= 0) return '0.0s'
  if (value >= 60) {
    const minutes = Math.floor(value / 60)
    const seconds = (value % 60).toFixed(1)
    return `${minutes}m ${seconds}s`
  }
  return `${value.toFixed(1)}s`
}

function roundTo2(value: number) {
  return Math.round(value * 100) / 100
}

function escapeHtmlAttribute(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('"', '&quot;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
}

async function parseJsonSafely(response: Response) {
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) return null
  return response.json()
}

onMounted(async () => {
  await authStore.ensureInitialized()
  await loadProducts()
  await loadDraftLibrary()
  const routeDraftId = typeof route.query.draftId === 'string' ? route.query.draftId : ''
  if (routeDraftId) {
    await loadDraft(routeDraftId)
  }
  window.addEventListener('message', handleReviewBridgeMessage)
})

watch(
  () => route.path,
  (path) => {
    const currentScene = routeSceneMap[path]
    if (!currentScene || switchingScene.value || selectedScene.value === currentScene) return
    selectedScene.value = currentScene
  },
  { immediate: true },
)

watch(selectedScene, async (scene, previous) => {
  showModeMenu.value = false
  if (!scene || !previous || scene === previous || switchingScene.value) return
  await handleSceneSwitch(scene, previous)
})

watch(reviewMode, (active) => {
  if (active) showModeMenu.value = false
})

onBeforeUnmount(() => {
  if (draftSaveTimer) clearTimeout(draftSaveTimer)
  void saveDraftNow()
  window.removeEventListener('message', handleReviewBridgeMessage)
  revokeClipBlobUrl()
  revokeMergedBlobUrl()
  revokeReviewMediaBlobUrl()
  revokeAvatarPreviewUrl()
})
</script>

<style scoped>
.clip-scroll-page {
  height: 100vh;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-bottom: 72px;
}

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

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.draft-badge {
  display: inline-flex;
  align-items: center;
  min-height: 38px;
}

.header-purpose-select {
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  outline: none;
  cursor: pointer;
  max-width: min(260px, 44vw);
}

.header-purpose-select:focus {
  border-color: rgba(37, 99, 235, 0.5);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.draft-library-button {
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 0 14px;
  background: #fff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.mode-switch {
  position: relative;
}

.mode-switch-button {
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 0 14px;
  background: #fff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
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
  font-size: 13px;
  font-weight: 600;
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

.draft-library-button:disabled,
.mode-switch-button:disabled {
  opacity: 0.7;
  cursor: default;
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
  color: #0f172a;
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

.draft-library-close {
  min-height: 38px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 0 14px;
  background: #fff;
  color: #334155;
  cursor: pointer;
}

.draft-library-secondary {
  min-height: 38px;
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  padding: 0 14px;
  background: #eff6ff;
  color: #1d4ed8;
  cursor: pointer;
}

.draft-library-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: calc(70vh - 96px);
  overflow: auto;
  padding: 16px 20px 20px;
}

.draft-library-empty {
  padding: 28px 20px;
  font-size: 14px;
  color: #64748b;
  text-align: center;
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
  font-size: 13px;
}

.draft-library-delete {
  min-width: 72px;
  border: 1px solid #fecaca;
  border-radius: 18px;
  background: #fff5f5;
  color: #dc2626;
  cursor: pointer;
}

.draft-library-publish {
  min-width: 72px;
  border: 1px solid #bfdbfe;
  border-radius: 18px;
  background: #eff6ff;
  color: #1d4ed8;
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

.review-frame-shell {
  min-height: calc(100vh - 160px);
  border-radius: 20px;
  overflow: hidden;
  background: #1a1a1a;
}

.review-frame {
  display: block;
  width: 100%;
  min-height: calc(100vh - 160px);
  border: none;
}

.grid-layout {
  display: grid;
  grid-template-columns: minmax(320px, 1.02fr) minmax(320px, 0.95fr) minmax(320px, 0.97fr);
  gap: 24px 26px;
  align-items: start;
}

.flow-column,
.studio-column,
.preview-column {
  display: contents;
}

.clip-step-product {
  grid-column: 1;
  grid-row: 1;
}

.clip-step-review {
  grid-column: 2;
  grid-row: 1;
}

.preview-card {
  grid-column: 3;
  grid-row: 1;
}

.digital-human-card {
  grid-column: 1;
  grid-row: 2;
}

.avatar-effect-card {
  grid-column: 2 / span 2;
  grid-row: 2;
}

.clip-step-product,
.clip-step-review,
.preview-card {
  min-height: 0;
}

.digital-human-card,
.avatar-effect-card {
  height: auto;
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
  overflow: visible;
}

.digital-human-card,
.avatar-effect-card {
  border-radius: 24px;
  padding: 18px 20px;
  gap: 10px;
}

.digital-human-card .primary-button,
.avatar-effect-card .primary-button {
  height: 38px;
  border-radius: 10px;
}

.panel-accent {
  background:
    radial-gradient(circle at top right, rgba(219, 234, 254, 0.8), transparent 26%),
    linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
}

.panel-head {
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

.panel-step,
.panel-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
}

.panel-step {
  background: rgba(37, 99, 235, 0.12);
  color: #2563eb;
  letter-spacing: 0.08em;
}

.panel-tag {
  background: #eff6ff;
  color: #1d4ed8;
  padding: 8px 12px;
  white-space: nowrap;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-block span,
.section-head span,
.summary-card span {
  font-size: 12px;
  color: #64748b;
}

.field-input {
  width: 100%;
  min-height: 46px;
  border: 1px solid #dbeafe;
  border-radius: 18px;
  padding: 0 16px;
  background: #fff;
  color: #0f172a;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.field-input:focus,
select.field-input:focus {
  border-color: rgba(37, 99, 235, 0.5);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12);
}

.profile-card,
.summary-card {
  border: 1px solid #dbeafe;
  border-radius: 18px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.96);
}

.profile-card strong,
.summary-card strong,
.asset-meta strong {
  color: #0f172a;
}

.profile-card p,
.preview-note {
  margin: 6px 0 0;
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
}

.profile-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-head strong {
  color: #0f172a;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.asset-card {
  border: 1px solid #dbeafe;
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.96);
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(148, 163, 184, 0.08);
  font: inherit;
  text-align: left;
  padding: 0;
  margin: 0;
  width: 100%;
}

.asset-card.active {
  border-color: rgba(59, 130, 246, 0.42);
  box-shadow: 0 12px 20px rgba(37, 99, 235, 0.08);
}

.asset-media {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: contain;
  background: #0f172a;
  display: block;
}

.asset-meta {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.asset-meta span {
  font-size: 12px;
  color: #64748b;
}

.empty-state,
.empty-stage {
  border: 1px dashed #bfdbfe;
  border-radius: 24px;
  padding: 22px;
  background: rgba(255, 255, 255, 0.88);
  text-align: center;
  color: #64748b;
}

.asset-grid > .empty-state {
  grid-column: 1 / -1;
  width: 100%;
  min-height: clamp(140px, 18vh, 180px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.clip-step-product .asset-grid > .empty-state {
  min-height: clamp(130px, 16vh, 165px);
}

.empty-stage {
  min-height: clamp(260px, 30vh, 340px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.clip-step-review .empty-stage {
  min-height: clamp(280px, 32vh, 360px);
}

.empty-stage-icon {
  width: 54px;
  height: 54px;
  border-radius: 999px;
  border: 1px solid #bfdbfe;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
  font-weight: 700;
  background: #eff6ff;
}

.step-footer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.inline-summary {
  color: #475569;
  font-size: 13px;
}

.primary-button,
.ghost-button {
  height: 46px;
  border-radius: 16px;
  padding: 0 18px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
}

.primary-button {
  border: none;
  background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
  color: #fff;
}

.ghost-button {
  border: 1px solid #bfdbfe;
  background: #fff;
  color: #2563eb;
}

.primary-button:disabled,
.ghost-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.full-width {
  width: 100%;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.summary-actions {
  display: flex;
  gap: 12px;
}

.segmented-control {
  display: inline-flex;
  gap: 3px;
  padding: 3px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: #fff;
}

.segmented-option {
  min-height: 30px;
  border: 0;
  border-radius: 10px;
  padding: 0 12px;
  background: transparent;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.segmented-option.active {
  background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
  color: #fff;
  box-shadow: 0 8px 14px rgba(37, 99, 235, 0.16);
}

.digital-human-body {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 8px;
  align-items: stretch;
}

.digital-human-pane,
.layout-preview-pane {
  min-width: 0;
}

.pane-title {
  margin-bottom: 10px;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.upload-dropzone,
.digital-result-box {
  position: relative;
  width: 100%;
  min-height: 0;
  max-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  box-sizing: border-box;
  border: 1px dashed rgba(59, 130, 246, 0.34);
  border-radius: 18px;
  background:
    radial-gradient(circle at top, rgba(191, 219, 254, 0.24), transparent 52%),
    linear-gradient(180deg, #fff 0%, #fbfdff 100%);
  color: #64748b;
  text-align: center;
  cursor: pointer;
  overflow: hidden;
}

.digital-result-box {
  cursor: default;
}

.upload-dropzone strong,
.digital-result-box strong {
  color: #0f172a;
  font-size: 15px;
}

.upload-dropzone span,
.digital-result-box span {
  font-size: 13px;
}

.upload-icon {
  color: #94a3b8;
  font-size: 42px;
}

.avatar-upload-preview,
.avatar-result-preview {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  padding: 0;
  margin: 0;
  border: 0;
  object-fit: contain;
  background: #0f172a;
}

.avatar-effect-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr);
  gap: 38px;
  align-items: start;
  margin-bottom: 8px;
}

.effect-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.effect-row {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  align-items: center;
  gap: 6px;
  min-height: 30px;
}

.effect-label,
.effect-switch-row span {
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.effect-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.effect-chip {
  min-height: 28px;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: #fff;
  padding: 0 12px;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.effect-chip.active {
  border-color: rgba(37, 99, 235, 0.42);
  background: #eff6ff;
  color: #2563eb;
}

.effect-slider-wrap {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 48px;
  align-items: center;
  gap: 12px;
}

.effect-slider {
  width: 100%;
  accent-color: #2563eb;
}

.effect-slider-wrap strong {
  color: #475569;
  font-size: 13px;
}

.effect-switch-row {
  min-height: 28px;
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  align-items: center;
  gap: 6px;
}

.effect-switch-row input {
  width: 18px;
  height: 18px;
  accent-color: #2563eb;
}

.avatar-layout-preview {
  position: relative;
  min-height: 188px;
  max-height: min(46vh, 520px);
  border: 1px solid #dbeafe;
  border-radius: 12px;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(180deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(180deg, #fbfdff, #f6faff);
  background-size: 28px 28px, 28px 28px, auto;
}

.avatar-layout-base,
.avatar-layout-video {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-layout-base {
  position: absolute;
  inset: 0;
}

.avatar-layout-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.avatar-layout-pip {
  position: absolute;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 16 / 9;
  min-width: 58px;
  overflow: hidden;
  border: 1.5px solid rgba(37, 99, 235, 0.65);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.82);
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.avatar-layout-pip.position-bottom-right {
  right: 20px;
  bottom: 18px;
}

.avatar-layout-pip.position-bottom-left {
  left: 20px;
  bottom: 18px;
}

.avatar-layout-pip.position-top-right {
  right: 20px;
  top: 18px;
}

.avatar-layout-pip.position-top-left {
  left: 20px;
  top: 18px;
}

.avatar-layout-pip.shape-rounded {
  border-radius: 18px;
}

.avatar-layout-pip.shape-circle {
  aspect-ratio: 1;
  border-radius: 999px;
}

.avatar-layout-pip.bordered {
  border-style: solid;
  border-color: #2563eb;
}

.avatar-layout-pip.shadowed {
  box-shadow: 0 12px 22px rgba(15, 23, 42, 0.16);
}

.avatar-layout-pip.plated {
  padding: 6px;
  background: rgba(239, 246, 255, 0.9);
}

.preview-stage {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-card {
  min-height: 0;
}

.preview-screen {
  display: flex;
  min-height: clamp(280px, 32vh, 360px);
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 30px;
  border: 1px dashed rgba(59, 130, 246, 0.28);
  background:
    radial-gradient(circle at top, rgba(191, 219, 254, 0.4), transparent 54%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(239, 246, 255, 0.88));
  text-align: center;
  padding: 28px;
}

.preview-screen-static {
  align-items: stretch;
  justify-content: flex-start;
  gap: 16px;
  min-height: clamp(320px, 36vh, 420px);
}

.preview-video {
  width: 100%;
  max-height: 420px;
  border-radius: 24px;
  object-fit: contain;
  background: #0f172a;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.16);
}

.json-preview {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  color: #0f172a;
}

.hidden {
  display: none;
}

@media (max-width: 1280px) {
  .grid-layout {
    grid-template-columns: 1fr 1fr;
  }

  .clip-step-product {
    grid-column: 1;
    grid-row: 1;
  }

  .clip-step-review {
    grid-column: 2;
    grid-row: 1;
  }

  .digital-human-card {
    grid-column: 1;
    grid-row: 2;
  }

  .avatar-effect-card {
    grid-column: 2;
    grid-row: 2;
  }

  .preview-card {
    grid-column: 1 / -1;
    grid-row: 3;
  }
}

@media (max-width: 960px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .grid-layout,
  .asset-grid,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .clip-step-product,
  .clip-step-review,
  .digital-human-card,
  .avatar-effect-card,
  .preview-card {
    grid-column: 1;
    grid-row: auto;
  }

  .summary-actions {
    flex-direction: column;
  }
}
</style>

