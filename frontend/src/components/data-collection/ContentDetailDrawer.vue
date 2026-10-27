<template>
  <div v-show="modelValue" class="fixed inset-0 z-[100] flex justify-end">
    <div
      class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
      :class="isAnimating ? 'opacity-100' : 'opacity-0'"
      @click="close"
    ></div>

    <div
      class="relative w-full max-w-lg h-full bg-white shadow-2xl flex flex-col transition-transform duration-300 ease-out transform pointer-events-auto"
      :class="isAnimating ? 'translate-x-0' : 'translate-x-full'"
    >
      <div class="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between shrink-0">
        <h2 class="text-base font-bold text-slate-800 flex items-center gap-2">
          <span class="material-symbols-outlined text-primary">feed</span>
          内容详情
        </h2>
        <button @click="close" class="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-lg transition-colors">
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>

      <div v-if="loading" class="p-6 flex-1 overflow-y-auto space-y-6">
        <div class="h-48 bg-slate-200 rounded-xl animate-pulse"></div>
        <div class="space-y-3">
          <div class="h-6 bg-slate-200 rounded w-full animate-pulse"></div>
          <div class="h-6 bg-slate-200 rounded w-3/4 animate-pulse"></div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div v-for="i in 4" :key="i" class="h-16 bg-slate-100 rounded-lg animate-pulse"></div>
        </div>
      </div>

      <div v-else-if="detail" class="p-5 sm:p-6 flex-1 overflow-y-auto custom-scrollbar">
        <div v-if="'cover' in detail && detail.cover" class="w-full h-52 rounded-2xl overflow-hidden shadow-sm mb-5 border border-slate-200 bg-slate-100">
          <img :src="detail.cover" class="w-full h-full object-cover" />
        </div>

        <h1 class="text-xl font-bold text-slate-900 leading-snug mb-3">{{ displayTitle }}</h1>

        <div class="flex flex-col gap-3 mb-5 pb-5 border-b border-slate-100">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-2 text-xs text-slate-500">
              <span class="font-medium text-primary bg-primary/10 px-2.5 py-1 rounded-md flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">person</span>
                <span class="max-w-[150px] truncate" :title="detail.author || detail.authorName || '未知作者'">
                  {{ detail.author || detail.authorName || '未知作者' }}
                </span>
              </span>
              <span class="flex items-center gap-1 bg-slate-100 px-2.5 py-1 rounded-md">
                <span class="material-symbols-outlined text-[14px]">schedule</span>
                {{ detail.publishTime || '未知' }}
              </span>
            </div>
            <div class="flex items-center gap-2 w-full sm:w-auto">
              <button
                v-if="hasDownloadUrl"
                @click="isImage ? handleBatchDownload() : downloadMedia(primaryDownloadUrl || '', displayTitle)"
                :disabled="isDownloading"
                class="flex-1 sm:flex-none justify-center inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-primary/20 bg-primary/5 text-primary hover:bg-primary hover:text-white transition-all font-medium text-sm shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span class="material-symbols-outlined text-[16px]">
                  {{ isDownloading ? 'hourglass_empty' : 'download' }}
                </span> 
                {{ isDownloading ? (isImage ? `已下 ${downloadCounts}/${totalToDownload}` : '下载中...') : (isImage ? '极速下载全部' : '下载视频') }}
              </button>

              <a
                v-if="hasSourceUrl"
                :href="detail.sourceUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="flex-1 sm:flex-none justify-center inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 hover:text-primary hover:border-primary/30 hover:bg-primary/5 transition-all text-sm font-medium shadow-sm"
              >
                <span class="material-symbols-outlined text-[16px]">open_in_new</span> 查看原文
              </a>
              <span
                v-else-if="!hasDownloadUrl"
                class="flex-1 sm:flex-none justify-center inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-400 cursor-not-allowed text-sm font-medium"
              >
                <span class="material-symbols-outlined text-[16px]">link_off</span> 暂无链接
              </span>
            </div>
          </div>
        </div>

        <div v-if="isImage && normalizedImages.length" class="space-y-4 mb-5">
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
            <div 
              v-for="(img, idx) in normalizedImages" 
              :key="idx"
              class="block aspect-[3/4] rounded-lg overflow-hidden border border-border group relative bg-gray-50 dark:bg-gray-800"
            >
              <img 
                :src="img.url" 
                loading="lazy"
                class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                :alt="`Image ${Number(idx) + 1}`"
              >
              <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4">
                <a :href="img.url" target="_blank" @click.stop class="text-white hover:text-primary transition-colors flex flex-col items-center" title="在新标签页打开">
                  <span class="material-symbols-outlined text-3xl">open_in_new</span>
                </a>
                <button @click.stop="downloadMedia(img.downloadUrl, `${(detail as any)?.title || 'media'}_${Number(idx) + 1}`)" class="text-white hover:text-primary transition-colors flex flex-col items-center" title="极速下载">
                  <span class="material-symbols-outlined text-3xl">download</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="shouldShowSummary" class="mb-5">
          <h3 class="text-sm font-bold text-slate-800 mb-2 flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">short_text</span>
            内容摘要
          </h3>
          <div class="bg-slate-50 px-3.5 py-3 rounded-xl border border-slate-100 text-slate-600 text-sm leading-relaxed">{{ displaySummary }}</div>
        </div>

        <div class="mb-5">
          <h3 class="text-sm font-bold text-slate-800 mb-2 flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">monitoring</span>
            {{ isHotRankDetail ? '热榜指标' : '互动指标' }}
          </h3>
          <div v-if="isHotRankDetail" class="grid grid-cols-1 gap-3">
            <MetricCard icon="local_fire_department" label="热度" :value="detail.hotValue || 0" />
          </div>
          <div v-else class="grid grid-cols-2 gap-3">
            <MetricCard v-if="'hotValue' in detail && detail.hotValue" icon="local_fire_department" label="热度" :value="detail.hotValue" />
            <MetricCard icon="favorite" label="点赞量" :value="detail.likes || 0" />
            <MetricCard icon="chat_bubble" label="评论量" :value="detail.comments || 0" />
            <MetricCard icon="share" label="分享量" :value="detail.shares || 0" />
            <MetricCard icon="star" label="收藏量" :value="(detail as any).collects || 0" />
          </div>
        </div>

        <div v-if="detail.tags && detail.tags.length">
          <h3 class="text-sm font-bold text-slate-800 mb-2 flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">sell</span>
            标签
          </h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="tag in detail.tags" :key="tag" class="px-2.5 py-1 bg-blue-50 text-blue-600 border border-blue-100 text-xs font-medium rounded-lg">
              #{{ tag }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="!loading && detail" class="p-4 border-t border-slate-200 bg-white grid grid-cols-2 gap-3 shrink-0">
        <button
          @click="handleRewrite"
          class="py-2.5 bg-primary hover:bg-primary-dark text-white font-bold rounded-lg text-sm transition-colors flex items-center justify-center gap-1.5"
        >
          <span class="material-symbols-outlined text-[18px]">magic_button</span>
          一键仿写
        </button>
        <button
          @click="close"
          class="py-2.5 bg-white text-slate-700 hover:bg-slate-50 border-2 border-slate-200 hover:border-slate-300 font-bold rounded-lg text-sm transition-colors flex items-center justify-center gap-1.5"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, nextTick, ref, watch } from 'vue'
