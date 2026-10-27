<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full">
    <div class="px-5 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between shrink-0">
      <div>
        <h2 class="font-bold text-slate-800 flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-[20px]">perm_media</span>
          视觉资产与物料库
        </h2>
        <p class="text-xs text-slate-500 mt-1">管理品牌授权使用的Logo、UI界面、宣传图等媒体语料。</p>
      </div>
      <button
        @click="triggerUpload"
        :disabled="uploading"
        class="w-8 h-8 rounded-lg border-2 border-dashed border-slate-300 text-slate-400 hover:border-primary hover:text-primary hover:bg-primary/5 flex items-center justify-center transition-colors"
        title="上传素材"
      >
        <span class="material-symbols-outlined text-[20px]">upload</span>
      </button>
      <input ref="fileInputRef" type="file" class="hidden" accept="image/*,video/*" @change="handleFileChange" />
    </div>

    <div class="p-5 overflow-y-auto flex-1 custom-scrollbar">
      <div v-if="assets.length === 0" class="h-full flex flex-col items-center justify-center text-slate-400">
        <span class="material-symbols-outlined text-4xl mb-2 opacity-50">imagesmode</span>
        <p class="text-sm">暂无素材</p>
      </div>

      <div v-else class="grid grid-cols-2 gap-3">
        <div
          v-for="asset in assets"
          :key="asset.id"
          class="group relative rounded-lg border border-slate-200 overflow-hidden bg-slate-100 hover:border-primary/50 hover:shadow-md transition-all cursor-pointer aspect-video"
          @click="emit('view', asset)"
        >
          <video
            v-if="isVideoAsset(asset)"
            :src="asset.assetUrl"
            class="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
            muted
            playsinline
            preload="metadata"
          />
          <img v-else :src="asset.thumbnail || asset.assetUrl" class="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity" />

          <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
            <div class="absolute top-2 left-2 flex gap-1">
              <span class="bg-primary/90 text-white text-[9px] font-bold px-1.5 py-0.5 rounded backdrop-blur-sm uppercase">
                {{ asset.assetType }}
              </span>
            </div>

            <div class="absolute bottom-2 left-2 right-2 flex items-end justify-between">
              <div class="flex flex-wrap gap-1 w-2/3">
                <span v-for="tag in asset.tags.slice(0, 2)" :key="tag" class="bg-black/50 text-slate-100 text-[9px] font-medium px-1.5 py-0.5 rounded border border-white/10 truncate max-w-[60px]">
                  #{{ tag }}
                </span>
                <span v-if="asset.tags.length > 2" class="bg-black/50 text-slate-100 text-[9px] font-medium px-1.5 py-0.5 rounded border border-white/10">
                  +{{ asset.tags.length - 2 }}
                </span>
              </div>
              <div class="flex gap-1 border border-white/20 bg-black/40 rounded overflow-hidden">
                <span class="material-symbols-outlined text-[14px] p-1" :class="asset.usableForCover ? 'text-green-400' : 'text-slate-500'" title="可作封面">vertical_shades</span>
                <span class="material-symbols-outlined text-[14px] p-1" :class="asset.usableForVideo ? 'text-blue-400' : 'text-slate-500'" title="可作视频语料">movie</span>
                <button
                  type="button"
                  class="material-symbols-outlined text-[14px] p-1 text-red-300 hover:text-red-200"
                  title="删除素材"
                  @click.stop="emit('remove', asset)"
                >
                  delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { VisualAssetItem } from '../../types/brandInjection'

const props = defineProps<{
  assets: VisualAssetItem[]
  uploading?: boolean
}>()

const emit = defineEmits<{
  (e: 'upload', file: File): void
  (e: 'view', asset: VisualAssetItem): void
  (e: 'remove', asset: VisualAssetItem): void
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)

function triggerUpload() {
  if (props.uploading) return
  fileInputRef.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  emit('upload', file)
  input.value = ''
}

function isVideoAsset(asset: VisualAssetItem): boolean {
  if (asset.assetType === 'video') return true
  const src = (asset.assetUrl || '').toLowerCase()
  return src.endsWith('.mp4') || src.endsWith('.mov') || src.endsWith('.webm') || src.endsWith('.m4v')
}
</script>
