<template>
  <div class="h-full bg-slate-50 flex flex-col font-sans text-slate-800 absolute inset-0">
    <div class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shrink-0 shadow-sm z-10">
      <div class="flex items-center gap-4">
        <button
          @click="router.back()"
          class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"
        >
          <span class="material-symbols-outlined text-[20px]">arrow_back</span>
        </button>
        <div class="h-6 w-px bg-slate-200"></div>
        <div>
          <h1 class="text-lg font-bold text-slate-900 font-display flex items-center gap-2">
            <span class="material-symbols-outlined" :class="themeColorClass">public</span>
            {{ platformName }}明细
          </h1>
          <p class="text-[11px] text-slate-400 mt-0.5">{{ platformLatestUpdateText }}</p>
        </div>
      </div>

      <div class="flex gap-3">
        <button
          v-if="supportsLinkCollection"
          @click="openLinkTaskModal"
          class="px-3 py-1.5 bg-white hover:bg-slate-50 text-primary border border-primary/30 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-sm"
        >
          <span class="material-symbols-outlined text-[16px]">link</span>
          链接采集
        </button>
        <button
          @click="openCreateTaskModal"
          class="px-3 py-1.5 bg-primary hover:bg-primary-dark text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-sm shadow-primary/20"
        >
          <span class="material-symbols-outlined text-[16px]">add</span>
          创建关键词任务
        </button>
      </div>
    </div>

    <div class="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shrink-0 z-10">
      <div class="flex bg-slate-100 p-1 rounded-lg border border-slate-200">
        <button
          v-if="supportsHotRanks"
          @click="activeTab = 'hot'"
          class="px-4 py-1.5 text-xs font-bold rounded-md transition-all flex items-center gap-1.5"
          :class="activeTab === 'hot' ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        >
          <span class="material-symbols-outlined text-[16px]">local_fire_department</span>
          全站热榜
        </button>
        <button
          @click="activeTab = 'image_library'"
          class="px-4 py-1.5 text-xs font-bold rounded-md transition-all flex items-center gap-1.5"
          :class="activeTab === 'image_library' ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        >
          <span class="material-symbols-outlined text-[16px]">image</span>
          图文素材库
        </button>
        <button
          @click="activeTab = 'video_library'"
          class="px-4 py-1.5 text-xs font-bold rounded-md transition-all flex items-center gap-1.5"
          :class="activeTab === 'video_library' ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'"
        >
          <span class="material-symbols-outlined text-[16px]">movie</span>
          视频素材库
        </button>
      </div>

      <div class="flex items-center gap-4">
        <button
          v-if="supportsHotRanks && activeTab === 'hot'"
          @click="handleRefreshHot"
          :disabled="loading"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-primary bg-primary/10 hover:bg-primary/20 rounded-lg transition-all border border-primary/20 disabled:opacity-50"
        >
          <span class="material-symbols-outlined text-[16px]" :class="{ 'animate-spin': loading }">refresh</span>
          更新热榜
        </button>

        <div v-if="isLibraryTab" class="relative">
          <input
            v-model="localSearchKeyword"
            type="text"
            :placeholder="`在${currentLibraryLabel}中搜索...`"
            class="w-72 pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all placeholder:text-slate-400"
          >
          <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[18px] text-slate-400">search</span>
          <button
            v-if="localSearchKeyword"
            @click="localSearchKeyword = ''"
            class="absolute right-1 top-1/2 -translate-y-1/2 bg-slate-200 hover:bg-slate-300 text-slate-600 px-2 py-0.5 rounded text-[10px] font-bold transition-colors"
          >
            清空
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto pt-1.5 px-6 pb-6 relative">
      <div
        v-if="taskRunning"
        class="mb-4 bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800 flex items-center gap-2"
      >
        <span class="material-symbols-outlined animate-spin text-blue-600">progress_activity</span>
        <span>{{ taskNotice }}</span>
      </div>

      <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl p-8 flex flex-col items-center justify-center text-center">
        <span class="material-symbols-outlined text-4xl text-red-400 gap-2 mb-3">error</span>
        <h3 class="font-bold text-red-800 mb-1">获取数据失败</h3>
        <p class="text-xs text-red-600 mb-4">{{ error.message }}</p>
        <button @click="loadData" class="px-4 py-2 bg-white text-red-600 border border-red-200 hover:bg-red-50 font-bold rounded-lg text-sm shadow-sm transition-colors flex items-center gap-2">
          <span class="material-symbols-outlined text-[16px]">refresh</span>
          重试
        </button>
      </div>

      <template v-else>
        <HotRankList
          v-if="supportsHotRanks && activeTab === 'hot'"
          :data="hotData"
          :loading="loading"
          @view-detail="openDetail"
        />

        <div v-else class="flex flex-col h-full">
          <!-- 预览模式工具栏 - 吸顶显示 -->
          <div v-if="searchMode === 'staging'" class="sticky top-0 z-20 -mx-6 px-6 py-2 mb-4 bg-white/95 backdrop-blur-sm border-b border-slate-200 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-blue-500">inventory_2</span>
                <div class="text-sm">
                  正在预览 <strong>"{{ stagingKeyword }}"</strong> 的结果 (共 {{ currentListData.length }} 条)
                </div>
              </div>
              <button @click="backToLibrary" class="text-xs font-bold text-blue-600 hover:text-blue-800 underline flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">arrow_back</span>
                返回我的素材库
              </button>
            </div>

            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <button @click="toggleSelectAll" class="text-xs font-bold text-slate-600 hover:text-primary flex items-center gap-1">
                  <span class="material-symbols-outlined text-[18px]">{{ isAllSelected ? 'check_box' : 'check_box_outline_blank' }}</span>
                  {{ isAllSelected ? '取消全选' : '本页全选' }}
                </button>
                <div class="h-4 w-px bg-slate-200"></div>
                <div class="text-[11px] text-slate-500">已选中 <span class="font-bold text-primary">{{ selectedTaskIds.length }}</span> 项</div>
              </div>

              <button
                @click="handleBatchSave"
                :disabled="selectedTaskIds.length === 0 || loading"
                class="px-3 py-1 bg-primary text-white text-[11px] font-bold rounded-lg hover:bg-primary-dark transition-all flex items-center gap-1 shadow-sm disabled:opacity-30"
              >
                <span class="material-symbols-outlined text-[14px]">download</span>
                批量保留入库
              </button>
            </div>
          </div>

          <SearchResultList
            :data="currentListData"
            :loading="loading"
            :stagingMode="searchMode === 'staging'"
            :savedIds="savedIds"
            :savingIds="savingIds"
            v-model:selectedIds="selectedTaskIds"
            @view-detail="openDetail"
            @save="saveToLibrary"
          />
        </div>
      </template>
    </div>

    <div v-if="showTaskModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div class="bg-white rounded-xl shadow-xl w-[520px] overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 class="font-bold text-slate-800">创建关键词任务</h3>
          <button @click="showTaskModal = false" class="text-slate-400 hover:text-slate-600">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">搜索关键词</label>
            <input
              v-model="taskForm.keyword"
              @keyup.enter="submitCreateTask"
              type="text"
              placeholder="输入关键词，例如 COS"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm"
            >
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">采集内容类型</label>
            <div class="grid grid-cols-2 gap-3">
              <button
                type="button"
                @click="taskForm.contentKind = 'video'"
                :class="taskForm.contentKind === 'video' ? 'border-primary bg-blue-50 text-primary shadow-sm' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'"
                class="rounded-lg border px-4 py-3 text-left transition-colors"
              >
                <span class="material-symbols-outlined text-[18px] align-[-4px] mr-1">movie</span>
                <span class="text-sm font-semibold">视频</span>
              </button>
              <button
                v-if="supportsImageContent"
                type="button"
                @click="taskForm.contentKind = 'image'"
                :class="taskForm.contentKind === 'image' ? 'border-primary bg-blue-50 text-primary shadow-sm' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'"
                class="rounded-lg border px-4 py-3 text-left transition-colors"
              >
                <span class="material-symbols-outlined text-[18px] align-[-4px] mr-1">image</span>
                <span class="text-sm font-semibold">图文</span>
              </button>
            </div>
          </div>

          <p class="text-[11px] text-slate-500">默认每次采集 20 条，内容类型会透传到抖音搜索条件。</p>
        </div>
        <div class="px-6 py-4 bg-slate-50 flex justify-end gap-3">
          <button @click="showTaskModal = false" class="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">取消</button>
          <button @click="submitCreateTask" :disabled="!taskForm.keyword.trim() || taskRunning" class="px-4 py-2 text-sm font-medium bg-primary text-white disabled:opacity-50 hover:bg-primary-dark rounded-lg transition-colors shadow-sm shadow-primary/20">
            {{ taskRunning ? '采集中...' : '开始采集' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showLinkTaskModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div class="bg-white rounded-xl shadow-xl w-[560px] overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h3 class="font-bold text-slate-800">通过链接采集</h3>
          <button @click="showLinkTaskModal = false" class="text-slate-400 hover:text-slate-600">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">抖音视频/图文链接</label>
            <textarea
              v-model="linkTaskForm.url"
              rows="4"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm resize-none"
              placeholder="例如：https://www.douyin.com/video/7623265981984558376?modeFrom=userPost..."
            ></textarea>
          </div>
          <p class="text-[11px] text-slate-500">系统会启动 detail 爬虫任务，完成后自动绑定到当前用户素材库。</p>
        </div>
        <div class="px-6 py-4 bg-slate-50 flex justify-end gap-3">
          <button @click="showLinkTaskModal = false" class="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors">取消</button>
          <button @click="submitLinkTask" :disabled="!linkTaskForm.url.trim() || taskRunning" class="px-4 py-2 text-sm font-medium bg-primary text-white disabled:opacity-50 hover:bg-primary-dark rounded-lg transition-colors shadow-sm shadow-primary/20">
            开始采集
          </button>
        </div>
      </div>
    </div>

    <ContentDetailDrawer
      v-model="drawerVisible"
      :detail="drawerData"
      :loading="drawerLoading"
      :savedIds="savedIds"
      @save-to-library="saveToLibrary"
      @delete-material="deleteFromDrawer"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getPlatformDetail,
  getPlatformHotRanks,
  getKeywordTaskResults,
  createDetailUrlTask,
  createKeywordTask,
  getContentDetail,
  collectStagedResults,
  getMyContent,
  deleteMaterialRelation
} from '../../api/dataCollection'
import { taskStore } from '../../data-collection/taskStore'
import { ApiError } from '../../api/http'
import ContentDetailDrawer from '../../components/data-collection/ContentDetailDrawer.vue'
import HotRankList from '../../components/data-collection/HotRankList.vue'
import SearchResultList from '../../components/data-collection/SearchResultList.vue'
import type { ContentDetail, HotRankItem, SearchResultItem } from '../../types/dataCollection'

type TabKey = 'hot' | 'image_library' | 'video_library'

const router = useRouter()
const route = useRoute()

const PLATFORM_META: Record<string, {
  name: string
  themeClass: string
  supportsHotRanks: boolean
  supportsLinkCollection: boolean
  supportsContentKinds: Array<'image' | 'video'>
}> = {
  douyin: { name: '\u6296\u97f3', themeClass: 'text-gray-900', supportsHotRanks: true, supportsLinkCollection: true, supportsContentKinds: ['image', 'video'] },
  xiaohongshu: { name: '\u5c0f\u7ea2\u4e66', themeClass: 'text-red-500', supportsHotRanks: false, supportsLinkCollection: false, supportsContentKinds: ['image', 'video'] },
  kuaishou: { name: '\u5feb\u624b', themeClass: 'text-orange-500', supportsHotRanks: false, supportsLinkCollection: false, supportsContentKinds: ['video'] },
  bilibili: { name: 'B\u7ad9', themeClass: 'text-sky-500', supportsHotRanks: false, supportsLinkCollection: false, supportsContentKinds: ['video'] },
}

const platformCode = computed(() => String(route.query.code ?? 'douyin'))
const platformMeta = computed(() => PLATFORM_META[platformCode.value] ?? {
  name: '\u5e73\u53f0',
  themeClass: 'text-primary',
  supportsHotRanks: false,
  supportsLinkCollection: false,
  supportsContentKinds: ['image', 'video'] as Array<'image' | 'video'>,
})
const platformName = computed(() => platformMeta.value.name)
const themeColorClass = computed(() => platformMeta.value.themeClass)
const supportsHotRanks = computed(() => platformMeta.value.supportsHotRanks)
const supportsLinkCollection = computed(() => platformMeta.value.supportsLinkCollection)
const supportsImageContent = computed(() => platformMeta.value.supportsContentKinds.includes('image'))
const platformLatestUpdateText = ref('\u4e0a\u6b21\u540c\u6b65: \u6682\u65e0')

const activeTab = ref<TabKey>('hot')
const isLibraryTab = computed(() => activeTab.value === 'image_library' || activeTab.value === 'video_library')
const currentLibraryKind = computed<'image' | 'video'>(() => (activeTab.value === 'video_library' ? 'video' : 'image'))
const currentLibraryLabel = computed(() => (currentLibraryKind.value === 'image' ? '图文素材库' : '视频素材库'))

const loading = ref(false)
const taskRunning = ref(false)
const taskNotice = ref('')
const lastSubmittedTaskNo = ref('')
const lastSubmittedLinkTaskNo = ref('')
const error = ref<Error | null>(null)

const hotData = ref<HotRankItem[]>([])
const currentSnapshotNo = ref<string | undefined>(undefined)

const searchMode = ref<'library' | 'staging'>('library')
const stagingKeyword = ref('')
const stagingTaskNo = ref('')
const stagingKind = ref<'image' | 'video'>('image')
const stagingData = ref<SearchResultItem[]>([])
const libraryData = ref<SearchResultItem[]>([])
const selectedTaskIds = ref<string[]>([])
const savingIds = ref<string[]>([])

const localSearchKeyword = ref('')
const displayKeyword = computed(() => localSearchKeyword.value.trim().toLowerCase())
const displayedLibraryData = computed(() => {
  if (!displayKeyword.value) return libraryData.value
  return libraryData.value.filter((item) => {
    return (
      item.title.toLowerCase().includes(displayKeyword.value) ||
      item.summary.toLowerCase().includes(displayKeyword.value) ||
      (item.keyword ?? '').toLowerCase().includes(displayKeyword.value)
    )
  })
})
const displayedStagingData = computed(() => {
  if (!displayKeyword.value) return stagingData.value
  return stagingData.value.filter((item) => {
    return (
      item.title.toLowerCase().includes(displayKeyword.value) ||
      item.summary.toLowerCase().includes(displayKeyword.value) ||
      (item.keyword ?? '').toLowerCase().includes(displayKeyword.value)
    )
  })
})
const currentListData = computed(() => (searchMode.value === 'staging' ? displayedStagingData.value : displayedLibraryData.value))
const savedIds = computed(() => libraryData.value.map((item) => item.id))
const isAllSelected = computed(() => {
  if (currentListData.value.length === 0) return false
  const unsavedItems = currentListData.value.filter(it => !savedIds.value.includes(it.id))
  if (unsavedItems.length === 0) return false
  return unsavedItems.every(it => selectedTaskIds.value.includes(it.id))
})

const showTaskModal = ref(false)
const taskForm = reactive({
  keyword: '',
  contentKind: 'video' as 'image' | 'video',
})
const showLinkTaskModal = ref(false)
const linkTaskForm = reactive({
  url: '',
})

const drawerVisible = ref(false)
const drawerLoading = ref(false)
const drawerData = ref<HotRankItem | SearchResultItem | null>(null)

function openCreateTaskModal() {
  taskForm.keyword = ''
  const defaultKind = isLibraryTab.value ? currentLibraryKind.value : 'video'
  taskForm.contentKind = !supportsImageContent.value && defaultKind === 'image' ? 'video' : defaultKind
  showTaskModal.value = true
}

function openLinkTaskModal() {
  linkTaskForm.url = ''
  showLinkTaskModal.value = true
}

function handleCrawlerAuthError(err: unknown, fallbackMessage: string) {
  const message = err instanceof ApiError || err instanceof Error ? err.message : fallbackMessage
  error.value = new Error(message)
  taskNotice.value = ''

  if (err instanceof ApiError && /Cookie|授权中心|授权/.test(message)) {
    const shouldGo = window.confirm(`${message}\n\n是否现在前往平台授权中心？`)
    if (shouldGo) {
      router.push({ name: 'platform' })
    }
    return
  }

  window.alert(message)
}

async function loadPlatformMeta() {
  const detail = await getPlatformDetail(platformCode.value)
  const latest = detail.lastSyncAt || detail.latestUpdateTime || '暂无'
  platformLatestUpdateText.value = `上次同步: ${latest}`
}

async function loadHot(options: { force?: boolean } = {}) {
  const data = await getPlatformHotRanks(platformCode.value, {
    pageNo: 1,
    pageSize: 50,
    sortBy: 'heat',
    force: options.force
  })
  currentSnapshotNo.value = data.snapshotNo ?? undefined
  hotData.value = data.list.map((item) => ({
    ...item,
    sourceScene: 'hot_rank',
    sourceRefNo: item.snapshotNo || currentSnapshotNo.value,
  }))
  return data
}

async function handleRefreshHot() {
  if (loading.value) return
  loading.value = true
  error.value = null
  try {
    const data = await loadHot({ force: true })
    if (data.refreshing) {
      for (const delay of [5000, 15000]) {
        window.setTimeout(() => {
          if (activeTab.value === 'hot') {
            void loadHot()
          }
        }, delay)
      }
    }
  } catch (err) {
    error.value = err as Error
    window.alert(err instanceof ApiError ? err.message : '更新热榜失败')
  } finally {
    loading.value = false
  }
}

async function loadLibrary(kind: 'image' | 'video') {
  const page = await getMyContent(platformCode.value, kind)
  libraryData.value = page.list
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    await loadPlatformMeta()
    if (activeTab.value === 'hot' && supportsHotRanks.value) {
      await loadHot()
    } else {
      if (activeTab.value === 'hot') {
        activeTab.value = supportsImageContent.value ? 'image_library' : 'video_library'
      }
      await loadLibrary(currentLibraryKind.value)
    }
  } catch (err) {
    error.value = err as Error
  } finally {
    loading.value = false
  }
}

