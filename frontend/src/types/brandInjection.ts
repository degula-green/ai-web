export interface BrandProfile {
  brandId: string
  brandName: string
  productName: string
  positioning: string
  targetAudience: string
  scenarios: string
  tone: string
  forbiddenPhrases: string[]
  coverUrl?: string
}

export interface BrandProductCard {
  brandId: string
  brandName: string
  productName: string
  coverUrl?: string | null
  sellingPointsCount: number
  visualAssetsCount: number
  updatedAt?: string | null
}

export type SellingPointType = 'required' | 'optional' | 'forbidden'
export type SellingPointSource = 'manual' | 'ai' | 'external'
export type SellingPointStatus = 'draft' | 'pending_confirm' | 'confirmed' | 'rejected'

export interface SellingPointItem {
  id: string
  title: string
  description: string
  type: SellingPointType
  weight: number
  source: SellingPointSource
  status: SellingPointStatus
  platforms: string[]
  scenarios: string[]
}

export type AssetType = 'ui' | 'promo' | 'logo' | 'product' | 'video'

export interface VisualAssetItem {
  id: string
  assetType: AssetType
  assetUrl: string
  thumbnail: string
  tags: string[]
  relatedSellingPointIds: string[]
  platforms: string[]
  scenarios: string[]
  usableForCover: boolean
  usableForVideo: boolean
}

export interface BrandContextPayload {
  brandProfile: BrandProfile
  requiredSellingPoints: SellingPointItem[]
  optionalSellingPoints: SellingPointItem[]
  forbiddenPhrases: string[]
  selectedAssets: VisualAssetItem[]
  toneRules: string
}
