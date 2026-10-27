<template>

  <div ref="shellRoot"></div>



  <router-view v-slot="{ Component }">

    <Teleport v-if="contentReady && Component" to="#content-frame">

      <component :is="Component" />

    </Teleport>

  </router-view>



  <Teleport v-if="contentReady" to="#brand-context-mount">

    <BrandContextInjector />

  </Teleport>

  <Teleport v-if="contentReady" to="#sidebar-vue-mount">

    <SidebarNav />

  </Teleport>

  <SettingsModal v-model="isSettingsOpen" :default-tab="settingsDefaultTab" />

</template>



<script setup lang="ts">
import { listBrandProducts } from '../api/brandInjection'
import { getApiBaseUrl, request } from '../api/http'
import { platformAccountApi, type AccountShortInfo } from '../api/platformAccount'
import BrandContextInjector from '../components/creation/BrandContextInjector.vue'
import SidebarNav from '../components/layout/SidebarNav.vue'

import SettingsModal from '../components/profile/SettingsModal.vue'

import { nextTick, onBeforeUnmount, onMounted, ref, provide } from 'vue'

import { Teleport } from 'vue'

import { ensureLegacyScope, renderLegacyFragment } from '../lib/legacy-dom'

import { legacyLayoutSource } from '../lib/legacy-pages'



const shellRoot = ref<HTMLElement | null>(null)

const contentReady = ref(false)



const isSettingsOpen = ref(false)

const settingsDefaultTab = ref('general')



provide('openSettings', (tabName: string = 'general') => {

  settingsDefaultTab.value = tabName

  isSettingsOpen.value = true

})

const layoutScopeName = 'layout'

const layoutFunctions = [

  'toggleSubNav',

  'openModal',

  'closeModal',

  'toggleDataSource',

  'openContentDetailModal',

  'closeContentDetailModal',

  'openScheduleModal',

  'closeScheduleModal',

  'toggleCustomTimePicker',

  'openNewPlanModal',

  'closeNewPlanModal',

  'openAddToolModal',

  'closeAddToolModal',

  'openAddPlatformModal',

  'closeAddPlatformModal',

  'toggleAuthFields',

  'openAddAgentModal',

  'closeAddAgentModal',

]

let cleanup = () => {}
let planTypeListenersBound = false
let publishTimeListenersBound = false
let videoPickerListenersBound = false
let videoPickerUiInitialized = false
let publishSubmitListenerBound = false
let publishPlatformListenersBound = false
let publishProductListenersBound = false
let publishProductOptions: BrandProductOption[] = []
let publishModalAvatarOnly = false
let publishModalPresetDraftId = ''
let publishDraftSceneFilter: AvatarDraftSceneFilter = 'all'
let publishDraftOffset = 0
const publishDraftPageSize = 10
let publishDraftTotal = 0
let publishDraftSummaries: AvatarDraftIndexRead[] = []

interface CreationDraftRead {
  draft_id: string
  title?: string | null
  content_info?: Record<string, unknown>
  digital_human_params?: Record<string, unknown>
  extracted_copy?: string | null
  rewritten_copy?: string | null
  clip_params?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

interface CreationDraftListResponse {
  items: CreationDraftRead[]
}

interface AvatarDraftIndexRead {
  draft_id: string
  user_id: number
  scene_code: 'talk' | 'sales' | 'product' | 'model' | 'clip' | string
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

type AvatarDraftSceneFilter = 'all' | 'talk' | 'sales' | 'product' | 'model' | 'clip'

interface AssetUploadTicketRead {
  upload_url: string
  file_url: string
  content_type: string
}

interface PublishAccountOption extends AccountShortInfo {
  platformType: number
}

interface PublishSelectedAccount {
  platform_type: number
  account_id: number
}

interface BrandProductOption {
  brandId: string
  brandName: string
  productName: string
}

const publishPlatformCodeMap: Record<number, string> = {
  1: 'xiaohongshu',
  2: 'bilibili',
  3: 'douyin',
  4: 'kuaishou',
}

const publishPlatformNameMap: Record<number, string> = {
  1: 'Xiaohongshu',
  2: 'Bilibili',
  3: 'Douyin',
  4: 'Kuaishou',
}

const publishDraftSceneLabelMap: Record<AvatarDraftSceneFilter, string> = {
  all: '全部',
  talk: '口播',
  sales: '卖货',
  product: '产品介绍',
  model: '模特',
  clip: '视频剪辑',
}


onMounted(async () => {

  if (!shellRoot.value) {

    return

  }



  const rendered = renderLegacyFragment({

    container: shellRoot.value,

    html: legacyLayoutSource,

    scope: layoutScopeName,

    isolateIds: false,

    executeScripts: false,

    functionNames: layoutFunctions,

    transformBodyHtml: (bodyHtml) =>
      bodyHtml
        .replace(
          /<aside id="sidebar">[\s\S]*?<\/aside>/i,
          '<aside id="sidebar"><div id="sidebar-vue-mount"></div></aside>',
        )
        .replace(
          /<iframe id="content-frame"[\s\S]*?<\/iframe>/i,
          '<div id="content-frame"></div>',
        ),

  })



  cleanup = rendered.cleanup

  registerLayoutScope()

  window.addEventListener('message', handleMessage)

  contentReady.value = true

  await nextTick()

})



onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage)

  cleanup()

})



function registerLayoutScope() {

  const scopeApi = ensureLegacyScope(layoutScopeName)



  Object.assign(scopeApi, {

    toggleSubNav,

    openModal,

    closeModal,

    toggleDataSource,

    openContentDetailModal,

    closeContentDetailModal,

    openScheduleModal,

    closeScheduleModal,

    toggleCustomTimePicker,

    openNewPlanModal,

    closeNewPlanModal,

    openAddToolModal,

    closeAddToolModal,

    openAddPlatformModal,

    closeAddPlatformModal,

    toggleAuthFields,

    openAddAgentModal,

    closeAddAgentModal,

  })

}