import type { HotRankItem, SearchResultItem } from '../../types/dataCollection'

const MetricCard = defineComponent({
  props: ['icon', 'label', 'value'],
  setup(props) {
    return () =>
      h('div', { class: 'bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3' }, [
        h('div', { class: 'w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center text-slate-500' }, [
          h('span', { class: 'material-symbols-outlined text-[16px]' }, props.icon as string),
        ]),
        h('div', [
          h('p', { class: 'text-[10px] text-slate-400 font-medium mb-0.5' }, props.label as string),
          h('p', { class: 'text-base font-bold text-slate-800 font-display leading-none' }, formatNumber(props.value as number)),
        ]),
      ])
  },
})

const props = defineProps<{
  modelValue: boolean
  detail: HotRankItem | SearchResultItem | null
  loading: boolean
  savedIds?: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save-to-library', item: HotRankItem | SearchResultItem): void
  (e: 'delete-material', item: HotRankItem | SearchResultItem): void
}>()

const isAnimating = ref(false)
const isDownloading = ref(false)
const downloadCounts = ref(0)
const totalToDownload = ref(0)

const canDelete = computed(() => Boolean(props.detail && (props.detail as SearchResultItem).chainId))
const hasSourceUrl = computed(() => Boolean((props.detail?.sourceUrl || '').trim()))
const isHotRankDetail = computed(() => props.detail?.sourceScene === 'hot_rank')
const displayTitle = computed(() => String((props.detail as any)?.title || '').trim())
const displaySummary = computed(() => String((props.detail as any)?.summary || '').trim())

