import { request } from './http'
import type {
  ContentDetail,
  ExportResult,
  HotRankItem,
  KeywordResultPage,
  KeywordTaskSummary,
  OverviewData,
  PagedList,
  PlatformSummary,
  SearchResultItem,
} from '../types/dataCollection'

const BASE = '/api/v1/data-collection'
const TASKS_BASE = '/api/v1/tasks'

interface KeywordTaskPayload {
  platformCode: string
  keyword: string
  contentKind?: 'image' | 'video'
  maxNotesCount?: number
}

interface DetailUrlTaskPayload {
  platformCode: string
  url: string
}

interface KeywordResultsQuery {
  pageNo?: number
  pageSize?: number
  keyword?: string
  sortBy?: 'heat' | 'time' | 'engagement'
}

interface UserMaterialsQuery {
  contentKind?: 'image' | 'video'
  keyword?: string
  pageNo?: number
  pageSize?: number
  sortBy?: 'selectedAt' | 'publishAt'
}

interface CollectPayload {
  taskId: string
  platform: string
  selectedIds: string[]
}

interface ExportPayload {
  exportScope: 'hot_rank' | 'material_library'
  contentKind?: 'image' | 'video'
  fileType: 'csv' | 'json'
  sourceRefNo?: string
  boardType?: string
  snapshotNo?: string
}

export async function getOverview(): Promise<OverviewData> {
  return request<OverviewData>(`${BASE}/overview`)
}

export async function getPlatformSummaryList(): Promise<PlatformSummary[]> {
  return request<PlatformSummary[]>(`${BASE}/platforms`)
}

export async function getPlatformDetail(platformCode: string): Promise<PlatformSummary & { supportsContentKinds?: string[] }> {
  return request<PlatformSummary & { supportsContentKinds?: string[] }>(`${BASE}/platforms/${platformCode}`)
}

export async function getPlatformHotRanks(
  platformCode: string,
  params: { snapshotNo?: string; boardType?: string; sortBy?: string; pageNo?: number; pageSize?: number; force?: boolean } = {},
): Promise<PagedList<HotRankItem> & { snapshotNo?: string | null; refreshing?: boolean }> {
  const query = new URLSearchParams()
  if (params.snapshotNo) query.set('snapshotNo', params.snapshotNo)
  if (params.boardType) query.set('boardType', params.boardType)
  if (params.sortBy) query.set('sortBy', params.sortBy)
  if (params.force) query.set('force', 'true')
  query.set('pageNo', String(params.pageNo ?? 1))
  query.set('pageSize', String(params.pageSize ?? 20))
  const data = await request<{
    pageNo: number
    pageSize: number
    total: number
    list: Array<Record<string, unknown>>
    snapshotNo?: string | null
    refreshing?: boolean
  }>(`${BASE}/platforms/${platformCode}/hot-ranks?${query.toString()}`)
  return {
    ...data,
    list: data.list.map((item) => mapHotRankItem(item)),
  }
}

export async function createKeywordTask(payload: KeywordTaskPayload): Promise<KeywordTaskSummary> {
  const normalizedContentKind = normalizePlatformContentKind(payload.platformCode, payload.contentKind)
  const res = await request<{ task_id: string; state: string }>(`${TASKS_BASE}`, {
    method: 'POST',
    body: {
      task_type: 'mediacrawler_collect',
      platform: payload.platformCode,
      source_type: 'keyword',
      source_value: payload.keyword,
      start_async: true,
      config: {
        collector: 'mediacrawler',
        crawler_type: 'search',
        crawler_max_notes_count: payload.maxNotesCount ?? 20,
        contentKind: normalizedContentKind,
        douyin_search_content_type: normalizedContentKind,
      },
    },
  })
  return {
    taskNo: res.task_id,
    taskStatus: res.state,
    platformCode: payload.platformCode,
    keyword: payload.keyword,
    contentKind: normalizedContentKind,
    resultCount: 0,
  }
}