async function loadStagingResults(taskNo: string, keyword: string) {
  loading.value = true
  try {
    const resultPage = await getKeywordTaskResults(taskNo, {
      pageNo: 1,
      pageSize: 100,
    })

    const normalizedResults = resultPage.list.map((item) => ({
      ...item,
      sourceScene: 'keyword_search' as const,
      sourceRefNo: taskNo,
    }))

    stagingKeyword.value = keyword
    stagingTaskNo.value = taskNo
    stagingKind.value = (normalizedResults[0]?.contentKind ?? 'image') as 'image' | 'video'
    stagingData.value = normalizedResults
    activeTab.value = stagingKind.value === 'video' ? 'video_library' : 'image_library'
    searchMode.value = 'staging'
  } catch (err) {
    console.error('Failed to load staging results', err)
    window.alert('加载检索结果失败，可能已过期')
  } finally {
    loading.value = false
  }
}

async function submitCreateTask() {
  const keyword = taskForm.keyword.trim()
  if (!keyword || taskRunning.value) return
  showTaskModal.value = false
  taskRunning.value = true
  taskNotice.value = `正在启动“${keyword}”的采集任务...`
  error.value = null

  try {
    // 移除授权账户就绪检查，直接走爬虫账号池逻辑
    const taskSummary = await createKeywordTask({
      platformCode: platformCode.value,
      keyword,
      contentKind: taskForm.contentKind,
    })

    taskStore.addTask({
      taskNo: taskSummary.taskNo,
      keyword,
      platformCode: platformCode.value
    })
    lastSubmittedTaskNo.value = taskSummary.taskNo

    taskNotice.value = `采集任务已在后台启动！`
    window.setTimeout(() => {
      taskNotice.value = ''
    }, 3000)

  } catch (err) {
    handleCrawlerAuthError(err, '启动关键词采集失败')
  } finally {
    taskRunning.value = false
  }
}

