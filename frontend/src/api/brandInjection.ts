import { request } from './http'
import type { BrandProductCard, BrandProfile, BrandContextPayload, SellingPointItem, VisualAssetItem } from '../types/brandInjection'

const BASE = '/api/v1/brand-knowledge'

interface ProductListResponse {
  pageNo: number
  pageSize: number
  total: number
  list: BrandProductCard[]
}

interface SellingPointsSavePayload {
  upserts: Array<{
    id?: string
    title: string
    description: string
    type: string
    weight: number
    source: string
    status: string
    platforms: string[]
    scenarios: string[]
  }>
  deleteIds: string[]
}

function isNumericId(value: string | null | undefined): value is string {
  if (!value) return false
  return /^\d+$/.test(value)
}

function normalizeAssetType(type: string): VisualAssetItem['assetType'] {
  if (type === 'logo' || type === 'ui' || type === 'promo' || type === 'product' || type === 'video') {
    return type
  }
  return 'promo'
}

export async function listBrandProducts(params: { keyword?: string; pageNo?: number; pageSize?: number } = {}): Promise<ProductListResponse> {
  const query = new URLSearchParams()
  if (params.keyword?.trim()) query.set('keyword', params.keyword.trim())
  query.set('pageNo', String(params.pageNo ?? 1))
  query.set('pageSize', String(params.pageSize ?? 50))
  return request<ProductListResponse>(`${BASE}/products?${query.toString()}`)
}

export async function createBrandProfile(profile: BrandProfile): Promise<string> {
  const data = await request<{ brandId: string }>(`${BASE}/products`, {
    method: 'POST',
    body: {
      brandName: profile.brandName,
      productName: profile.productName,
      positioning: profile.positioning,
      targetAudience: profile.targetAudience,
      scenarios: profile.scenarios,
      tone: profile.tone,
      forbiddenPhrases: profile.forbiddenPhrases,
      coverUrl: profile.coverUrl?.trim() || null,
    },
  })
  return data.brandId
}

export async function getBrandProfile(brandId: string): Promise<BrandProfile> {
  const data = await request<{
    brandId: string
    brandName: string
    productName: string
    positioning: string
    targetAudience: string
    scenarios: string
    tone: string
    forbiddenPhrases: string[]
    coverUrl?: string | null
  }>(`${BASE}/products/${brandId}`)

  return {
    brandId: data.brandId,
    brandName: data.brandName ?? '',
    productName: data.productName ?? '',
    positioning: data.positioning ?? '',
    targetAudience: data.targetAudience ?? '',
    scenarios: data.scenarios ?? '',
    tone: data.tone ?? '',
    forbiddenPhrases: Array.isArray(data.forbiddenPhrases) ? data.forbiddenPhrases.map((x) => String(x)) : [],
    coverUrl: data.coverUrl ?? '',
  }
}

export async function saveBrandProfile(profile: BrandProfile): Promise<string> {
  if (isNumericId(profile.brandId)) {
    await request<{ brandId: string }>(`${BASE}/products/${profile.brandId}`, {
      method: 'PUT',
      body: {
        brandName: profile.brandName,
        productName: profile.productName,
        positioning: profile.positioning,
        targetAudience: profile.targetAudience,
        scenarios: profile.scenarios,
        tone: profile.tone,
        forbiddenPhrases: profile.forbiddenPhrases,
        coverUrl: profile.coverUrl?.trim() || null,
      },
    })
    return profile.brandId
  }
  return createBrandProfile(profile)
}

export async function deleteBrandProfile(brandId: string): Promise<void> {
  await request<{ brandId: string }>(`${BASE}/products/${brandId}`, { method: 'DELETE' })
}

export async function getSellingPoints(brandId: string): Promise<SellingPointItem[]> {
  const data = await request<{
    pageNo: number
    pageSize: number
    total: number
    list: Array<{
      id: string
      title: string
      description: string
      type: SellingPointItem['type']
      weight: number
      source: SellingPointItem['source']
      status: SellingPointItem['status']
      platforms: string[]
      scenarios: string[]
    }>
  }>(`${BASE}/products/${brandId}/selling-points?pageNo=1&pageSize=100`)

  return data.list.map((item) => ({
    id: String(item.id),
    title: item.title ?? '',
    description: item.description ?? '',
    type: item.type ?? 'optional',
    weight: Number(item.weight ?? 5),
    source: item.source ?? 'manual',
    status: item.status ?? 'draft',
    platforms: Array.isArray(item.platforms) ? item.platforms.map((x) => String(x)) : [],
    scenarios: Array.isArray(item.scenarios) ? item.scenarios.map((x) => String(x)) : [],
  }))
}