const shouldShowSummary = computed(() => {
  const summary = normalizeContentText(displaySummary.value)
  if (!summary) return false
  return summary !== normalizeContentText(displayTitle.value)
})

// 内容类型识别
const contentKind = computed(() => {
  if (!props.detail) return 'video'
  const d = props.detail as any
  return d.contentKind || d.content_kind || d.kind || 'video'
})

const isImage = computed(() => contentKind.value === 'image')

const primaryDownloadUrl = computed(() => {
  const d = props.detail as any
  return String(
    d?.downloadUrl ||
    d?.videoDownloadUrl ||
    d?.download_url ||
    d?.videoUrl ||
    d?.video_url ||
    d?.play_url ||
    '',
  ).trim()
})

// 规范化图片列表
const normalizedImages = computed(() => {
  if (!props.detail) return []
  const d = props.detail as any
  
  // 1. 如果后端已经直接提供了 images 数组（URL 字符串数组）
  if (Array.isArray(d.images) && d.images.length > 0) {
    return d.images.map((url: string) => ({ url, downloadUrl: url }))
  }

  const coverImages = splitMediaUrls(d.cover || d.coverUrl || d.cover_url)
  if (coverImages.length > 0) {
    return coverImages.map((url: string) => ({ url, downloadUrl: url }))
  }
  
  // 2. 解析 mediaJson / media_json
  const mj = d.mediaJson || d.media_json
  if (mj) {
    let list = []
    try {
      list = typeof mj === 'string' ? JSON.parse(mj) : mj
    } catch (e) {
      console.error('Failed to parse mediaJson:', e)
    }
    
    if (Array.isArray(list)) {
      return list.map(item => {
        // 优先使用 download_url_list 中的第一项（高清无水印）
        const dUrl = (item.download_url_list && item.download_url_list[0]) || (item.url_list && item.url_list[0]) || ''
        const vUrl = (item.url_list && item.url_list[0]) || dUrl
        return { url: vUrl, downloadUrl: dUrl }
      })
    }
  }
  
  return []
})

function splitMediaUrls(value: unknown): string[] {
  const raw = String(value ?? '').trim()
  if (!raw) return []
  return raw.split(/[,，\n]/).map((item) => item.trim()).filter(Boolean)
}

const hasDownloadUrl = computed(() => {
  if (isImage.value) return normalizedImages.value.length > 0
  return Boolean(primaryDownloadUrl.value)
})

function normalizeContentText(value: string) {
  return value.replace(/\s+/g, '').replace(/[，。,.!！?？#]/g, '').toLowerCase()
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      nextTick(() => {
        isAnimating.value = true
      })
    } else {
      isAnimating.value = false
      downloadCounts.value = 0
      totalToDownload.value = 0
    }
  },
)

function close() {
  isAnimating.value = false
  setTimeout(() => {
    emit('update:modelValue', false)
  }, 300)
}

/**
 * 批量顺序下载图文
 */
/**
 * 批量顺序下载图文
 * 采用 Fetch + Blob 方案，确保下载流真正完成后再开始下一个，有效避开浏览器拦截
 */