async function submitLinkTask() {
  const url = linkTaskForm.url.trim()
  if (!url || taskRunning.value) return
  showLinkTaskModal.value = false
  taskRunning.value = true
  taskNotice.value = '正在启动链接采集任务...'
  error.value = null

  try {
    const taskSummary = await createDetailUrlTask({
      platformCode: platformCode.value,
      url,
    })

    taskStore.addTask({
      taskNo: taskSummary.taskNo,
      keyword: '链接采集',
      platformCode: platformCode.value,
      taskKind: 'detail_url',
      sourceUrl: url,
    })
    lastSubmittedLinkTaskNo.value = taskSummary.taskNo

    taskNotice.value = '链接采集任务已在后台启动，完成后会自动加入素材库。'
    window.setTimeout(() => {
      taskNotice.value = ''
    }, 3000)
  } catch (err) {
    handleCrawlerAuthError(err, '启动链接采集失败')
  } finally {
    taskRunning.value = false
  }
}

async function backToLibrary() {
  searchMode.value = 'library'
  await loadLibrary(currentLibraryKind.value)
}

async function saveToLibrary(item: HotRankItem | SearchResultItem) {
  const sourceScene = item.sourceScene ?? ('rank' in item ? 'hot_rank' : 'keyword_search')
  const sourceRefNo = item.sourceRefNo ?? (sourceScene === 'hot_rank' ? currentSnapshotNo.value : stagingTaskNo.value)
  if (!sourceRefNo) return

  const id = (item as any).contentId || (item as any).aweme_id || item.id
  if (!id || savingIds.value.includes(id)) return

  savingIds.value.push(id)
  try {
    await collectStagedResults({
      taskId: sourceRefNo,
      platform: platformCode.value,
      selectedIds: [id],
    })

    // 从选中列表中移除
    selectedTaskIds.value = selectedTaskIds.value.filter(sid => sid !== id)
    await loadLibrary(currentLibraryKind.value)
    if (searchMode.value === 'staging') {
      stagingData.value = stagingData.value.map((row) => (
        row.id === id || (row as any).contentId === id || (row as any).aweme_id === id
          ? { ...row, importStatus: 'imported' }
          : row
      ))
    }
  } catch (err) {
    console.error(err)
    const message = err instanceof ApiError ? err.message : '入库失败，请稍后重试'
    window.alert(message)
  } finally {
    savingIds.value = savingIds.value.filter(sid => sid !== id)
  }
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedTaskIds.value = []
  } else {
    selectedTaskIds.value = currentListData.value
      .filter(it => !savedIds.value.includes(it.id))
      .map(it => it.id)
  }
}