export async function saveSellingPoints(
  brandId: string,
  points: SellingPointItem[],
  originalPointIds: string[],
): Promise<void> {
  const currentPersistedIds = points.map((point) => point.id).filter((id) => isNumericId(id))
  const deleteIds = originalPointIds.filter((id) => isNumericId(id) && !currentPersistedIds.includes(id))

  const payload: SellingPointsSavePayload = {
    upserts: points.map((point) => ({
      id: isNumericId(point.id) ? point.id : undefined,
      title: point.title,
      description: point.description,
      type: point.type,
      weight: point.weight,
      source: point.source,
      status: point.status,
      platforms: point.platforms,
      scenarios: point.scenarios,
    })),
    deleteIds,
  }

  await request<{ upserted: number; deleted: number }>(`${BASE}/products/${brandId}/selling-points`, {
    method: 'PUT',
    body: payload,
  })
}

export async function extractAISellingPoints(_brandId: string, _context: unknown): Promise<SellingPointItem[]> {
  throw new Error('AI selling point extraction is not available in this version')
}

export async function syncFeishuApproval(_sellingPointIds: string[]): Promise<void> {
  throw new Error('Feishu approval sync is not available in this version')
}

export async function getVisualAssets(brandId: string): Promise<VisualAssetItem[]> {
  const data = await request<{
    pageNo: number
    pageSize: number
    total: number
    list: Array<{
      id: string
      assetType: string
      assetUrl: string
      thumbnail: string
      tags: string[]
      relatedSellingPointIds: string[]
      platforms: string[]
      scenarios: string[]
      usableForCover: boolean
      usableForVideo: boolean
    }>
  }>(`${BASE}/products/${brandId}/visual-assets?pageNo=1&pageSize=100`)

  return data.list.map((item) => ({
    id: String(item.id),
    assetType: normalizeAssetType(item.assetType),
    assetUrl: item.assetUrl ?? '',
    thumbnail: item.thumbnail ?? item.assetUrl ?? '',
    tags: Array.isArray(item.tags) ? item.tags.map((x) => String(x)) : [],
    relatedSellingPointIds: Array.isArray(item.relatedSellingPointIds) ? item.relatedSellingPointIds.map((x) => String(x)) : [],
    platforms: Array.isArray(item.platforms) ? item.platforms.map((x) => String(x)) : [],
    scenarios: Array.isArray(item.scenarios) ? item.scenarios.map((x) => String(x)) : [],
    usableForCover: Boolean(item.usableForCover),
    usableForVideo: Boolean(item.usableForVideo),
  }))
}

export async function uploadVisualAsset(file: File, meta: Partial<VisualAssetItem>, brandId: string): Promise<VisualAssetItem> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('assetType', meta.assetType ?? 'promo')
  formData.append('tags', JSON.stringify(meta.tags ?? []))
  formData.append('platforms', JSON.stringify(meta.platforms ?? []))
  formData.append('scenarios', JSON.stringify(meta.scenarios ?? []))
  formData.append('relatedSellingPointIds', JSON.stringify(meta.relatedSellingPointIds ?? []))
  formData.append('usableForCover', String(meta.usableForCover ?? false))
  formData.append('usableForVideo', String(meta.usableForVideo ?? false))

  const data = await request<{
    id: string
    assetType: string
    assetUrl: string
    thumbnail: string
  }>(`${BASE}/products/${brandId}/visual-assets/upload`, {
    method: 'POST',
    body: formData,
  })

  return {
    id: String(data.id),
    assetType: normalizeAssetType(data.assetType),
    assetUrl: data.assetUrl,
    thumbnail: data.thumbnail || data.assetUrl,
    tags: meta.tags ?? [],
    relatedSellingPointIds: meta.relatedSellingPointIds ?? [],
    platforms: meta.platforms ?? [],
    scenarios: meta.scenarios ?? [],
    usableForCover: meta.usableForCover ?? false,
    usableForVideo: meta.usableForVideo ?? false,
  }
}

export async function deleteVisualAsset(assetId: string): Promise<void> {
  await request<{ assetId: string }>(`${BASE}/visual-assets/${assetId}`, { method: 'DELETE' })
}

export async function injectBrandContext(payload: BrandContextPayload): Promise<{ success: boolean; taskId: string }> {
  await request<BrandContextPayload>(`${BASE}/context/payload`, {
    method: 'POST',
    body: {
      brandId: payload.brandProfile.brandId,
      sellingPointIds: [
        ...payload.requiredSellingPoints.map((item) => item.id),
        ...payload.optionalSellingPoints.map((item) => item.id),
      ],
      assetIds: payload.selectedAssets.map((item) => item.id),
      toneRules: payload.toneRules,
    },
  })
  return { success: true, taskId: `ctx_${Date.now()}` }
}


