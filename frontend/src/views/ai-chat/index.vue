<template>
  <div class="relative h-full w-full bg-surface">
    <iframe
      class="h-full w-full border-0"
      :src="activeUrl"
      title="Content Remix Agent"
      allow="clipboard-read; clipboard-write"
      @load="handleLoad"
    />

    <div
      v-if="showHelp"
      class="absolute inset-0 z-10 flex items-center justify-center bg-black/65 p-6"
    >
      <div class="w-full max-w-xl rounded-xl bg-white p-5 text-slate-800 shadow-xl">
        <h3 class="text-base font-semibold">二创页面未正常显示</h3>
        <p class="mt-2 text-sm text-slate-600">
          当前尝试地址：<code>{{ activeUrl }}</code>
        </p>
        <p class="mt-1 text-sm text-slate-600">
          请确认 `ai-agent-service/frontend` 正在运行。
        </p>
        <div class="mt-4 flex flex-wrap gap-2">
          <button class="btn" @click="switchUrl('http://localhost:5374')">切到 5374</button>
          <button class="btn" @click="switchUrl('http://localhost:5373')">切到 5373</button>
          <button class="btn" @click="openNewTab">新窗口打开</button>
          <button class="btn primary" @click="reloadCurrent">重试当前地址</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

const envUrl = (import.meta.env.VITE_REMIX_CHAT_URL as string | undefined)?.trim()
const activeUrl = ref(envUrl || 'http://localhost:5374')
const showHelp = ref(false)
let loadTimer: ReturnType<typeof setTimeout> | null = null

function startTimer() {
  if (loadTimer) clearTimeout(loadTimer)
  showHelp.value = false
  loadTimer = setTimeout(() => {
    showHelp.value = true
  }, 3000)
}

function handleLoad() {
  if (loadTimer) clearTimeout(loadTimer)
  showHelp.value = false
}

function switchUrl(url: string) {
  activeUrl.value = url
  startTimer()
}

function reloadCurrent() {
  activeUrl.value = `${activeUrl.value.split('?')[0]}?t=${Date.now()}`
  startTimer()
}

function openNewTab() {
  window.open(activeUrl.value, '_blank', 'noopener,noreferrer')
}

onMounted(() => {
  startTimer()
})
</script>

<style scoped>
.btn {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 13px;
}

.btn.primary {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}
</style>