async function handleBatchSave() {
  if (selectedTaskIds.value.length === 0 || loading.value) return
  const count = selectedTaskIds.value.length
  if (!window.confirm(`确认将选中的 ${count} 条内容保留并存入素材库吗？`)) return

  loading.value = true
  try {
    const res = await collectStagedResults({
      taskId: stagingTaskNo.value,
      platform: platformCode.value,
      selectedIds: selectedTaskIds.value
    })

    // 成功提示
    window.alert(`入库成功：已将 ${res.collectedCount} 条内容转入${currentLibraryLabel.value}`)

    // 清空选中并刷新
    selectedTaskIds.value = []
    await loadLibrary(currentLibraryKind.value)
    if (searchMode.value === 'staging') {
      const resp = await getKeywordTaskResults(stagingTaskNo.value)
      stagingData.value = resp.list.map(it => ({ ...it, sourceScene: 'keyword_search', sourceRefNo: stagingTaskNo.value }))
    }
  } catch (err) {
    window.alert(err instanceof Error ? err.message : '批量入库失败')
  } finally {
    loading.value = false
  }
}

async function openDetail(item: HotRankItem | SearchResultItem) {
  drawerVisible.value = true
  drawerLoading.value = true
  try {
    const detail = await getContentDetail(item.contentId || item.id, {
      platformCode: platformCode.value,
      contentKind: item.contentKind,
      sourceScene: item.sourceScene,
      sourceRefNo: item.sourceRefNo,
      snapshotNo: (item as any).snapshotNo,
    })
    drawerData.value = toDrawerItem(detail, item)
  } catch (err) {
    console.error(err)
    drawerData.value = item
  } finally {
    drawerLoading.value = false
  }
}