export async function createDetailUrlTask(payload: DetailUrlTaskPayload): Promise<KeywordTaskSummary> {
  const crawlerUrl = normalizeDetailSourceValue(payload.platformCode, payload.url)
  const res = await request<{ task_id: string; state: string }>(`${TASKS_BASE}`, {
    method: 'POST',
    body: {
      task_type: 'mediacrawler_collect',
      platform: payload.platformCode,
      source_type: 'detail',
      source_value: payload.url,
      title: '链接采集',
      start_async: true,
      config: {
        collector: 'mediacrawler',
        crawler_type: 'detail',
        urls: crawlerUrl,
        source_url: payload.url,
        enable_comments: false,
        enable_sub_comments: false,
      },
    },
  })
  return {
    taskNo: res.task_id,
    taskStatus: res.state,
    platformCode: payload.platformCode,
    keyword: payload.url,
    contentKind: 'video',
    resultCount: 0,
  }
}

function normalizeDetailSourceValue(platformCode: string, url: string): string {
  if (String(platformCode || '').toLowerCase() !== 'douyin') return url
  return extractDouyinContentId(url) || url
}

function extractDouyinContentId(url: string): string {
  const text = String(url || '').trim()
  if (!text) return ''
  const directMatch = text.match(/\/(?:video|note)\/(\d{10,30})/)
  if (directMatch?.[1]) return directMatch[1]
  const queryMatch = text.match(/[?&](?:modal_id|aweme_id|group_id)=(\d{10,30})/)
  if (queryMatch?.[1]) return queryMatch[1]
  const looseMatch = text.match(/(?<!\d)(7\d{15,25})(?!\d)/)
  return looseMatch?.[1] ?? ''
}

function normalizePlatformContentKind(platformCode: string, contentKind?: 'image' | 'video'): 'image' | 'video' {
  const platform = String(platformCode || '').toLowerCase()
  if (platform === 'bilibili' || platform === 'kuaishou') {
    return 'video'
  }
  return contentKind ?? 'video'
}

export async function collectDetailUrlResult(payload: {
  taskId: string
  platform: string
  url: string
}): Promise<{ collectedCount: number; contentId: string; chainId?: string | null; contentKind?: 'image' | 'video'; duplicated?: boolean }> {
  return request(`${BASE}/collect-detail-url`, {
    method: 'POST',
    body: payload,
  })
}

export async function getKeywordTask(taskId: string): Promise<KeywordTaskSummary> {
  return request<KeywordTaskSummary>(`${TASKS_BASE}/${taskId}`)
}

export async function deleteKeywordTask(taskNo: string): Promise<void> {
  return request<void>(`${TASKS_BASE}/${taskNo}`, {
    method: 'DELETE',
  })
}

export async function getKeywordTaskResults(taskNo: string, _params: KeywordResultsQuery = {}): Promise<KeywordResultPage> {
  const data = await request<Array<Record<string, unknown>>>(`${BASE}/staged-results/${taskNo}`)
  return {
    pageNo: 1,
    pageSize: data.length,
    total: data.length,
    taskNo,
    taskStatus: 'finished',
    list: data.map((item) => ({
      ...mapSearchResultItem(item),
      importStatus: 'not_imported',
      sourceScene: 'keyword_search',
      sourceRefNo: taskNo,
    })),
  }
}

export async function searchPlatformContents(
  platformCode: string,
  payload: {
    keyword: string
    pageSize?: number
  },
): Promise<{ task: KeywordTaskSummary; results: SearchResultItem[] }> {
  const task = await createKeywordTask({
    platformCode,
    keyword: payload.keyword,
    maxNotesCount: payload.pageSize ?? 20,
  })
  const resultPage = await getKeywordTaskResults(task.taskNo, {
    pageNo: 1,
    pageSize: payload.pageSize ?? 20,
  })
  const mapped = resultPage.list.map((item) => ({ ...item, sourceRefNo: task.taskNo }))
  return { task, results: mapped }
}

export async function getContentDetail(
  contentId: string,
  params: {
    platformCode?: string
    contentKind?: string
    sourceScene?: string
    sourceRefNo?: string
    boardType?: string
    snapshotNo?: string
  } = {},
): Promise<ContentDetail | null> {
  const query = new URLSearchParams()
  query.set('platformCode', params.platformCode ?? 'douyin')
  if (params.contentKind) query.set('contentKind', params.contentKind)
  if (params.sourceScene) query.set('sourceScene', params.sourceScene)
  if (params.sourceRefNo) query.set('sourceRefNo', params.sourceRefNo)
  if (params.boardType) query.set('boardType', params.boardType)
  if (params.snapshotNo) query.set('snapshotNo', params.snapshotNo)
  return request<ContentDetail | null>(`${BASE}/contents/${encodeURIComponent(contentId)}?${query.toString()}`)
}