function handleMessage(event: MessageEvent) {

  if (event.source && event.source !== window) {

    return

  }



  if (event.data === 'openGenerationModal') {

    openModal()

    return

  }



  if (event.data === 'openAddToolModal') {

    openAddToolModal()

    return

  }



  if (event.data === 'openAddPlatformModal') {

    openAddPlatformModal()

    return

  }



  if (event.data === 'openAddAgentModal') {

    openAddAgentModal()

    return

  }



  if (event.data === 'openScheduleModal') {

    openScheduleModal()

    return

  }



  if (event.data === 'openNewPlanModal') {

    publishModalAvatarOnly = false
    publishModalPresetDraftId = ''
    openNewPlanModal()

    return

  }



  if (event.data?.type === 'openNewPlanModal') {

    publishModalAvatarOnly = event.data.mode === 'avatarOnly'
    publishModalPresetDraftId = typeof event.data.draftId === 'string' ? event.data.draftId : ''
    openNewPlanModal()

    return

  }



  if (event.data?.type === 'openContentDetailModal') {

    openContentDetailModal(event.data.data)

  }

}



function toggleSubNav(id: string) {

  byId(id)?.classList.toggle('collapsed')

}



function openModal() {

  const modal = byId('generationModal')

  const content = byId('generationModalContent')

  if (!modal || !content) return



  modal.classList.remove('hidden')

  void modal.offsetWidth

  content.classList.remove('scale-95', 'opacity-0')

  content.classList.add('scale-100', 'opacity-100')

}



function closeModal() {

  const modal = byId('generationModal')

  const content = byId('generationModalContent')

  if (!modal || !content) return



  content.classList.remove('scale-100', 'opacity-100')

  content.classList.add('scale-95', 'opacity-0')

  window.setTimeout(() => {

    modal.classList.add('hidden')

  }, 300)

}



function toggleDataSource(mode: string) {

  const section = byId('reference_data_section')

  if (!section) return

  section.style.display = mode === 'rewrite' ? 'block' : 'none'

}



function openContentDetailModal(data: Record<string, string> = {}) {

  const modal = byId('contentDetailModal')

  const backdrop = byId('detailModalBackdrop')

  const panel = byId('detailModalPanel')

  if (!modal || !backdrop || !panel) return



  text('modalTitle', data.title || '')

  text('modalId', data.id || 'ID: #---')



  const viewsText = data.views || '--'

  text('modalViews', viewsText)



  const isDash = viewsText === '-'

  text('modalLikes', isDash ? '--' : randomMetric(100, 5000))

  text('modalSaves', isDash ? '--' : randomMetric(50, 2000))

  text('modalShares', isDash ? '--' : randomMetric(10, 1000))



  const scoreText = data.score || '--'

  text('modalScore', scoreText !== '-' ? `${scoreText}/100` : '--')



  modal.classList.remove('hidden')

  void modal.offsetWidth

  backdrop.classList.remove('opacity-0')

  backdrop.classList.add('opacity-100')

  panel.classList.remove('scale-95', 'opacity-0')

  panel.classList.add('scale-100', 'opacity-100')

}



function closeContentDetailModal() {

  closeOverlay('contentDetailModal', 'detailModalBackdrop', 'detailModalPanel')

}



function openScheduleModal() {

  openOverlay('scheduleModal', 'scheduleModalBackdrop', 'scheduleModalPanel')

}



function closeScheduleModal() {

  closeOverlay('scheduleModal', 'scheduleModalBackdrop', 'scheduleModalPanel')

}



function toggleCustomTimePicker(value: string) {

  const container = byId('custom-time-picker-container')

  if (!container) return



  if (value === 'custom') {

    container.classList.remove('hidden')

    void container.offsetWidth

    container.classList.add('opacity-100')

    container.classList.remove('opacity-0', '-translate-y-2')

    return

  }



  container.classList.add('opacity-0', '-translate-y-2')

  container.classList.remove('opacity-100')

  window.setTimeout(() => {

    container.classList.add('hidden')

  }, 300)

}



function openNewPlanModal() {
  openOverlay('newPlanModal', 'newPlanModalBackdrop', 'newPlanModalPanel')
  ensureVideoPickerUi()
  ensurePublishDescriptionUi()
  ensurePublishAccountUi()
  ensurePublishProductUi()
  bindNewPlanTypeEvents()
  bindPublishTimeEvents()
  bindVideoPickerEvents()
  bindPublishPlatformEvents()
  bindPublishProductEvents()
  bindPublishSubmit()
  syncNewPlanTypeLock()
  syncNewPlanTypeFields()
  syncPublishTimeFields()
  syncPublishProductMode()
  void syncPublishAccounts()
  void loadPublishProductOptions()
  if (publishModalPresetDraftId) {
    void loadPublishDraftById(publishModalPresetDraftId)
  }
}

function ensurePublishDescriptionUi() {
  if (byId('publishDescription')) {
    return
  }
  const titleContainer = byId('publishTitle')?.parentElement
  if (!titleContainer || !titleContainer.parentElement) {
    return
  }

  const section = document.createElement('div')
  section.className = 'col-span-2'
  section.innerHTML = `
    <label class="block text-sm font-semibold text-text-main mb-1.5">描述</label>
    <textarea id="publishDescription" rows="4" placeholder="请输入发布描述，默认会带入改写文案" class="w-full px-3 py-2.5 bg-surface border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary text-text-main placeholder:text-text-secondary transition-all resize-y"></textarea>
    <p class="mt-1 text-xs text-text-secondary">标题用于短标题展示，描述会单独写入发布正文。</p>
  `.trim()
  titleContainer.insertAdjacentElement('afterend', section)
}

function closeNewPlanModal() {
  publishModalAvatarOnly = false
  publishModalPresetDraftId = ''
  closeOverlay('newPlanModal', 'newPlanModalBackdrop', 'newPlanModalPanel')
}

