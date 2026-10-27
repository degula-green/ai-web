<template>
  <div ref="hostRef" class="h-full">
    <LegacyPageHost :html="page.html" :scope="page.scope" :title="page.title" @ready="handleReady" />
  </div>

  <div
    v-if="detailVisible && selectedDetail"
    class="fixed inset-0 z-[80] flex items-center justify-center bg-slate-900/35 px-4"
    @click.self="closeDetail"
  >
    <div class="w-full max-w-xl rounded-2xl border border-slate-200 bg-white shadow-2xl">
      <div class="flex items-start justify-between border-b border-slate-100 px-6 py-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Publish Detail</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">{{ selectedDetail.title }}</h3>
        </div>
        <button
          class="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          @click="closeDetail"
        >
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>

      <div class="grid gap-5 px-6 py-5 md:grid-cols-[112px,1fr]">
        <div class="h-28 w-28 overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
          <img
            v-if="selectedDetail.cover_url"
            :src="selectedDetail.cover_url"
            :alt="selectedDetail.title"
            class="h-full w-full object-cover"
          />
          <div v-else class="flex h-full w-full items-center justify-center text-slate-300">
            <span class="material-symbols-outlined text-[28px]">image</span>
          </div>
        </div>

        <div class="grid gap-3 text-sm">
          <div class="flex flex-wrap gap-2">
            <span class="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-semibold text-white">
              {{ selectedDetail.platform_name }}
            </span>
            <span class="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-600">
              {{ getStatusLabel(selectedDetail.status) }}
            </span>
          </div>

          <div class="grid gap-2 text-slate-600">
            <div><span class="font-medium text-slate-900">账号：</span>{{ selectedDetail.account_name }}</div>
            <div><span class="font-medium text-slate-900">时间：</span>{{ formatDetailTime(selectedDetail) }}</div>
            <div v-if="selectedDetail.request_group_id"><span class="font-medium text-slate-900">分组：</span>{{ selectedDetail.request_group_id }}</div>
            <div v-if="selectedDetail.status_message"><span class="font-medium text-slate-900">说明：</span>{{ selectedDetail.status_message }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div
    v-if="dayItemsVisible"
    class="fixed inset-0 z-[79] flex items-center justify-center bg-slate-900/35 px-4"
    @click.self="closeDayItems"
  >
    <div class="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white shadow-2xl">
      <div class="flex items-start justify-between border-b border-slate-100 px-6 py-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Schedule Items</p>
          <h3 class="mt-1 text-lg font-bold text-slate-900">{{ dayItemsTitle }}</h3>
        </div>
        <button
          class="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          @click="closeDayItems"
        >
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>

      <div class="max-h-[70vh] overflow-y-auto px-6 py-5">
        <div class="grid gap-3">
          <button
            v-for="item in dayItems"
            :key="`${item.id}-${item.platform_code}`"
            type="button"
            class="rounded-xl border border-slate-200 bg-white px-4 py-3 text-left transition hover:border-primary/40 hover:bg-slate-50"
            @click="openDetailFromItem(item)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full bg-slate-900 px-2 py-0.5 text-[11px] font-semibold text-white">
                    {{ item.platform_name }}
                  </span>
                  <span class="text-xs text-slate-500">
                    {{ item.scheduled_at ? formatDateTimeLabel(item.scheduled_at) : '未排期' }}
                  </span>
                </div>
                <p class="mt-2 truncate text-sm font-semibold text-slate-900">{{ item.title }}</p>
                <p class="mt-1 truncate text-xs text-slate-500">{{ item.account_name }}</p>
              </div>
              <span class="material-symbols-outlined text-[18px] text-slate-300">chevron_right</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import {
  distributionApi,
  type PublishPlanCalendarItem,
  type PublishPlanOverviewResponse,
  type PublishPlanPendingItem,
} from '../api/distribution'
import LegacyPageHost from '../components/LegacyPageHost.vue'
import { legacyPagesByKey } from '../lib/legacy-pages'

type DetailItem = (PublishPlanCalendarItem | PublishPlanPendingItem) & {
  status_message?: string | null
}

type CalendarRenderMode = 'month' | 'week'

const page = legacyPagesByKey.schedule
const hostRef = ref<HTMLElement | null>(null)
const isReady = ref(false)
const currentView = ref<CalendarRenderMode>('month')
const focusDate = ref(startOfDay(new Date()))

const detailVisible = ref(false)
const selectedDetail = ref<DetailItem | null>(null)
const dayItemsVisible = ref(false)
const dayItemsTitle = ref('')
const dayItems = ref<PublishPlanCalendarItem[]>([])

const MAX_VISIBLE_CALENDAR_ITEMS = 3

let lastRequestId = 0
let removePrevListener: (() => void) | null = null
let removeNextListener: (() => void) | null = null
let removeWeekButtonListener: (() => void) | null = null
let removeMonthButtonListener: (() => void) | null = null
let removeHostClickListener: (() => void) | null = null

function handleReady() {
  isReady.value = true
  bindStaticEvents()
  void loadOverview()
}

function bindStaticEvents() {
  removePrevListener?.()
  removeNextListener?.()
  removeWeekButtonListener?.()
  removeMonthButtonListener?.()
  removeHostClickListener?.()

  const prevButton = queryHost<HTMLElement>('#schedulePrevMonthButton')
  const nextButton = queryHost<HTMLElement>('#scheduleNextMonthButton')
  const toggleButtons = queryHostAll<HTMLElement>('button')
  const weekButton = toggleButtons.find((button) => button.textContent?.includes('周视图'))
  const monthButton = toggleButtons.find((button) => button.textContent?.includes('月视图'))

  if (prevButton) {
    const onClick = () => {
      focusDate.value = currentView.value === 'week'
        ? addDays(focusDate.value, -7)
        : new Date(focusDate.value.getFullYear(), focusDate.value.getMonth() - 1, 1)
      void loadOverview()
    }
    prevButton.addEventListener('click', onClick)
    removePrevListener = () => prevButton.removeEventListener('click', onClick)
  }

  if (nextButton) {
    const onClick = () => {
      focusDate.value = currentView.value === 'week'
        ? addDays(focusDate.value, 7)
        : new Date(focusDate.value.getFullYear(), focusDate.value.getMonth() + 1, 1)
      void loadOverview()
    }
    nextButton.addEventListener('click', onClick)
    removeNextListener = () => nextButton.removeEventListener('click', onClick)
  }

  if (weekButton) {
    const onClick = () => {
      currentView.value = 'week'
      updateViewToggle()
      void loadOverview()
    }
    weekButton.addEventListener('click', onClick)
    removeWeekButtonListener = () => weekButton.removeEventListener('click', onClick)
  }

  if (monthButton) {
    const onClick = () => {
      currentView.value = 'month'
      updateViewToggle()
      void loadOverview()
    }
    monthButton.addEventListener('click', onClick)
    removeMonthButtonListener = () => monthButton.removeEventListener('click', onClick)
  }

  const hostElement = hostRef.value
  if (hostElement) {
    const onClick = (event: Event) => {
      const target = event.target as HTMLElement | null
      if (!target) {
        return
      }

      const detailButton = target.closest<HTMLElement>('[data-action="open-detail"]')
      if (detailButton) {
        const raw = detailButton.dataset.item
        if (raw) {
          openDetailFromJson(raw)
        }
        return
      }

      const calendarCard = target.closest<HTMLElement>('[data-action="open-calendar-detail"]')
      if (calendarCard) {
        const raw = calendarCard.dataset.item
        if (raw) {
          openDetailFromJson(raw)
        }
        return
      }

      const dayItemsButton = target.closest<HTMLElement>('[data-action="open-day-items"]')
      if (dayItemsButton) {
        const raw = dayItemsButton.dataset.items
        const date = dayItemsButton.dataset.date
        if (raw && date) {
          openDayItemsFromJson(raw, date)
        }
      }
    }
    hostElement.addEventListener('click', onClick)
    removeHostClickListener = () => hostElement.removeEventListener('click', onClick)
  }

  updateViewToggle()
}

async function loadOverview() {
  if (!isReady.value) {
    return
  }

  const requestId = ++lastRequestId
  renderLoadingState()

  try {
    const overview = await fetchOverviewForCurrentView()
    if (requestId !== lastRequestId) {
      return
    }
    renderOverview(overview)
  } catch (error) {
    if (requestId !== lastRequestId) {
      return
    }
    renderErrorState(error)
  }
}

async function fetchOverviewForCurrentView(): Promise<PublishPlanOverviewResponse> {
  const primaryMonth = formatMonthValue(focusDate.value)
  const primaryOverview = await distributionApi.getPublishPlanOverview(primaryMonth)

  if (currentView.value === 'month') {
    return primaryOverview
  }

  const weekDates = getWeekDates(focusDate.value)
  const extraMonths = [...new Set(weekDates.map((date) => formatMonthValue(date)).filter((month) => month !== primaryMonth))]
  if (!extraMonths.length) {
    return primaryOverview
  }

  const extraOverviews = await Promise.all(extraMonths.map((month) => distributionApi.getPublishPlanOverview(month)))
  const mergedCalendarItems = [...primaryOverview.calendar_items]
  extraOverviews.forEach((overview) => {
    overview.calendar_items.forEach((item) => {
      if (!mergedCalendarItems.some((existing) => existing.id === item.id)) {
        mergedCalendarItems.push(item)
      }
    })
  })

  return {
    ...primaryOverview,
    calendar_items: mergedCalendarItems,
  }
}

function renderOverview(overview: PublishPlanOverviewResponse) {
  updateSummary(overview.summary.pending_count)
  updateTitle()
  updateViewToggle()
  renderCalendar(overview.calendar_items)
  renderPendingList(overview.pending_items)
}

function renderLoadingState() {
  updateSummary(null, '加载中...')
  updateTitle()
  updateViewToggle()
}

function renderErrorState(error: unknown) {
  updateSummary(null, '加载失败')
  updateTitle()

  const pendingCountBadge = queryHost<HTMLElement>('#schedulePendingCountBadge')
  if (pendingCountBadge) {
    pendingCountBadge.textContent = '0 items'
  }

  const pendingList = queryHost<HTMLElement>('#schedulePendingList')
  if (pendingList) {
    pendingList.innerHTML = `
      <div class="bg-white p-4 rounded-xl border border-red-100 text-sm text-red-600 shadow-sm">
        发布计划加载失败，请稍后重试。
      </div>
    `
  }

  const calendarGrid = queryHost<HTMLElement>('#scheduleCalendarGrid')
  if (calendarGrid) {
    calendarGrid.innerHTML = `
      <div class="col-span-7 bg-white min-h-[160px] p-6 flex items-center justify-center text-sm text-red-600">
        日历数据加载失败
      </div>
    `
  }

  console.error('Failed to load publish plan overview', error)
}

function updateSummary(count: number | null, text?: string) {
  const summaryBadge = queryHost<HTMLElement>('#scheduleSummaryBadge')
  const summaryText = summaryBadge?.querySelectorAll('span')?.[1] as HTMLElement | undefined
  if (summaryText) {
    summaryText.textContent = text ?? `待发布任务 ${count ?? 0}`
  }
}

function updateTitle() {
  const title =
    queryHost<HTMLElement>('#scheduleMonthTitle') ??
    queryHost<HTMLElement>('h3.font-bold.text-lg.text-text-main')
  if (!title) {
    return
  }

  title.textContent = currentView.value === 'month'
    ? formatMonthLabel(formatMonthValue(focusDate.value))
    : formatWeekLabel(focusDate.value)
}

function updateViewToggle() {
  const buttons = queryHostAll<HTMLElement>('button')
  const weekButton = buttons.find((button) => button.textContent?.includes('周视图'))
  const monthButton = buttons.find((button) => button.textContent?.includes('月视图'))

  setToggleButtonState(weekButton, currentView.value === 'week')
  setToggleButtonState(monthButton, currentView.value === 'month')
}

function renderCalendar(items: PublishPlanCalendarItem[]) {
  const calendarGrid = queryHost<HTMLElement>('#scheduleCalendarGrid')
  if (!calendarGrid) {
    return
  }

  const itemsByDate = new Map<string, PublishPlanCalendarItem[]>()
  items.forEach((item) => {
    const existing = itemsByDate.get(item.date) ?? []
    existing.push(item)
    itemsByDate.set(item.date, existing)
  })

  calendarGrid.innerHTML =
    currentView.value === 'month'
      ? buildMonthCalendarMarkup(formatMonthValue(focusDate.value), itemsByDate)
      : buildWeekCalendarMarkup(focusDate.value, itemsByDate)
}

function renderPendingList(items: PublishPlanPendingItem[]) {
  const pendingCountBadge = queryHost<HTMLElement>('#schedulePendingCountBadge')
  if (pendingCountBadge) {
    pendingCountBadge.textContent = `${items.length} items`
  }

  const pendingList = queryHost<HTMLElement>('#schedulePendingList')
  if (!pendingList) {
    return
  }

  if (!items.length) {
    pendingList.innerHTML = `
      <div class="bg-white p-4 rounded-xl border border-border text-sm text-text-secondary shadow-sm">
        当前没有待发布内容。
      </div>
    `
    return
  }

  pendingList.innerHTML = items.map((item) => buildPendingCardMarkup(item)).join('')
}

function buildMonthCalendarMarkup(month: string, itemsByDate: Map<string, PublishPlanCalendarItem[]>) {
  const [yearText, monthText] = month.split('-')
  const year = Number(yearText)
  const monthIndex = Number(monthText) - 1
  const firstDay = new Date(year, monthIndex, 1)
  const firstWeekday = firstDay.getDay()
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate()
  const previousMonthDays = new Date(year, monthIndex, 0).getDate()
  const today = formatDateKey(new Date())

  const headerMarkup = buildWeekdayHeaders()
  const dayCells = Array.from({ length: 42 }, (_, index) => {
    let dayNumber = 0
    let cellDate = ''
    let isCurrentMonth = true

    if (index < firstWeekday) {
      dayNumber = previousMonthDays - firstWeekday + index + 1
      cellDate = formatDateKey(new Date(year, monthIndex - 1, dayNumber))
      isCurrentMonth = false
    } else if (index >= firstWeekday + daysInMonth) {
      dayNumber = index - firstWeekday - daysInMonth + 1
      cellDate = formatDateKey(new Date(year, monthIndex + 1, dayNumber))
      isCurrentMonth = false
    } else {
      dayNumber = index - firstWeekday + 1
      cellDate = formatDateKey(new Date(year, monthIndex, dayNumber))
    }

    const isToday = cellDate === today
    const dayItems = isCurrentMonth ? itemsByDate.get(cellDate) ?? [] : []
    return buildDayCellMarkup({
      cellDate,
      dayNumber,
      isCurrentMonth,
      isToday,
      items: dayItems,
      minHeightClass: 'min-h-[100px]',
      maxVisibleItems: MAX_VISIBLE_CALENDAR_ITEMS,
    })
  }).join('')

  return `${headerMarkup}${dayCells}`
}

function buildWeekCalendarMarkup(anchorDate: Date, itemsByDate: Map<string, PublishPlanCalendarItem[]>) {
  const today = formatDateKey(new Date())
  const weekDates = getWeekDates(anchorDate)
  const headerMarkup = buildWeekdayHeaders()
  const dayCells = weekDates.map((date) => {
    const cellDate = formatDateKey(date)
    return buildDayCellMarkup({
      cellDate,
      dayNumber: date.getDate(),
      isCurrentMonth: true,
      isToday: cellDate === today,
      items: itemsByDate.get(cellDate) ?? [],
      minHeightClass: 'min-h-[420px]',
      maxVisibleItems: null,
    })
  }).join('')
  return `${headerMarkup}${dayCells}`
}

function buildWeekdayHeaders() {
  const weekdayHeaders = ['日', '一', '二', '三', '四', '五', '六']
  return weekdayHeaders
    .map(
      (label) =>
        `<div class="bg-surface-secondary p-2 text-center text-xs font-bold text-text-secondary">${label}</div>`,
    )
    .join('')
}

function buildDayCellMarkup(options: {
  cellDate: string
  dayNumber: number
  isCurrentMonth: boolean
  isToday: boolean
  items: PublishPlanCalendarItem[]
  minHeightClass: string
  maxVisibleItems?: number | null
}) {
  const { cellDate, dayNumber, isCurrentMonth, isToday, items, minHeightClass, maxVisibleItems } = options
  const cellClasses = isCurrentMonth
    ? `bg-white ${minHeightClass} p-2 flex flex-col gap-1 group hover:bg-surface-secondary/30 transition-colors${isToday ? ' bg-primary/5' : ''}`
    : `bg-white ${minHeightClass} p-2 flex flex-col gap-1 opacity-40`
  const visibleItems = maxVisibleItems && maxVisibleItems > 0 ? items.slice(0, maxVisibleItems) : items
  const hiddenCount = maxVisibleItems && maxVisibleItems > 0 ? Math.max(items.length - maxVisibleItems, 0) : 0

  return `
    <div class="${cellClasses}" data-date="${cellDate}">
      ${buildCalendarDayNumber(dayNumber, isCurrentMonth, isToday)}
      ${visibleItems.map((item) => buildCalendarItemMarkup(item)).join('')}
      ${hiddenCount > 0 ? buildCalendarMoreButtonMarkup(cellDate, items, hiddenCount) : ''}
    </div>
  `
}

function buildCalendarDayNumber(dayNumber: number, isCurrentMonth: boolean, isToday: boolean) {
  if (isToday && isCurrentMonth) {
    return `<span class="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold shadow-md shadow-primary/20">${dayNumber}</span>`
  }
  return `<span class="${isCurrentMonth ? 'text-xs font-bold text-text-main' : 'text-xs font-medium text-text-tertiary'}">${dayNumber}</span>`
}

function buildCalendarItemMarkup(item: PublishPlanCalendarItem) {
  const tone = getPlatformTone(item.platform_code)
  return `
    <button
      type="button"
      data-action="open-calendar-detail"
      data-item="${escapeAttribute(JSON.stringify(item))}"
      class="${tone.cardClass} w-full p-1.5 rounded flex items-center gap-1.5 cursor-pointer hover:shadow-sm transition-shadow text-left"
    >
      <span class="w-1.5 h-1.5 rounded-full ${tone.dotClass}"></span>
      <span class="text-[10px] font-medium ${tone.textClass} truncate">${escapeHtml(item.platform_name)}: ${escapeHtml(item.title)}</span>
    </button>
  `
}

function buildCalendarMoreButtonMarkup(cellDate: string, items: PublishPlanCalendarItem[], hiddenCount: number) {
  return `
    <button
      type="button"
      data-action="open-day-items"
      data-date="${escapeAttribute(cellDate)}"
      data-items="${escapeAttribute(JSON.stringify(items))}"
      class="mt-0.5 flex w-full items-center justify-center rounded border border-dashed border-slate-300 px-2 py-1 text-[10px] font-medium text-slate-500 transition hover:border-primary/40 hover:text-primary"
    >
      +${hiddenCount} more
    </button>
  `
}

function buildPendingCardMarkup(item: PublishPlanPendingItem) {
  const tone = getPlatformTone(item.platform_code)
  const statusTone = getStatusTone(item.status)
  const scheduleText = item.scheduled_at ? formatDateTimeLabel(item.scheduled_at) : '未排期'
  const coverMarkup = item.cover_url
    ? `<img class="w-full h-full object-cover" src="${escapeAttribute(item.cover_url)}" alt="${escapeAttribute(item.title)}" />`
    : `<div class="w-full h-full ${tone.placeholderClass} flex items-center justify-center"><span class="material-symbols-outlined ${tone.placeholderIconClass} text-[24px]">${tone.placeholderIcon}</span></div>`

  return `
    <div class="bg-white p-3 rounded-xl border border-border hover:border-primary/50 cursor-default shadow-sm hover:shadow-md transition-all group relative">
      <div class="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          type="button"
          data-action="open-detail"
          data-item="${escapeAttribute(JSON.stringify(item))}"
          class="text-text-tertiary hover:text-primary"
          title="查看详情"
        >
          <span class="material-symbols-outlined text-[16px]">edit_square</span>
        </button>
      </div>
      <div class="flex items-start gap-3">
        <div class="w-16 h-16 rounded-lg bg-gray-100 flex-shrink-0 overflow-hidden border border-border">
          ${coverMarkup}
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="${tone.badgeClass} text-white text-[10px] px-1.5 py-0.5 rounded font-medium">${escapeHtml(item.platform_name)}</span>
            <span class="${statusTone.className} text-[10px] px-1.5 py-0.5 rounded border">${escapeHtml(statusTone.label)}</span>
          </div>
          <p class="text-xs font-bold text-text-main line-clamp-2 leading-tight mb-2">${escapeHtml(item.title)}</p>
          <div class="flex items-center gap-2">
            <span class="text-[10px] text-text-tertiary flex items-center gap-1">
              <span class="material-symbols-outlined text-[12px]">schedule</span>
              ${escapeHtml(scheduleText)}
            </span>
          </div>
        </div>
      </div>
    </div>
  `
}

function openDetailFromJson(raw: string) {
  try {
    selectedDetail.value = JSON.parse(raw) as DetailItem
    detailVisible.value = true
  } catch (error) {
    console.error('Failed to parse detail payload', error)
  }
}

function openDetailFromItem(item: PublishPlanCalendarItem) {
  dayItemsVisible.value = false
  selectedDetail.value = item
  detailVisible.value = true
}

function closeDetail() {
  detailVisible.value = false
  selectedDetail.value = null
}

function openDayItemsFromJson(raw: string, date: string) {
  try {
    dayItems.value = JSON.parse(raw) as PublishPlanCalendarItem[]
    dayItemsTitle.value = formatDateLabel(date)
    dayItemsVisible.value = true
  } catch (error) {
    console.error('Failed to parse day items payload', error)
  }
}

function closeDayItems() {
  dayItemsVisible.value = false
  dayItemsTitle.value = ''
  dayItems.value = []
}

function getPlatformTone(platformCode: string) {
  const normalized = platformCode.toLowerCase()
  if (normalized === 'xiaohongshu') {
    return {
      cardClass: 'bg-red-50 border border-red-100',
      dotClass: 'bg-red-500',
      textClass: 'text-red-700',
      badgeClass: 'bg-red-500',
      placeholderClass: 'bg-red-50',
      placeholderIconClass: 'text-red-300',
      placeholderIcon: 'image',
    }
  }
  if (normalized === 'kuaishou') {
    return {
      cardClass: 'bg-orange-50 border border-orange-100 border-l-2 border-l-orange-400',
      dotClass: 'bg-orange-500',
      textClass: 'text-orange-700',
      badgeClass: 'bg-orange-500',
      placeholderClass: 'bg-orange-50',
      placeholderIconClass: 'text-orange-300',
      placeholderIcon: 'live_tv',
    }
  }
  if (normalized === 'douyin') {
    return {
      cardClass: 'bg-black/5 border border-black/10',
      dotClass: 'bg-black',
      textClass: 'text-text-main',
      badgeClass: 'bg-black',
      placeholderClass: 'bg-gray-100',
      placeholderIconClass: 'text-gray-300',
      placeholderIcon: 'videocam',
    }
  }
  return {
    cardClass: 'bg-blue-50 border border-blue-100',
    dotClass: 'bg-blue-500',
    textClass: 'text-blue-700',
    badgeClass: 'bg-blue-500',
    placeholderClass: 'bg-blue-50',
    placeholderIconClass: 'text-blue-300',
    placeholderIcon: 'article',
  }
}

function getStatusTone(status: string) {
  if (status === 'failed') {
    return { label: '失败', className: 'text-red-600 bg-red-50 border-red-100' }
  }
  if (status === 'scheduled') {
    return { label: '已排期', className: 'text-blue-600 bg-blue-50 border-blue-100' }
  }
  return { label: '已提交', className: 'text-green-600 bg-green-50 border-green-100' }
}

function getStatusLabel(status: string) {
  return getStatusTone(status).label
}

function formatDetailTime(item: DetailItem) {
  return item.scheduled_at
    ? `定时 ${formatDateTimeLabel(item.scheduled_at)}`
    : item.submitted_at
      ? `提交 ${formatDateTimeLabel(item.submitted_at)}`
      : '未记录'
}

function formatMonthValue(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

function formatMonthLabel(month: string) {
  const [yearText, monthText] = month.split('-')
  return `${yearText}年${Number(monthText)}月`
}

function formatWeekLabel(anchorDate: Date) {
  const weekDates = getWeekDates(anchorDate)
  const start = weekDates[0]
  const end = weekDates[6]
  return `${formatMonthLabel(formatMonthValue(anchorDate))} · ${String(start.getMonth() + 1).padStart(2, '0')}-${String(start.getDate()).padStart(2, '0')} 至 ${String(end.getMonth() + 1).padStart(2, '0')}-${String(end.getDate()).padStart(2, '0')}`
}

function formatDateKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function formatDateTimeLabel(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function formatDateLabel(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function getWeekDates(anchorDate: Date) {
  const start = startOfWeek(anchorDate)
  return Array.from({ length: 7 }, (_, index) => addDays(start, index))
}

function startOfWeek(date: Date) {
  const normalized = startOfDay(date)
  return addDays(normalized, -normalized.getDay())
}

function startOfDay(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

function addDays(date: Date, days: number) {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return startOfDay(next)
}

function setToggleButtonState(button: HTMLElement | undefined, active: boolean) {
  if (!button) {
    return
  }
  button.className = active
    ? 'px-3 py-1 text-xs font-medium bg-primary/10 border border-primary/20 rounded-md text-primary'
    : 'px-3 py-1 text-xs font-medium bg-white border border-border rounded-md text-text-secondary hover:text-primary'
}

function queryHost<T extends Element>(selector: string) {
  return hostRef.value?.querySelector<T>(selector) ?? null
}

function queryHostAll<T extends Element>(selector: string) {
  return Array.from(hostRef.value?.querySelectorAll<T>(selector) ?? [])
}

function escapeHtml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function escapeAttribute(value: string) {
  return escapeHtml(value)
}

onBeforeUnmount(() => {
  removePrevListener?.()
  removeNextListener?.()
  removeWeekButtonListener?.()
  removeMonthButtonListener?.()
  removeHostClickListener?.()
})
</script>