function toDrawerItem(detail: ContentDetail | null, source: HotRankItem | SearchResultItem): HotRankItem | SearchResultItem {
  if (!detail) return source
  const sourceScene = (detail.sourceScene as 'keyword_search' | 'hot_rank' | undefined) ?? source.sourceScene
  const extra = (detail.extraJson && typeof detail.extraJson === 'object' ? detail.extraJson : {}) as Record<string, unknown>
  const isHot = sourceScene === 'hot_rank' || 'rank' in source
  const fallbackLikes = isHot ? Number(extra.videoCount ?? 0) : 0
  const fallbackComments = isHot ? Number(extra.discussVideoCount ?? 0) : 0
  const fallbackShares = isHot ? Number(extra.articleDetailCount ?? 0) : 0
  const fallbackViews = isHot ? Number(extra.roomCount ?? 0) : 0
  const imageUrls = splitMediaUrls(detail.images ?? detail.coverUrl ?? ('cover' in source ? source.cover : ''))
  const base: SearchResultItem = {
    id: detail.contentId,
    contentId: detail.contentId,
    keyword: 'keyword' in source ? source.keyword : undefined,
    title: detail.title || source.title,
    summary: detail.summary || source.summary,
    cover: (imageUrls[0] || detail.coverUrl || ('cover' in source ? source.cover : null) || ''),
    author: detail.authorName || ('author' in source ? source.author : ''),
    authorName: detail.authorName || ('author' in source ? source.author : ''),
    publishTime: detail.publishAt || source.publishTime,
    likes: Number(detail.likeCount ?? source.likes ?? fallbackLikes),
    comments: Number(detail.commentCount ?? source.comments ?? fallbackComments),
    shares: Number(detail.shareCount ?? source.shares ?? fallbackShares),
    collects: Number(detail.collectCount ?? ('collects' in source ? source.collects : 0)),
    tags: detail.tagList ?? source.tags,
    sourceUrl: resolveSourceUrl(detail, source),
    sourceType: source.sourceType,
    platformCode: detail.platformCode || source.platformCode,
    contentKind: (detail.contentKind as 'image' | 'video') || source.contentKind,
    importStatus: (detail.importStatus as 'not_imported' | 'imported' | 'importing') ?? source.importStatus,
    materialId: detail.materialId ?? source.materialId ?? null,
    chainId: detail.chainId ?? source.chainId ?? null,
    sourceScene,
    sourceRefNo: source.sourceRefNo,
    downloadUrl: resolveDownloadUrl(detail, extra),
    mediaJson: detail.mediaJson,
    extraJson: detail.extraJson,
    rawJson: detail.rawJson,
    images: imageUrls.length > 0 ? imageUrls : detail.images,
  }
  if (!isHot) return base
  return {
    ...base,
    rank: Number('rank' in source ? source.rank : extra.rank ?? 0),
    hotValue: Number('hotValue' in source ? source.hotValue : extra.hotValue ?? 0),
    views: Number('views' in source ? source.views : fallbackViews),
    snapshotNo: ('snapshotNo' in source ? source.snapshotNo : undefined) ?? (typeof extra.snapshotNo === 'string' ? extra.snapshotNo : undefined),
  } as HotRankItem
}