function syncNewPlanTypeLock() {
  const typeInputs = Array.from(document.querySelectorAll<HTMLInputElement>('input[name="plan_content_type"]'))
  const typeSection = typeInputs[0]?.closest<HTMLElement>('.space-y-4')

  if (publishModalAvatarOnly) {
    const avatarInput = typeInputs.find((input) => input.value === 'avatar_video')
    if (avatarInput) {
      avatarInput.checked = true
    }
  }

  typeInputs.forEach((input) => {
    input.disabled = publishModalAvatarOnly
  })

  if (typeSection) {
    typeSection.classList.toggle('hidden', publishModalAvatarOnly)
  }
}

function syncNewPlanTypeFields() {
  const checkedType = document.querySelector<HTMLInputElement>('input[name="plan_content_type"]:checked')
  const avatarMode = checkedType?.value === 'avatar_video'
  const avatarSection = byId('avatarPublishParams')
  const defaultSections = document.querySelectorAll<HTMLElement>('.plan-default-fields')

  if (avatarSection) {
    avatarSection.classList.toggle('hidden', !avatarMode)
  }

  defaultSections.forEach((node) => {
    node.classList.toggle('hidden', avatarMode)
  })
}

function bindNewPlanTypeEvents() {
  if (planTypeListenersBound) {
    return
  }
  const typeInputs = document.querySelectorAll<HTMLInputElement>('input[name="plan_content_type"]')
  typeInputs.forEach((input) => {
    input.addEventListener('change', syncNewPlanTypeFields)
  })
  planTypeListenersBound = true
}

function syncPublishTimeFields() {
  const checkedTimeType = document.querySelector<HTMLInputElement>('input[name="publishTimeType"]:checked')
  const scheduleMode = checkedTimeType?.value === 'schedule'
  const scheduleContainer = byId('scheduledTimeContainer')
  if (scheduleContainer) {
    scheduleContainer.classList.toggle('hidden', !scheduleMode)
  }
}

function bindPublishTimeEvents() {
  if (publishTimeListenersBound) {
    return
  }
  const timeTypeInputs = document.querySelectorAll<HTMLInputElement>('input[name="publishTimeType"]')
  timeTypeInputs.forEach((input) => {
    input.onchange = syncPublishTimeFields
  })
  publishTimeListenersBound = true
}

function bindVideoPickerEvents() {
  if (videoPickerListenersBound) {
    return
  }
  const videoFileInput = byId('publishVideoFile') as HTMLInputElement | null
  const videoPathInput = byId('publishVideoPath') as HTMLInputElement | null
  const pickerButton = byId('publishVideoPickerButton') as HTMLButtonElement | null
  const localOption = byId('publishVideoLocalOption') as HTMLButtonElement | null
  const draftOption = byId('publishVideoDraftOption') as HTMLButtonElement | null
  const draftClose = byId('publishDraftLibraryClose') as HTMLButtonElement | null
  const draftMask = byId('publishDraftLibraryMask') as HTMLDivElement | null
  if (!videoFileInput || !videoPathInput || !pickerButton || !localOption || !draftOption || !draftClose || !draftMask) return

  pickerButton.onclick = () => {
    byId('publishVideoPickerMenu')?.classList.toggle('hidden')
  }

  localOption.onclick = () => {
    byId('publishVideoPickerMenu')?.classList.add('hidden')
    videoFileInput.click()
  }

  draftOption.onclick = async () => {
    byId('publishVideoPickerMenu')?.classList.add('hidden')
    openDraftLibrary()
    await loadPublishDraftLibrary()
  }

  draftClose.onclick = closeDraftLibrary
  draftMask.onclick = (event) => {
    if (event.target === draftMask) {
      closeDraftLibrary()
    }
  }

  videoFileInput.onchange = () => {
    const file = videoFileInput.files?.[0]
    if (file) {
      void uploadPublishVideo(file)
    }
  }

  document.addEventListener('click', (event) => {
    const target = event.target as Node | null
    const menu = byId('publishVideoPickerMenu')
    if (!menu || !pickerButton || !target) return
    if (pickerButton.contains(target) || menu.contains(target)) return
    menu.classList.add('hidden')
  })

  videoPickerListenersBound = true
}

function ensureVideoPickerUi() {
  if (videoPickerUiInitialized) {
    return
  }

  const videoFileInput = byId('publishVideoFile') as HTMLInputElement | null
  const videoPathInput = byId('publishVideoPath') as HTMLInputElement | null
  const videoHint = videoPathInput?.nextElementSibling as HTMLElement | null
  if (!videoFileInput || !videoPathInput) {
    return
  }

  videoFileInput.classList.add('hidden')
  videoPathInput.classList.add('hidden')
  videoHint?.classList.add('hidden')

  const container = videoFileInput.parentElement
  if (!container) {
    return
  }

  const picker = document.createElement('div')
  picker.innerHTML = `
    <div class="relative">
      <button id="publishVideoPickerButton" type="button" class="w-full px-4 py-3 bg-surface border border-border rounded-lg text-sm text-text-main transition-all flex items-center justify-between hover:border-primary/50">
        <span id="publishVideoPickerLabel">选择视频来源</span>
        <span class="material-symbols-outlined text-[18px] text-text-secondary">expand_more</span>
      </button>
      <div id="publishVideoPickerMenu" class="hidden absolute left-0 right-0 top-[calc(100%+8px)] z-20 bg-surface border border-border rounded-xl shadow-lg p-2">
        <button id="publishVideoLocalOption" type="button" class="w-full px-3 py-2.5 rounded-lg text-left text-sm text-text-main hover:bg-surface-secondary transition-colors flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px]">upload_file</span>
          <span>本地上传</span>
        </button>
        <button id="publishVideoDraftOption" type="button" class="w-full px-3 py-2.5 rounded-lg text-left text-sm text-text-main hover:bg-surface-secondary transition-colors flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px]">video_library</span>
          <span>素材库</span>
        </button>
      </div>
    </div>
    <input id="publishVideoSource" type="hidden">
    <p id="publishVideoMeta" class="mt-2 text-xs text-text-secondary">本地上传会先上传到 MinIO，素材库会从数字人主草稿表中分页读取各场景成片。</p>
  `.trim()
  container.appendChild(picker)

  const modal = document.createElement('div')
  modal.id = 'publishDraftLibraryMask'
  modal.className = 'fixed inset-0 z-[70] hidden bg-slate-900/40 backdrop-blur-sm p-4'
  modal.innerHTML = `
    <div class="w-full max-w-3xl mx-auto mt-10 bg-surface border border-border rounded-2xl shadow-xl overflow-hidden">
      <div class="px-5 py-4 border-b border-border flex items-center justify-between">
        <div>
          <h3 class="text-base font-bold text-text-main">素材库</h3>
          <p class="text-xs text-text-secondary mt-1">从数字人主草稿表中选择你自己的成片草稿，可按场景筛选后再带入发布。</p>
        </div>
        <button id="publishDraftLibraryClose" type="button" class="p-2 rounded-lg hover:bg-surface-secondary text-text-secondary">
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>
      <div id="publishDraftLibraryFilters" class="px-4 pt-4 pb-2 flex flex-wrap gap-2 border-b border-border"></div>
      <div id="publishDraftLibraryList" class="max-h-[420px] overflow-y-auto p-4 space-y-3">
        <div class="text-sm text-text-secondary">加载中...</div>
      </div>
      <div id="publishDraftLibraryPagination" class="px-4 py-3 border-t border-border flex items-center justify-between text-xs text-text-secondary"></div>
    </div>
  `
  document.body.appendChild(modal)
  videoPickerUiInitialized = true
}