async function handleBatchDownload() {
  if (!normalizedImages.value.length) return
  
  try {
    isDownloading.value = true
    totalToDownload.value = normalizedImages.value.length
    downloadCounts.value = 0
    
    console.log(`[Batch] 开始流式下载任务，共 ${totalToDownload.value} 个文件...`)

    for (const [index, img] of normalizedImages.value.entries()) {
      if (!img.downloadUrl) continue
      
      const fileName = `${(props.detail as any)?.title || 'image'}_${index + 1}`
      // 这里的 await 会等到 fetch 完成并触发保存动作
      await downloadMedia(img.downloadUrl, fileName, true)
      
      downloadCounts.value = index + 1
      console.log(`[Batch] 进度展示: ${downloadCounts.value}/${totalToDownload.value}`)
      
      // 添加极短的缓冲时间以平衡磁盘 I/O和浏览器主线程
      await new Promise(resolve => setTimeout(resolve, 300))
    }
    console.log('[Batch] 全量素材顺序下载已圆满完成。')
  } catch (error) {
    console.error('[Batch] 队列下载异常:', error)
  } finally {
    setTimeout(() => {
      isDownloading.value = false
    }, 1000)
  }
}

/**
 * 单个媒体下载核心逻辑 (Fetch + Blob)
 */
async function downloadMedia(url: string, title?: string, silent = false) {
  if (!url) return
  
  try {
    if (!silent) {
      isDownloading.value = true
      console.log(`[Download] 正在发起请求: ${title}...`)
    }
    
    // 1. 获取认证 token
    const sessionJson = localStorage.getItem('ai-content-auth-session')
    let token = ''
    if (sessionJson) {
      try { token = JSON.parse(sessionJson).accessToken } catch(e){}
    }
    
    // 2. 构造代理下载 URL
    const envBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const API_BASE_URL = envBase.replace(/\/$/, '')
    const safeTitle = sanitizeDownloadTitle(title || 'media')
    const queryParams = new URLSearchParams({ url, token, title: safeTitle })
    const proxyUrl = `${API_BASE_URL}/api/v1/data-collection/proxy-download?${queryParams.toString()}`
    
    // 3. 使用 Fetch 获取数据流（取代原本的 a.click 跳转方式）
    // 这能让浏览器知道下载行为是连续的并受前端控制，不容易被判定为“自动弹框”
    const response = await fetch(proxyUrl)
    if (!response.ok) {
      throw new Error(`HTTP 异常: ${response.status}`)
    }
    
    const blob = await response.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    
    // 4. 触发本地保存
    const tempLink = document.createElement('a')
    tempLink.href = blobUrl
    // 此时已经是本地 blob 对象的下载，不需要 target="_blank"
    tempLink.download = `${safeTitle}.${blob.type.split('/')[1] || 'webp'}`
    document.body.appendChild(tempLink)
    tempLink.click()
    
    // 5. 资源清理
    document.body.removeChild(tempLink)
    window.URL.revokeObjectURL(blobUrl)
    
  } catch (error: any) {
    console.error('[Download] 失败:', error)
    if (!silent) {
      // 只有手动单下且 fetch 失败时才回退到直接打开
      window.open(url, '_blank')
    }
    throw error // 抛出异常以便 handleBatchDownload 捕获
  } finally {
    if (!silent) {
      setTimeout(() => {
        isDownloading.value = false
      }, 500)
    }
  }
}

function sanitizeDownloadTitle(title: string) {
  const cleaned = title
    .replace(/[\x00-\x1f\x7f]+/g, ' ')
    .replace(/[\\/:*?"<>|]+/g, '_')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^[._ ]+|[._ ]+$/g, '')
  return (cleaned || 'media').slice(0, 96)
}

function formatNumber(num?: number) {
  const value = Number(num ?? 0)
  if (value >= 10000) return `${(value / 10000).toFixed(1)}w`
  return String(value)
}

function handleRewrite() {
  window.alert('一键仿写功能还在开发中，敬请期待。')
}

function handleDelete() {
  if (!props.detail || !canDelete.value) return
  emit('delete-material', props.detail)
}
</script>