function splitMediaUrls(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean)
  }
  const raw = String(value ?? '').trim()
  if (!raw) return []
  return raw.split(/[,，\n]/).map((item) => item.trim()).filter(Boolean)
}

function resolveSourceUrl(detail: ContentDetail, source: HotRankItem | SearchResultItem): string {
  const directUrl = String(detail.contentUrl ?? source.sourceUrl ?? '').trim()
  if (directUrl) return directUrl
  const contentId = String(detail.contentId || source.contentId || source.id).trim()
  if (!contentId) return ''
  const contentKind = String(detail.contentKind ?? source.contentKind ?? '').toLowerCase()
  if (platformCode.value === 'bilibili') {
    return `https://www.bilibili.com/video/${encodeURIComponent(contentId)}`
  }
  if (platformCode.value === 'kuaishou') {
    return `https://www.kuaishou.com/short-video/${encodeURIComponent(contentId)}`
  }
  if (platformCode.value === 'xiaohongshu') {
    return `https://www.xiaohongshu.com/explore/${encodeURIComponent(contentId)}`
  }
  if (contentKind === 'video') {
    return `https://www.douyin.com/video/${encodeURIComponent(contentId)}`
  }
  const title = String(detail.title || source.title || contentId).trim()
  return `https://www.douyin.com/search/${encodeURIComponent(title)}`
}