function ensurePublishAccountUi() {
  const container = byId('avatarPublishParams')
  if (!container || byId('publishAccountSelectorSection')) {
    return
  }

  const section = document.createElement('div')
  section.id = 'publishAccountSelectorSection'
  section.className = 'space-y-4 mt-4'
  section.innerHTML = `
    <div>
      <label class="block text-sm font-medium text-text-main mb-2">发布模式</label>
      <div class="grid grid-cols-2 gap-3" id="publishModeGroup">
        <label class="flex items-center gap-2 px-3 py-3 border border-border rounded-lg cursor-pointer text-sm text-text-main">
          <input type="radio" name="publishMode" value="headless" checked>
          <span>无头发布</span>
        </label>
        <label class="flex items-center gap-2 px-3 py-3 border border-border rounded-lg cursor-pointer text-sm text-text-main">
          <input type="radio" name="publishMode" value="headed">
          <span>有头发布</span>
        </label>
      </div>
      <p class="mt-1 text-xs text-text-secondary">无头发布在后台执行，有头发布会打开本机浏览器，便于观察发布过程。</p>
    </div>
    <div>
      <label class="block text-sm font-medium text-text-main mb-2">发布账号</label>
      <div id="publishAccountSelectorList" class="space-y-3">
        <div class="text-xs text-text-secondary">请先选择发布平台，再勾选具体发布账号。</div>
      </div>
    </div>
  `.trim()
  container.appendChild(section)
}

function ensurePublishProductUi() {
  const container = byId('avatarPublishParams')
  const accountSection = byId('publishAccountSelectorSection')
  if (!container || byId('publishProductSection')) {
    return
  }

  const section = document.createElement('div')
  section.id = 'publishProductSection'
  section.className = 'space-y-4 mt-4'
  section.innerHTML = `
    <div>
      <label class="block text-sm font-medium text-text-main mb-2">商品信息</label>
      <div class="grid grid-cols-2 gap-3" id="publishProductModeGroup">
        <label class="flex items-center gap-2 px-3 py-3 border border-border rounded-lg cursor-pointer text-sm text-text-main">
          <input type="radio" name="publishProductMode" value="brand" checked>
          <span>从品牌管理选择</span>
        </label>
        <label class="flex items-center gap-2 px-3 py-3 border border-border rounded-lg cursor-pointer text-sm text-text-main">
          <input type="radio" name="publishProductMode" value="manual">
          <span>手动填写</span>
        </label>
      </div>
    </div>
    <div id="publishProductBrandSection">
      <label class="block text-sm font-medium text-text-main mb-2">品牌商品</label>
      <select id="publishBrandProductSelect" class="w-full px-3 py-2.5 bg-surface border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary text-text-main transition-all">
        <option value="">请选择品牌管理中的商品</option>
      </select>
      <p id="publishBrandProductMeta" class="mt-1 text-xs text-text-secondary">选择后将自动带入品牌和商品名称。</p>
    </div>
    <div id="publishProductManualSection" class="hidden grid grid-cols-2 gap-3">
      <div>
        <label class="block text-sm font-medium text-text-main mb-2">品牌名</label>
        <input id="publishManualBrandName" type="text" placeholder="请输入品牌名" class="w-full px-3 py-2.5 bg-surface border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary text-text-main placeholder:text-text-secondary transition-all">
      </div>
      <div>
        <label class="block text-sm font-medium text-text-main mb-2">商品名</label>
        <input id="publishManualProductName" type="text" placeholder="请输入商品名" class="w-full px-3 py-2.5 bg-surface border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary text-text-main placeholder:text-text-secondary transition-all">
      </div>
    </div>
    <div>
      <label class="block text-sm font-medium text-text-main mb-2">商品链接</label>
      <input id="publishProductLink" type="text" placeholder="请输入抖音可识别的商品链接，未填写则不会挂商品" class="w-full px-3 py-2.5 bg-surface border border-border rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary text-text-main placeholder:text-text-secondary transition-all">
      <p class="mt-1 text-xs text-text-secondary">品牌管理选择只会带入品牌名和商品名；真正挂商品还需要这里的商品链接。</p>
    </div>
  `.trim()

  if (accountSection?.parentElement === container) {
    container.insertBefore(section, accountSection)
    return
  }
  container.appendChild(section)
}

function bindPublishPlatformEvents() {
  if (publishPlatformListenersBound) {
    return
  }
  const platformInputs = document.querySelectorAll<HTMLInputElement>('input[name="publish_platform"]')
  platformInputs.forEach((input) => {
    input.addEventListener('change', () => {
      void syncPublishAccounts()
    })
  })
  publishPlatformListenersBound = true
}