export async function collectStagedResults(payload: CollectPayload): Promise<{ collectedCount: number }> {
  return request<{ collectedCount: number }>(`${BASE}/collect`, {
    method: 'POST',
    body: payload,
  })
}

export async function getMyMaterials(params: UserMaterialsQuery = {}): Promise<PagedList<SearchResultItem>> {
  const query = new URLSearchParams()
  if (params.contentKind) query.set('contentKind', params.contentKind)
  if (params.keyword) query.set('keyword', params.keyword)
  query.set('pageNo', String(params.pageNo ?? 1))
  query.set('pageSize', String(params.pageSize ?? 20))
  query.set('sortBy', params.sortBy ?? 'selectedAt')
  const data = await request<{
    pageNo: number
    pageSize: number
    total: number
    list: Array<Record<string, unknown>>
  }>(`${BASE}/users/me/materials?${query.toString()}`)
  return {
    ...data,
    list: data.list.map((item) => mapSearchResultItem(item)),
  }
}

export async function getMyContent(platform: string, kind?: 'image' | 'video'): Promise<PagedList<SearchResultItem>> {
  const query = new URLSearchParams()
  query.set('platform', platform)
  if (kind) query.set('contentKind', kind)
  const data = await request<Array<Record<string, unknown>>>(`${BASE}/my-content?${query.toString()}`)
  return {
    pageNo: 1,
    pageSize: data.length,
    total: data.length,
    list: data.map((item) => ({
      ...mapSearchResultItem(item),
      importStatus: 'imported',
    })),
  }
}

export async function deleteMaterialRelation(chainId: string): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`${BASE}/users/me/material-relations/${chainId}`, {
    method: 'DELETE',
  })
}

export async function exportPlatformData(platformCode: string, payload: ExportPayload): Promise<ExportResult> {
  return request<ExportResult>(`${BASE}/platforms/${platformCode}/export`, {
    method: 'POST',
    body: payload,
  })
}

function mapHotRankItem(item: Record<string, unknown>): HotRankItem {
  const contentId = String(item.contentId ?? '')
  const coverImages = splitMediaUrls(item.images ?? item.coverUrl ?? item.cover_url ?? item.cover)
  return {
    id: contentId,
    contentId,
    rank: Number(item.rank ?? 0),
    title: String(item.title ?? ''),
    summary: String(item.summary ?? ''),
    cover: coverImages[0] ?? '',
    coverUrl: coverImages[0] ?? '',
    author: String(item.authorName ?? ''),
    authorName: String(item.authorName ?? ''),
    publishTime: String(item.publishTime ?? ''),
    hotValue: Number(item.hotValue ?? 0),
    likes: Number(item.likes ?? 0),
    comments: Number(item.comments ?? 0),
    shares: Number(item.shares ?? 0),
    views: Number(item.views ?? 0),
    tags: Array.isArray(item.tags) ? item.tags.map((it) => String(it)) : [],
    sourceUrl: String(item.sourceUrl ?? ''),
    sourceType: String(item.sourceType ?? 'hot_rank'),
    platformCode: String(item.platformCode ?? 'douyin'),
    contentKind: (item.contentKind as 'image' | 'video') ?? 'video',
    snapshotNo: item.snapshotNo ? String(item.snapshotNo) : undefined,
    importStatus: (item.importStatus as 'not_imported' | 'imported' | 'importing') ?? 'not_imported',
    materialId: item.materialId ? String(item.materialId) : null,
    chainId: item.chainId ? String(item.chainId) : null,
    sourceScene: 'hot_rank',
    sourceRefNo: item.snapshotNo ? String(item.snapshotNo) : undefined,
    images: coverImages.length > 0 ? coverImages : undefined,
    rawJson: item,
  }
}