function resolveDownloadUrl(detail: ContentDetail, extra: Record<string, unknown>): string | undefined {
  const directUrl = (
    detail.downloadUrl ||
    (detail as any).videoDownloadUrl ||
    (detail as any).video_download_url ||
    (detail as any).videoUrl ||
    (detail as any).video_url ||
    ''
  ).trim()
  if (directUrl) return directUrl

  const raw = (detail.rawJson && typeof detail.rawJson === 'object' ? detail.rawJson : {}) as any
  const rawDirectUrl = String(raw.video_download_url || raw.download_url || raw.play_url || '').trim()
  if (rawDirectUrl) return rawDirectUrl

  const playAddr =
    extra.play_addr ||
    raw.play_addr ||
    (raw.raw_data && raw.raw_data.play_addr) ||
    (raw.raw_data && raw.raw_data.aweme_info && raw.raw_data.aweme_info.video && raw.raw_data.aweme_info.video.play_addr) ||
    (raw.video && raw.video.play_addr) ||
    (raw.raw_data && raw.raw_data.video && raw.raw_data.video.play_addr)

  if (playAddr && Array.isArray(playAddr.url_list)) {
    const list = playAddr.url_list
    if (list.length >= 3) return list[2]
    if (list.length > 0) return list[0]
  }
  return undefined
}