function bindPublishProductEvents() {
  if (publishProductListenersBound) {
    return
  }
  const inputs = document.querySelectorAll<HTMLInputElement>('input[name="publishProductMode"]')
  inputs.forEach((input) => {
    input.addEventListener('change', syncPublishProductMode)
  })
  publishProductListenersBound = true
}

function syncPublishProductMode() {
  const checkedMode = document.querySelector<HTMLInputElement>('input[name="publishProductMode"]:checked')?.value || 'brand'
  byId('publishProductBrandSection')?.classList.toggle('hidden', checkedMode !== 'brand')
  byId('publishProductManualSection')?.classList.toggle('hidden', checkedMode !== 'manual')
}

async function loadPublishProductOptions() {
  const select = byId('publishBrandProductSelect') as HTMLSelectElement | null
  const meta = byId('publishBrandProductMeta')
  if (!select) {
    return
  }

  const previousValue = select.value
  select.innerHTML = '<option value="">加载中...</option>'
  if (meta) {
    meta.textContent = '正在读取品牌管理列表...'
  }

  try {
    const response = await listBrandProducts({ pageNo: 1, pageSize: 100 })
    publishProductOptions = (response.list || []).map((item) => ({
      brandId: String(item.brandId),
      brandName: String(item.brandName || '').trim(),
      productName: String(item.productName || '').trim(),
    }))

    select.innerHTML = [
      '<option value="">请选择品牌管理中的商品</option>',
      ...publishProductOptions.map(
        (item) =>
          `<option value="${escapeHtml(item.brandId)}">${escapeHtml(`${item.brandName} - ${item.productName}`)}</option>`,
      ),
    ].join('')

    if (previousValue && publishProductOptions.some((item) => item.brandId === previousValue)) {
      select.value = previousValue
    }

    if (meta) {
      meta.textContent = publishProductOptions.length
        ? '选择后将自动带入品牌和商品名称。'
        : '品牌管理里还没有商品，可切换为手动填写。'
    }
  } catch (error) {
    select.innerHTML = '<option value="">加载失败</option>'
    if (meta) {
      meta.textContent = error instanceof Error ? error.message : '品牌商品加载失败'
    }
  }
}

async function syncPublishAccounts() {
  const list = byId('publishAccountSelectorList')
  if (!list) {
    return
  }

  const platformTypes = Array.from(document.querySelectorAll<HTMLInputElement>('input[name="publish_platform"]:checked'))
    .map((input) => Number(input.value))
    .filter((value) => Number.isFinite(value) && publishPlatformCodeMap[value])

  if (!platformTypes.length) {
    list.innerHTML = '<div class="text-xs text-text-secondary">请先选择发布平台，再勾选具体发布账号。</div>'
    return
  }

  list.innerHTML = '<div class="text-xs text-text-secondary">正在加载账号...</div>'

  try {
    const groups = await Promise.all(
      platformTypes.map(async (platformType) => {
        const platformCode = publishPlatformCodeMap[platformType]
        const response = await platformAccountApi.listAccounts(platformCode)
        const accounts = (response.list || []).map((account) => ({
          ...account,
          platformType,
        }))
        return { platformType, accounts }
      }),
    )

    list.innerHTML = groups
      .map(({ platformType, accounts }) => renderPublishAccountGroup(platformType, accounts))
      .join('')
  } catch (error) {
    list.innerHTML = `<div class="text-xs text-red-500">${escapeHtml(error instanceof Error ? error.message : '加载账号失败')}</div>`
  }
}

function renderPublishAccountGroup(platformType: number, accounts: PublishAccountOption[]) {
  const title = publishPlatformNameMap[platformType] || String(platformType)
  if (!accounts.length) {
    return `
      <div class="border border-border rounded-xl p-3">
        <div class="text-sm font-medium text-text-main">${escapeHtml(title)}</div>
        <div class="mt-1 text-xs text-text-secondary">当前平台没有可用的授权账号。</div>
      </div>
    `.trim()
  }

  const items = accounts
    .map((account) => {
      const name = account.nickname || account.accountName || `账号 ${account.accountId}`
      const status = [account.authStatus, account.sessionStatus].filter(Boolean).join(' / ')
      return `
        <label class="flex items-start gap-3 px-3 py-3 border border-border rounded-lg cursor-pointer">
          <input
            type="checkbox"
            class="mt-1"
            name="publish_account"
            value="${account.accountId}"
            data-platform-type="${platformType}"
          >
          <span class="min-w-0">
            <span class="block text-sm text-text-main">${escapeHtml(name)}</span>
            <span class="block text-xs text-text-secondary mt-1">${escapeHtml(status || 'Authorized')}</span>
          </span>
        </label>
      `.trim()
    })
    .join('')

  return `
    <div class="border border-border rounded-xl p-3 space-y-3">
      <div class="text-sm font-medium text-text-main">${escapeHtml(title)}</div>
      <div class="space-y-2">${items}</div>
    </div>
  `.trim()
}

function openDraftLibrary() {
  publishDraftOffset = 0
  byId('publishDraftLibraryMask')?.classList.remove('hidden')
}

function closeDraftLibrary() {
  byId('publishDraftLibraryMask')?.classList.add('hidden')
}

async function uploadPublishVideo(file: File) {
  const label = byId('publishVideoPickerLabel')
  const videoPathInput = byId('publishVideoPath') as HTMLInputElement | null
  const videoSourceInput = byId('publishVideoSource') as HTMLInputElement | null
  const meta = byId('publishVideoMeta')
  if (!videoPathInput || !videoSourceInput) {
    return
  }

  if (label) {
    label.textContent = `上传中：${file.name}`
  }
  if (meta) {
    meta.textContent = '正在上传到 MinIO...'
  }

  try {
    const ticket = await request<AssetUploadTicketRead>('/api/v1/uploads/ticket', {
      method: 'POST',
      body: {
        module: 'distribution',
        media_type: 'video',
        file_name: file.name,
        content_type: file.type || 'video/mp4',
      },
    })

    const uploadResponse = await fetch(ticket.upload_url, {
      method: 'PUT',
      headers: {
        'Content-Type': ticket.content_type || file.type || 'video/mp4',
      },
      body: file,
    })
    if (!uploadResponse.ok) {
      throw new Error(`upload failed: ${uploadResponse.status}`)
    }

    videoPathInput.value = ticket.file_url
    videoSourceInput.value = ticket.file_url
    if (label) {
      label.textContent = `已上传：${file.name}`
    }
    if (meta) {
      meta.textContent = '本地视频已上传到 MinIO，可以直接发布。'
    }
  } catch (error) {
    if (label) {
      label.textContent = '选择视频来源'
    }
    if (meta) {
      meta.textContent = error instanceof Error ? error.message : '上传失败'
    }
  }
}

