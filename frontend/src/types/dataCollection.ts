export interface PlatformSummary {
  platformCode: string
  platformName: string
  icon: string
  latestUpdateTime: string
  hotRankCount: number
  keywordTaskCount: number
  status: 'normal' | 'collecting' | 'error'
  themeColor?: string
  lastSyncAt?: string | null
}

export interface OverviewStats {
  platformCount: number
  todayFetched: number
  hotRankUpdates: number
  keywordTaskCount: number
  keywordTaskActive: number
}

export interface OverviewData {
  stats: OverviewStats
  platforms: PlatformSummary[]
}

export interface HotRankItem {
  id: string
  contentId: string
  rank: number
  title: string
  summary: string
  cover?: string
  coverUrl?: string
  author: string
  authorName?: string
  publishTime: string
  hotValue?: number
  likes?: number
  comments?: number
  shares?: number
  views?: number
  tags: string[]
  sourceUrl: string
  sourceType: string
  platformCode: string
  contentKind: 'image' | 'video'
  snapshotNo?: string
  importStatus?: 'not_imported' | 'imported' | 'importing'
  materialId?: string | null
  chainId?: string | null
  sourceScene?: 'hot_rank' | 'keyword_search'
  sourceRefNo?: string
  downloadUrl?: string
  images?: string[]
  mediaJson?: any
  extraJson?: any
  rawJson?: any
}

export interface SearchResultItem {
  id: string
  contentId: string
  keyword?: string
  title: string
  summary: string
  cover: string
  author: string
  authorName?: string
  publishTime: string
  likes: number
  comments: number
  shares: number
  collects: number
  engagement?: number
  tags: string[]
  sourceUrl: string
  sourceType: string
  platformCode: string
  contentKind: 'image' | 'video'
  hotValue?: number
  importStatus?: 'not_imported' | 'imported' | 'importing'
  materialId?: string | null
  chainId?: string | null
  sourceScene?: 'hot_rank' | 'keyword_search'
  sourceRefNo?: string
  downloadUrl?: string
  images?: string[]
  mediaJson?: any
  extraJson?: any
  rawJson?: any
}

export interface SearchParams {
  keyword: string
  timeRange?: string
  sortBy?: 'heat' | 'time' | 'engagement'
  page?: number
  pageSize?: number
}

export interface PagedList<T> {
  pageNo: number
  pageSize: number
  total: number
  list: T[]
}

export interface KeywordTaskSummary {
  taskNo: string
  taskStatus: string
  platformCode: string
  keyword: string
  contentKind: string
  expireAt?: string | null
  resultCount: number
}

export interface KeywordResultPage extends PagedList<SearchResultItem> {
  taskNo: string
  taskStatus: string
  cacheExpireAt?: string | null
}

export interface MaterialImportResult {
  platformCode: string
  contentKind: string
  sourceScene: string
  sourceRefNo: string
  requestedCount: number
  insertedMaterialCount: number
  linkedCount: number
  duplicateMaterialCount: number
  duplicateLinkCount: number
  deletedRedisCount: number
  materialIds: string[]
  chainIds: string[]
}

export interface ContentDetail {
  contentId: string
  platformCode: string
  contentKind: string
  sourceScene?: string | null
  materialId?: string | null
  chainId?: string | null
  importStatus?: string | null
  title: string
  summary: string
  authorName?: string | null
  authorId?: string | null
  authorSecUid?: string | null
  authorAvatarUrl?: string | null
  publishAt?: string | null
  contentUrl?: string | null
  coverUrl?: string | null
  likeCount?: number
  commentCount?: number
  collectCount?: number
  shareCount?: number
  playCount?: number
  tagList?: string[]
  mediaCount?: number
  mediaJson?: any
  extraJson?: any
  rawJson?: any
  images?: string[]
  downloadUrl?: string
  videoDownloadUrl?: string
  videoUrl?: string
}

export interface ExportResult {
  exportNo: string
  fileType: string
  fileName: string
  filePath: string
  downloadUrl: string
  expireAt?: string | null
}