async function deleteFromDrawer(item: HotRankItem | SearchResultItem) {
  if (!item.chainId) return
  const confirmed = window.confirm('确认从素材库移除此内容吗？仅删除当前用户关系，不会删除主素材。')
  if (!confirmed) return
  try {
    await deleteMaterialRelation(item.chainId)
    drawerVisible.value = false
    drawerData.value = null
    libraryData.value = libraryData.value.filter((it) => it.chainId !== item.chainId)
    stagingData.value = stagingData.value.map((it) => (it.id === item.id ? { ...it, importStatus: 'not_imported', chainId: null } : it))
  } catch (err) {
    console.error(err)
    window.alert('删除失败，请稍后重试')
  }
}

watch(activeTab, async (tab) => {
  if (tab !== 'hot' && searchMode.value === 'staging' && currentLibraryKind.value !== stagingKind.value) {
    searchMode.value = 'library'
  }
  await loadData()
})

// 自动刷新逻辑：监听任务状态，完成采集后立刻加载结果
watch(() => taskStore.recentTasks, (newRecent, oldRecent) => {
  if (newRecent.length > (oldRecent?.length || 0)) {
    const latest = newRecent[0]
    if (
      latest.platformCode === platformCode.value
      && latest.taskKind === 'detail_url'
      && latest.status === 'completed'
      && (latest.taskNo === lastSubmittedLinkTaskNo.value || latest.sourceUrl)
    ) {
      const kind = latest.contentKind || currentLibraryKind.value
      lastSubmittedLinkTaskNo.value = ''
      activeTab.value = kind === 'video' ? 'video_library' : 'image_library'
      searchMode.value = 'library'
      stagingTaskNo.value = ''
      stagingKeyword.value = ''
      stagingData.value = []
      selectedTaskIds.value = []
      void loadLibrary(kind)
      return
    }
    // 如果完成的任务正是当前平台且是刚刚启动采集的那个关键词
    if (latest.platformCode === platformCode.value && latest.taskNo === lastSubmittedTaskNo.value) {
      loadStagingResults(latest.taskNo, latest.keyword)
      lastSubmittedTaskNo.value = ''
      taskNotice.value = ''
    }
  }
}, { deep: true })

onMounted(async () => {
  const queryKind = String(route.query.contentKind || '').toLowerCase()
  if (queryKind === 'image' || queryKind === 'video') {
    activeTab.value = queryKind === 'video' ? 'video_library' : 'image_library'
    searchMode.value = 'library'
  } else if (!supportsHotRanks.value) {
    activeTab.value = supportsImageContent.value ? 'image_library' : 'video_library'
  }
  await loadData()
})

watch(
  () => platformCode.value,
  async () => {
    searchMode.value = 'library'
    stagingTaskNo.value = ''
    stagingKeyword.value = ''
    stagingData.value = []
    selectedTaskIds.value = []
    activeTab.value = supportsHotRanks.value ? 'hot' : (supportsImageContent.value ? 'image_library' : 'video_library')
    await loadData()
  }
)

// 监听路由参数变化
watch(
  () => route.query,
  (query) => {
    const restoreTaskNo = query.restoreTaskNo as string
    const restoreKeyword = query.restoreKeyword as string

    if (restoreTaskNo && restoreKeyword) {
      loadStagingResults(restoreTaskNo, restoreKeyword)
      const newQuery = { ...query }
      delete newQuery.restoreTaskNo
      delete newQuery.restoreKeyword
      router.replace({ path: route.path, query: newQuery })
    }
  },
  { immediate: true }
)
</script>