async function loadPublishDraftLibrary() {
  const list = byId('publishDraftLibraryList')
  const filters = byId('publishDraftLibraryFilters')
  const pagination = byId('publishDraftLibraryPagination')
  if (!list) {
    return
  }
  renderPublishDraftFilters(filters)
  renderPublishDraftPagination(pagination)
  list.innerHTML = '<div class="text-sm text-text-secondary">加载中...</div>'

  try {
    const search = new URLSearchParams()
    search.set('limit', String(publishDraftPageSize))
    search.set('offset', String(publishDraftOffset))
    if (publishDraftSceneFilter !== 'all') {
      search.set('scene', publishDraftSceneFilter)
    }
    const data = await request<AvatarDraftIndexListResponse>(`/api/v1/avatar-drafts?${search.toString()}`)
    const items = data.items || []
    publishDraftSummaries = items
    publishDraftTotal = items.length < publishDraftPageSize ? publishDraftOffset + items.length : publishDraftOffset + items.length + 1
    renderPublishDraftFilters(filters)
    renderPublishDraftPagination(pagination)
    if (!items.length) {
      list.innerHTML = '<div class="text-sm text-text-secondary">当前没有可用草稿</div>'
      return
    }

    list.innerHTML = items
      .map((item) => {
        const title = escapeHtml(item.title || item.draft_id)
        const updatedAt = escapeHtml(item.updated_at || '')
        const sceneText = escapeHtml(publishDraftSceneLabelMap[(item.scene_code as AvatarDraftSceneFilter)] || item.scene_code || '未知场景')
        return `
          <button type="button" data-draft-id="${escapeHtml(item.draft_id)}" class="publish-draft-item w-full text-left p-4 border border-border rounded-xl hover:border-primary/50 hover:bg-surface-secondary transition-colors">
            <div class="flex items-center justify-between gap-3">
              <div class="text-sm font-bold text-text-main">${title}</div>
              <span class="inline-flex items-center rounded-full border border-border px-2 py-0.5 text-[11px] text-text-secondary">${sceneText}</span>
            </div>
            <div class="mt-1 text-xs text-text-secondary">${updatedAt}</div>
            <div class="mt-2 text-xs text-text-secondary">草稿状态：${escapeHtml(item.status || '-')}</div>
          </button>
        `
      })
      .join('')

    list.querySelectorAll<HTMLElement>('.publish-draft-item').forEach((node) => {
      node.onclick = () => {
        const draftId = node.dataset.draftId
        const selected = items.find((item) => item.draft_id === draftId)
        if (selected) {
          void loadPublishDraftBySummary(selected)
        }
      }
    })
  } catch (error) {
    list.innerHTML = `<div class="text-sm text-red-500">${escapeHtml(error instanceof Error ? error.message : '加载失败')}</div>`
  }
}

function renderPublishDraftFilters(container: HTMLElement | null) {
  if (!container) return
  const options: AvatarDraftSceneFilter[] = ['all', 'talk', 'sales', 'product', 'model', 'clip']
  container.innerHTML = options.map((scene) => `
    <button
      type="button"
      data-scene="${scene}"
      class="publish-draft-scene-filter px-3 py-1.5 rounded-full border text-xs transition-colors ${publishDraftSceneFilter === scene ? 'border-primary bg-primary/10 text-primary' : 'border-border text-text-secondary hover:border-primary/50'}"
    >${escapeHtml(publishDraftSceneLabelMap[scene])}</button>
  `).join('')
  container.querySelectorAll<HTMLElement>('.publish-draft-scene-filter').forEach((node) => {
    node.onclick = () => {
      const scene = (node.dataset.scene || 'all') as AvatarDraftSceneFilter
      publishDraftSceneFilter = scene
      publishDraftOffset = 0
      void loadPublishDraftLibrary()
    }
  })
}

function renderPublishDraftPagination(container: HTMLElement | null) {
  if (!container) return
  const currentCount = publishDraftSummaries.length
  const start = currentCount ? publishDraftOffset + 1 : 0
  const end = publishDraftOffset + currentCount
  const hasPrev = publishDraftOffset > 0
  const hasNext = currentCount >= publishDraftPageSize
  container.innerHTML = `
    <div>第 ${start}-${end} 条${publishDraftSceneFilter !== 'all' ? ` · ${escapeHtml(publishDraftSceneLabelMap[publishDraftSceneFilter])}` : ''}</div>
    <div class="flex items-center gap-2">
      <button id="publishDraftPrevPage" type="button" class="px-3 py-1.5 rounded-lg border border-border ${hasPrev ? 'text-text-main hover:border-primary/50' : 'text-text-tertiary cursor-not-allowed'}" ${hasPrev ? '' : 'disabled'}>上一页</button>
      <button id="publishDraftNextPage" type="button" class="px-3 py-1.5 rounded-lg border border-border ${hasNext ? 'text-text-main hover:border-primary/50' : 'text-text-tertiary cursor-not-allowed'}" ${hasNext ? '' : 'disabled'}>下一页</button>
    </div>
  `
  const prev = byId('publishDraftPrevPage') as HTMLButtonElement | null
  const next = byId('publishDraftNextPage') as HTMLButtonElement | null
  if (prev) {
    prev.onclick = () => {
      if (publishDraftOffset < publishDraftPageSize) {
        publishDraftOffset = 0
      } else {
        publishDraftOffset -= publishDraftPageSize
      }
      void loadPublishDraftLibrary()
    }
  }
  if (next) {
    next.onclick = () => {
      publishDraftOffset += publishDraftPageSize
      void loadPublishDraftLibrary()
    }
  }
}

