export type AvatarPurposeScene =
  | '口播数字人'
  | '卖货数字人'
  | '产品介绍数字人'
  | '模特数字人'
  | '视频剪辑数字人'

export type AvatarStepKey =
  | 'extract'
  | 'rewrite'
  | 'voice'
  | 'model_prompt'
  | 'avatar'
  | 'preview'
  | 'clip'

export interface AvatarSceneFlowConfig {
  purposeScene: AvatarPurposeScene
  pageTitle: string
  pageSubtitle: string
  requiresAudio: boolean
  steps: AvatarStepKey[]
  stepTitles?: Partial<Record<AvatarStepKey, string>>
}

const defaultStepTitles: Record<AvatarStepKey, string> = {
  extract: '提取文案',
  rewrite: '改写文案',
  voice: '声音生成',
  model_prompt: '模特提示词',
  avatar: '形象选择',
  preview: '视频预览',
  clip: '视频剪辑',
}

export const avatarSceneFlowConfigs: Record<AvatarPurposeScene, AvatarSceneFlowConfig> = {
  '口播数字人': {
    purposeScene: '口播数字人',
    pageTitle: '口播数字人',
    pageSubtitle: '聚焦单人口播内容生产，复用通用草稿、音频、素材上传与数字人生成能力。',
    requiresAudio: true,
    steps: ['extract', 'rewrite', 'voice', 'avatar', 'preview', 'clip'],
  },
  '卖货数字人': {
    purposeScene: '卖货数字人',
    pageTitle: '卖货数字人',
    pageSubtitle: '保留口播前置链路，并在成片前增加商品融合步骤，先生成融合图，再驱动数字人视频。',
    requiresAudio: true,
    steps: ['extract', 'rewrite', 'voice', 'avatar', 'model_prompt', 'preview', 'clip'],
    stepTitles: {
      model_prompt: '产品融合',
      preview: '视频生成',
    },
  },
  '产品介绍数字人': {
    purposeScene: '产品介绍数字人',
    pageTitle: '产品介绍数字人',
    pageSubtitle: '面向产品讲解和品牌说明场景，复用统一草稿、声音、数字人和预览能力。',
    requiresAudio: false,
    steps: ['avatar', 'model_prompt', 'preview', 'clip'],
    stepTitles: {
      avatar: '形象选择',
      model_prompt: '图像生成',
      preview: '视频生成',
      clip: '视频剪辑',
    },
  },
  '模特数字人': {
    purposeScene: '模特数字人',
    pageTitle: '模特数字人',
    pageSubtitle: '面向模特展示与服饰陈列场景，采用图文驱动流程并切换到独立 RunningHub AI App。',
    requiresAudio: false,
    steps: ['extract', 'rewrite', 'model_prompt', 'avatar', 'preview', 'clip'],
    stepTitles: {
      rewrite: '场景文案',
      avatar: '参考图选择',
      preview: '生成预览',
    },
  },
  '视频剪辑数字人': {
    purposeScene: '视频剪辑数字人',
    pageTitle: '视频剪辑数字人',
    pageSubtitle: '先验证产品素材、文案、配音时间点到 FFmpeg 成片的 MVP 闭环，不做重编辑器。',
    requiresAudio: true,
    steps: ['avatar', 'rewrite', 'voice', 'preview', 'clip'],
    stepTitles: {
      avatar: '素材选择',
      rewrite: '短视频文案',
      voice: '配音时间轴',
      preview: '剪辑预览',
      clip: '成片输出',
    },
  },
}

export function getAvatarSceneFlowConfig(scene: AvatarPurposeScene): AvatarSceneFlowConfig {
  const config = avatarSceneFlowConfigs[scene]
  return {
    ...config,
    stepTitles: {
      ...defaultStepTitles,
      ...(config.stepTitles || {}),
    },
  }
}
