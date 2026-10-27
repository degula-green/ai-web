import type { BrandProfile, SellingPointItem, VisualAssetItem } from '../types/brandInjection'

export const mockBrandProfile: BrandProfile = {
  brandId: 'b_1001',
  brandName: '星火智能',
  productName: '星火内容自动化矩阵系统',
  positioning: '企业级全渠道内容一站式 AI 生产与分发平台',
  targetAudience: 'MCN机构、企业市场部、电商运营团队、自媒体矩阵操盘手',
  scenarios: '多图文批量生成、爆款短视频混剪、跨平台一键矩阵分发、全网热点实时追踪',
  tone: '专业、科技感、高效、值得信赖',
  forbiddenPhrases: ['便宜', '免费试用', '完全替代人工', '秒杀一切竞品', '国家级']
}

export const mockSellingPoints: SellingPointItem[] = [
  {
    id: 'sp_1',
    title: '全渠道一站式矩阵管理',
    description: '支持抖音、小红书、视频号等 10+ 主流平台，实现一个系统管控百个账号。',
    type: 'required',
    weight: 10,
    source: 'manual',
    status: 'confirmed',
    platforms: ['douyin', 'xiaohongshu', 'weibo'],
    scenarios: ['软件测评', '效率提升演示']
  },
  {
    id: 'sp_2',
    title: '独创上下文记忆生成的 AI 大脑',
    description: '深入理解品牌调性和禁用词，创作内容高度符合企业标准，大幅降低人工审核成本。',
    type: 'optional',
    weight: 8,
    source: 'ai',
    status: 'pending_confirm',
    platforms: ['xiaohongshu', 'zhihu'],
    scenarios: ['技术解析', '产品种草']
  },
  {
    id: 'sp_3',
    title: '不能说“完全替代人工”',
    description: '强调这是人效翻倍工具，而不是取代人的系统。避免引起受众抵触。',
    type: 'forbidden',
    weight: 10,
    source: 'manual',
    status: 'confirmed',
    platforms: [],
    scenarios: []
  },
  {
    id: 'sp_4',
    title: '热点秒配，分钟级成片',
    description: '关联全网实时热榜，AI自动化拆解热点结构并结合品牌特性，3分钟直出混剪短视频。',
    type: 'optional',
    weight: 6,
    source: 'ai',
    status: 'rejected',
    platforms: ['douyin'],
    scenarios: ['娱乐搞笑', '带货']
  }
]

export const mockVisualAssets: VisualAssetItem[] = [
  {
    id: 'va_1',
    assetType: 'logo',
    assetUrl: 'https://picsum.photos/seed/logo/200/200',
    thumbnail: 'https://picsum.photos/seed/logo/200/200',
    tags: ['官方Logo', '白底'],
    relatedSellingPointIds: [],
    platforms: [],
    scenarios: ['通用'],
    usableForCover: true,
    usableForVideo: true
  },
  {
    id: 'va_2',
    assetType: 'ui',
    assetUrl: 'https://picsum.photos/seed/ui1/800/600',
    thumbnail: 'https://picsum.photos/seed/ui1/200/150',
    tags: ['Dashboard', '暗黑模式', '数据大屏'],
    relatedSellingPointIds: ['sp_1'],
    platforms: ['xiaohongshu'],
    scenarios: ['功能展示'],
    usableForCover: true,
    usableForVideo: false
  },
  {
    id: 'va_3',
    assetType: 'promo',
    assetUrl: 'https://picsum.photos/seed/promo/800/600',
    thumbnail: 'https://picsum.photos/seed/promo/200/150',
    tags: ['年终大促', '海报'],
    relatedSellingPointIds: ['sp_2', 'sp_4'],
    platforms: ['weibo', 'douyin'],
    scenarios: ['节日营销'],
    usableForCover: true,
    usableForVideo: true
  }
]