async function loadPublishDraftBySummary(summary: AvatarDraftIndexRead) {
  const endpointMap: Record<string, string> = {
    talk: '/api/v1/creation-drafts',
    sales: '/api/v1/avatar-sales-drafts',
    product: '/api/v1/avatar-product-drafts',
    model: '/api/v1/avatar-model-drafts',
    clip: '/api/v1/avatar-clip-drafts',
  }
  const base = endpointMap[summary.scene_code] || '/api/v1/creation-drafts'
  try {
    const draft = await request<CreationDraftRead>(`${base}/${summary.draft_id}`)
    applyDraftToPublishForm(draft)
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '草稿加载失败')
  }
}

async function loadPublishDraftById(draftId: string) {
  try {
    const summary = await request<AvatarDraftIndexRead>(`/api/v1/avatar-drafts/${draftId}`)
    await loadPublishDraftBySummary(summary)
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '草稿加载失败')
  }
}

function applyDraftToPublishForm(draft: CreationDraftRead) {
  const videoUrl = resolveDraftVideoUrl(draft)
  const titleInput = byId('publishTitle') as HTMLInputElement | null
  const descriptionInput = byId('publishDescription') as HTMLTextAreaElement | null
  const topicInput = byId('publishTopics') as HTMLInputElement | null
  const taskRefInput = byId('publishTaskRef') as HTMLInputElement | null
  const videoPathInput = byId('publishVideoPath') as HTMLInputElement | null
  const videoSourceInput = byId('publishVideoSource') as HTMLInputElement | null
  const label = byId('publishVideoPickerLabel')
  const meta = byId('publishVideoMeta')

  if (videoUrl && videoPathInput && videoSourceInput) {
    videoPathInput.value = videoUrl
    videoSourceInput.value = videoUrl
  }
  if (titleInput && draft.title) {
    titleInput.value = draft.title
  }
  if (descriptionInput) {
    descriptionInput.value = resolveDraftDescription(draft)
  }
  if (topicInput) {
    topicInput.value = resolveDraftTopics(draft).join(',')
  }
  if (taskRefInput) {
    taskRefInput.value = draft.draft_id
  }
  if (label) {
    label.textContent = `已选择草稿：${draft.title || draft.draft_id}`
  }
  if (meta) {
    meta.textContent = videoUrl ? '已从草稿带入视频地址和标题。' : '这个草稿没有可用的视频地址。'
  }
  closeDraftLibrary()
}

function resolveDraftVideoUrl(draft: CreationDraftRead) {
  const digital = draft.digital_human_params || {}
  const clip = (draft as CreationDraftRead & { clip_params?: Record<string, unknown> }).clip_params || {}
  const contentInfo = draft.content_info || {}
  const candidates = [
    clip.output_url,
    clip.merged_output_url,
    clip.clipped_video_url,
    typeof clip.clipped_video_playback_path === 'string' && clip.clipped_video_playback_path.trim()
      ? `${getApiBaseUrl()}${clip.clipped_video_playback_path.trim()}`
      : '',
    contentInfo.local_video_url,
    digital.generated_video_url,
    digital.local_video_url,
    digital.video_url,
    contentInfo.video_url,
    digital.generated_video_source_url,
  ]
  for (const item of candidates) {
    const value = typeof item === 'string' ? item.trim() : ''
    if (value) {
      return value
    }
  }
  return ''
}

function resolveDraftDescription(draft: CreationDraftRead) {
  const candidates = [
    draft.rewritten_copy,
    draft.extracted_copy,
    draft.title,
    draft.content_info?.description,
    draft.content_info?.desc,
  ]
  for (const item of candidates) {
    const value = typeof item === 'string' ? item.trim() : ''
    if (value) {
      return value
    }
  }
  return ''
}