function mapSearchResultItem(item: Record<string, unknown>): SearchResultItem {
  const platformCode = String(item.platformCode ?? item.platform ?? 'douyin')
  const normalizedPlatformCode = normalizePlatformCode(platformCode)
  const contentId = String(item.contentId ?? item.id ?? item.aweme_id ?? item.note_id ?? item.video_id ?? '')
  const publishTime = formatCrawlerTimestamp(item.publishTime ?? item.publishAt ?? item.publish_time ?? item.create_time ?? item.time)
  const coverImages = splitMediaUrls(
    item.images ??
    item.image_list ??
    item.coverUrl ??
    item.cover_url ??
    item.video_cover_url ??
    item.cover
  )

  return {
    id: contentId,
    contentId,
    keyword: item.keyword || item.source_keyword ? String(item.keyword ?? item.source_keyword) : undefined,
    title: String(item.title ?? item.desc ?? ''),
    summary: String(item.summary ?? item.desc ?? ''),
    cover: coverImages[0] ?? '',
    author: String(item.authorName ?? item.author ?? item.nickname ?? ''),
    authorName: String(item.authorName ?? item.author ?? item.nickname ?? ''),
    publishTime,
    likes: Number(item.likes ?? item.likeCount ?? item.liked_count ?? 0),
    comments: Number(item.comments ?? item.commentCount ?? item.comment_count ?? item.video_comment ?? 0),
    shares: Number(item.shares ?? item.shareCount ?? item.share_count ?? 0),
    collects: Number(item.collects ?? item.collectCount ?? item.collected_count ?? 0),
    engagement: Number(item.engagement ?? 0),
    tags: Array.isArray(item.tags) ? item.tags.map((it) => String(it)) : [],
    sourceUrl: String(item.sourceUrl ?? item.contentUrl ?? item.content_url ?? item.aweme_url ?? item.note_url ?? item.video_url ?? ''),
    sourceType: String(item.sourceType ?? item.sourceScene ?? 'keyword_search'),
    platformCode: normalizedPlatformCode,
    contentKind: inferContentKind(normalizedPlatformCode, item),
    importStatus: (item.importStatus as 'not_imported' | 'imported' | 'importing') ?? 'not_imported',
    materialId: item.materialId ? String(item.materialId) : null,
    chainId: item.chainId ?? item.relation_id ? String(item.chainId ?? item.relation_id) : null,
    sourceScene: (item.sourceScene as 'keyword_search' | 'hot_rank') ?? 'keyword_search',
    sourceRefNo: item.sourceRefNo ? String(item.sourceRefNo) : undefined,
    downloadUrl: item.downloadUrl || item.video_download_url || item.video_play_url ? String(item.downloadUrl ?? item.video_download_url ?? item.video_play_url) : undefined,
    images: coverImages.length > 0 ? coverImages : undefined,
    rawJson: item,
  }
}

function splitMediaUrls(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean)
  }
  const raw = String(value ?? '').trim()
  if (!raw) return []
  return raw.split(/[,，\n]/).map((item) => item.trim()).filter(Boolean)
}

function formatCrawlerTimestamp(value: unknown): string {
  if (value === undefined || value === null || value === '') return ''
  const raw = Number(value)
  if (Number.isFinite(raw) && raw > 0) {
    const millis = raw > 9_999_999_999 ? raw : raw * 1000
    return new Date(millis).toLocaleString()
  }
  return String(value)
}

function normalizePlatformCode(platformCode: string): string {
  const code = String(platformCode || '').toLowerCase()
  const mapping: Record<string, string> = {
    dy: 'douyin',
    xhs: 'xiaohongshu',
    ks: 'kuaishou',
    bili: 'bilibili',
  }
  return mapping[code] ?? code
}

function inferContentKind(platformCode: string, item: Record<string, unknown>): 'image' | 'video' {
  if (platformCode === 'bilibili' || platformCode === 'kuaishou') return 'video'
  if (platformCode === 'xiaohongshu') {
    return String(item.type ?? '').toLowerCase() === 'video' ? 'video' : 'image'
  }
  return item.aweme_id && String(item.aweme_type ?? '') !== '68' ? 'video' : ((item.contentKind as 'image' | 'video') ?? (item.aweme_id ? 'video' : 'image'))
}