function resolveDraftTopics(draft: CreationDraftRead) {
  const contentInfo = draft.content_info || {}
  const tagList = Array.isArray(contentInfo.tags) ? contentInfo.tags : []
  const normalized = tagList
    .map((item) => String(item || '').trim().replace(/^#/, ''))
    .filter(Boolean)
  if (normalized.length) {
    return normalized
  }
  return Array.from(new Set((draft.title || '').match(/#([^\s#]+)/g)?.map((item) => item.replace(/^#/, '')) || []))
}

function escapeHtml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function resolvePublishProductPayload() {
  const checkedMode = document.querySelector<HTMLInputElement>('input[name="publishProductMode"]:checked')?.value || 'brand'
  const productLink = ((byId('publishProductLink') as HTMLInputElement | null)?.value || '').trim()
  if (checkedMode === 'manual') {
    const brandName = ((byId('publishManualBrandName') as HTMLInputElement | null)?.value || '').trim()
    const productName = ((byId('publishManualProductName') as HTMLInputElement | null)?.value || '').trim()
    return {
      brand_id: null,
      brand_name: brandName || null,
      product_name: productName || null,
      product_link: productLink || null,
    }
  }

  const selectedId = ((byId('publishBrandProductSelect') as HTMLSelectElement | null)?.value || '').trim()
  const selected = publishProductOptions.find((item) => item.brandId === selectedId)
  return {
    brand_id: selected?.brandId || null,
    brand_name: selected?.brandName || null,
    product_name: selected?.productName || null,
    product_link: productLink || null,
  }
}

function bindPublishSubmit() {
  if (publishSubmitListenerBound) {
    return
  }
  const submitButton = shellRoot.value?.querySelector<HTMLElement>('#newPlanModal button.bg-primary')
  if (!submitButton) {
    return
  }

  submitButton.onclick = async (event) => {
    event.preventDefault()
    await submitNewPlan()
  }
  publishSubmitListenerBound = true
}

async function submitNewPlan() {
  const checkedType = document.querySelector<HTMLInputElement>('input[name="plan_content_type"]:checked')
  if (checkedType?.value !== 'avatar_video') {
    closeNewPlanModal()
    return
  }

  const selectedAccounts: PublishSelectedAccount[] = Array.from(
    document.querySelectorAll<HTMLInputElement>('input[name="publish_account"]:checked'),
  )
    .map((input) => ({
      platform_type: Number(input.dataset.platformType || 0),
      account_id: Number(input.value),
    }))
    .filter((item) => Number.isFinite(item.platform_type) && Number.isFinite(item.account_id))
  const videoPath = (byId('publishVideoPath') as HTMLInputElement | null)?.value.trim() || ''
  const title = (byId('publishTitle') as HTMLInputElement | null)?.value.trim() || ''
  const description = (byId('publishDescription') as HTMLTextAreaElement | null)?.value.trim() || ''
  const rawTopics = (byId('publishTopics') as HTMLInputElement | null)?.value.trim() || ''
  const taskRef = (byId('publishTaskRef') as HTMLInputElement | null)?.value.trim() || ''
  const checkedPublishTime = document.querySelector<HTMLInputElement>('input[name="publishTimeType"]:checked')
  const checkedPublishMode = document.querySelector<HTMLInputElement>('input[name="publishMode"]:checked')
  const scheduledAt = (byId('scheduledPublishAt') as HTMLInputElement | null)?.value.trim() || ''
  const productPayload = resolvePublishProductPayload()

  if (!selectedAccounts.length) {
    window.alert('请至少选择一个发布账号')
    return
  }
  if (!videoPath) {
    window.alert('请先选择或上传视频')
    return
  }
  if (!title) {
    window.alert('请输入发布标题')
    return
  }

  const submitButton = shellRoot.value?.querySelector<HTMLElement>('#newPlanModal button.bg-primary')
  const originalText = submitButton?.innerHTML || ''
  if (submitButton) {
    submitButton.setAttribute('disabled', 'true')
    submitButton.innerHTML = '<span class="material-symbols-outlined text-[18px]">hourglass_top</span>提交中...'
  }

  try {
    const payload = {
      draft_id: taskRef.startsWith('draft_') ? taskRef : null,
      task_ref: taskRef || null,
      selected_accounts: selectedAccounts,
      video_url: videoPath,
      title,
      description: description || title,
      brand_id: productPayload.brand_id,
      brand_name: productPayload.brand_name,
      product_name: productPayload.product_name,
      product_link: productPayload.product_link,
      topics: rawTopics
        .split(/[,\n]/)
        .map((item) => item.trim().replace(/^#/, ''))
        .filter(Boolean),
      publish_time_type: checkedPublishTime?.value === 'schedule' ? 'schedule' : 'now',
      scheduled_at: checkedPublishTime?.value === 'schedule' ? scheduledAt || null : null,
      publish_mode: checkedPublishMode?.value === 'headed' ? 'headed' : 'headless',
    }

    const result = await request<{ results: Array<{ platform_name: string; downstream_message: string }> }>(
      '/api/v1/distribution/publish',
      {
        method: 'POST',
        body: payload,
      },
    )

    const successCount = (result.results || []).filter((item) => item.downstream_message).length
    window.alert(successCount > 0 ? '发送成功' : '发布任务已提交')
    closeNewPlanModal()
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '提交发布失败')
  } finally {
    if (submitButton) {
      submitButton.removeAttribute('disabled')
      submitButton.innerHTML = originalText
    }
  }
}


function openAddToolModal() {

  openOverlay('addToolModal', 'addToolModalBackdrop', 'addToolModalPanel')

}



function closeAddToolModal() {

  closeOverlay('addToolModal', 'addToolModalBackdrop', 'addToolModalPanel')

}



function openAddPlatformModal() {

  openOverlay('addPlatformModal', 'addPlatformModalBackdrop', 'addPlatformModalPanel')

}



function closeAddPlatformModal() {

  closeOverlay('addPlatformModal', 'addPlatformModalBackdrop', 'addPlatformModalPanel')

}



function toggleAuthFields(method: string) {

  const apiFields = byId('auth-api-fields')

  const oauthInfo = byId('auth-oauth-info')

  if (!apiFields || !oauthInfo) return



  if (method === 'oauth') {

    oauthInfo.classList.remove('hidden')

    oauthInfo.classList.add('flex')

    apiFields.classList.add('hidden')

    return

  }



  oauthInfo.classList.add('hidden')

  oauthInfo.classList.remove('flex')

  apiFields.classList.remove('hidden')

}



function openAddAgentModal() {

  openOverlay('addAgentModal', 'addAgentModalBackdrop', 'addAgentModalPanel')

}



function closeAddAgentModal() {

  closeOverlay('addAgentModal', 'addAgentModalBackdrop', 'addAgentModalPanel')

}



function openOverlay(modalId: string, backdropId: string, panelId: string) {

  const modal = byId(modalId)

  const backdrop = byId(backdropId)

  const panel = byId(panelId)

  if (!modal || !backdrop || !panel) return



  modal.classList.remove('hidden')

  void modal.offsetWidth

  backdrop.classList.remove('opacity-0')

  backdrop.classList.add('opacity-100')

  panel.classList.remove('scale-95', 'opacity-0')

  panel.classList.add('scale-100', 'opacity-100')

}



function closeOverlay(modalId: string, backdropId: string, panelId: string) {

  const modal = byId(modalId)

  const backdrop = byId(backdropId)

  const panel = byId(panelId)

  if (!modal || !backdrop || !panel) return



  backdrop.classList.remove('opacity-100')

  backdrop.classList.add('opacity-0')

  panel.classList.remove('scale-100', 'opacity-100')

  panel.classList.add('scale-95', 'opacity-0')

  window.setTimeout(() => {

    modal.classList.add('hidden')

  }, 300)

}



function byId(id: string) {

  return document.getElementById(id)

}



function text(id: string, value: string) {

  const element = byId(id)

  if (element) {

    element.textContent = value

  }

}



function randomMetric(min: number, max: number) {

  return Math.floor(Math.random() * (max - min + 1) + min).toLocaleString()

}

</script>

