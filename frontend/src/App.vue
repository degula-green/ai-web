<template>
  <RouterView />

  <div v-if="hasTasks" class="fixed bottom-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
    <TransitionGroup name="task-list">
      <div
        v-for="task in visibleActiveTasks"
        :key="`active-${task.taskNo}`"
        class="w-80 rounded-xl border border-blue-100 bg-white p-4 shadow-2xl pointer-events-auto"
      >
        <div class="flex items-center gap-3">
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-50 text-blue-500">
            <span class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
          </div>
          <div class="min-w-0 flex-1">
            <h4 class="truncate text-xs font-bold text-slate-800">{{ taskTitle(task, 'running') }}</h4>
            <p class="truncate text-[10px] text-slate-500">{{ taskSubtitle(task) }}</p>
          </div>
          <div class="flex gap-1">
            <button
              type="button"
              :title="task.taskDomain === 'crawler' ? '取消任务' : '关闭追踪'"
              class="rounded p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-red-500"
              @click="taskStore.cancelTask(task.taskNo)"
            >
              <span class="material-symbols-outlined text-[14px]">close</span>
            </button>
          </div>
        </div>
      </div>

      <div
        v-for="task in visibleRecentTasks"
        :key="`recent-${task.taskNo}`"
        class="w-80 rounded-xl border bg-white p-4 shadow-2xl pointer-events-auto"
        :class="task.status === 'failed' ? 'border-red-100' : 'border-green-100'"
      >
        <div class="flex items-center gap-3">
          <div
            class="flex h-8 w-8 items-center justify-center rounded-full"
            :class="task.status === 'failed' ? 'bg-red-50 text-red-500' : 'bg-green-50 text-green-500'"
          >
            <span class="material-symbols-outlined text-[18px]">
              {{ task.status === 'failed' ? 'error' : 'check_circle' }}
            </span>
          </div>
          <div class="min-w-0 flex-1">
            <h4 class="truncate text-xs font-bold text-slate-800">{{ taskTitle(task, 'completed') }}</h4>
            <p class="truncate text-[10px] text-slate-500">{{ taskDoneText(task) }}</p>
          </div>
          <div class="flex gap-1">
            <button
              v-if="canViewTask(task)"
              type="button"
              class="rounded bg-green-500 px-2 py-1 text-[10px] font-bold text-white transition-colors hover:bg-green-600"
              @click="viewTask(task)"
            >
              查看
            </button>
            <button
              type="button"
              class="rounded p-1 text-slate-400 hover:bg-slate-100"
              @click="taskStore.dismissTask(task.taskNo)"
            >
              <span class="material-symbols-outlined text-[14px]">close</span>
            </button>
          </div>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { authStore } from './auth/store'
import { taskStore, type AsyncTask } from './data-collection/taskStore'
import { collectDetailUrlResult, getKeywordTask, getKeywordTaskResults } from './api/dataCollection'

const router = useRouter()
const route = useRoute()

const copywritingApiBaseUrl = (
  import.meta.env.VITE_REMIX_AGENT_API_BASE_URL
  ?? import.meta.env.VITE_AGENT_API_BASE_URL
  ?? 'http://localhost:8002'
).replace(/\/$/, '')

const visibleActiveTasks = computed(() => taskStore.activeTasks.filter(shouldShowTask))
const visibleRecentTasks = computed(() => taskStore.recentTasks.filter(shouldShowTask))
const hasTasks = computed(() => visibleActiveTasks.value.length > 0 || visibleRecentTasks.value.length > 0)

let pollTimer: ReturnType<typeof setInterval> | null = null

function shouldShowTask(task: AsyncTask) {
  if (!task.hideWhileOnSource || !task.sourceRoutePath) return true
  return route.path !== task.sourceRoutePath
}

function buildHeaders() {
  const headers = new Headers({ 'Content-Type': 'application/json' })
  const token = authStore.state.session?.accessToken
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return headers
}

async function parseJsonSafely(response: Response) {
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    return null
  }
  return response.json()
}

async function pollCrawlerTask(task: AsyncTask) {
  const response = await getKeywordTask(task.taskNo) as any
  const data = response.data || response
  const isFinished = ['finished', 'parsing', 'manual_intervention', 'closed'].includes(data.state)
  const isFailed = data.state === 'failed'

  if (!isFinished && !isFailed) {
    return
  }

  if (isFinished) {
    let resultCount = data.result_count || 0
    let contentKind = task.contentKind
    if (task.taskKind === 'detail_url') {
      try {
        const bindResult = await collectDetailUrlResult({
          taskId: task.taskNo,
          platform: task.platformCode,
          url: task.sourceUrl || task.keyword,
        })
        resultCount = bindResult.collectedCount || 1
        contentKind = bindResult.contentKind || contentKind || 'video'
        router.push({
          path: '/data-collection/platform',
          query: {
            code: task.platformCode,
            contentKind,
          },
        })
      } catch (error: any) {
        taskStore.updateTaskStatus(task.taskNo, {
          status: 'failed',
          lastError: error?.message || '链接采集完成，但绑定素材库失败',
        })
        return
      }
    } else {
      try {
        const resultPage = await getKeywordTaskResults(task.taskNo)
        resultCount = resultPage.total
      } catch (error) {
        console.warn('Load task result count failed:', error)
      }
    }

    taskStore.updateTaskStatus(task.taskNo, {
      status: 'completed',
      resultCount,
      contentKind,
    })
    return
  }

  taskStore.updateTaskStatus(task.taskNo, {
    status: 'failed',
    lastError: data.error_message || '采集失败',
  })
}

async function pollAvatarVideoTask(task: AsyncTask) {
  const endpoint = task.humanType === 'video'
    ? `${copywritingApiBaseUrl}/api/v1/digital-human/videoretalk/tasks/${task.taskNo}`
    : `${copywritingApiBaseUrl}/api/v1/digital-human/s2v/tasks/${task.taskNo}`
  const response = await fetch(endpoint, {
    method: 'GET',
    headers: buildHeaders(),
  })
  const data = await parseJsonSafely(response) as { output?: any; detail?: string } | null
  if (!response.ok) {
    throw new Error(typeof data?.detail === 'string' ? data.detail : '数字人任务查询失败')
  }

  const output = data?.output || {}
  const taskStatus = String(output.task_status || '')
  const results = output.results
  const resultUrl = String(
    output.video_url
    || (Array.isArray(results) ? results[0]?.video_url || results[0]?.url : results?.video_url || results?.url)
    || '',
  )

  if (resultUrl) {
    taskStore.updateTaskStatus(task.taskNo, {
      status: 'completed',
      taskStatus,
      resultUrl,
    })
    return
  }

  if (['FAILED', 'CANCELED', 'CANCELLED'].includes(taskStatus.toUpperCase())) {
    taskStore.updateTaskStatus(task.taskNo, {
      status: 'failed',
      taskStatus,
      lastError: `数字人视频生成失败，当前状态：${taskStatus || 'FAILED'}`,
    })
    return
  }

  taskStore.updateTaskStatus(task.taskNo, {
    taskStatus,
  })
}

async function pollAvatarGalleryTask(task: AsyncTask) {
  const response = await fetch(`${copywritingApiBaseUrl}/api/v1/digital-human/runninghub/tasks/${task.taskNo}`, {
    method: 'POST',
    headers: buildHeaders(),
  })
  const data = await parseJsonSafely(response) as { output?: any; detail?: string } | null
  if (!response.ok) {
    throw new Error(typeof data?.detail === 'string' ? data.detail : '任务查询失败')
  }

  const output = data?.output || {}
  const taskStatus = String(output.task_status || '')
  const rawResults = output.results
  const resultUrls = (Array.isArray(rawResults) ? rawResults : rawResults ? [rawResults] : [])
    .map((item) => String(item?.url || item?.video_url || ''))
    .filter(Boolean)

  if (['SUCCESS', 'SUCCEEDED'].includes(taskStatus.toUpperCase())) {
    taskStore.updateTaskStatus(task.taskNo, {
      status: 'completed',
      taskStatus,
      resultUrls,
    })
    return
  }

  if (['FAILED', 'CANCELED', 'CANCELLED'].includes(taskStatus.toUpperCase())) {
    taskStore.updateTaskStatus(task.taskNo, {
      status: 'failed',
      taskStatus,
      lastError: `展示图任务失败: ${taskStatus || 'FAILED'}`,
    })
    return
  }

  taskStore.updateTaskStatus(task.taskNo, {
    taskStatus,
  })
}

async function pollActiveTasks() {
  if (taskStore.activeTasks.length === 0) return

  for (const task of [...taskStore.activeTasks]) {
    try {
      if (task.taskDomain === 'avatar_video') {
        await pollAvatarVideoTask(task)
        continue
      }
      if (task.taskDomain === 'avatar_gallery') {
        await pollAvatarGalleryTask(task)
        continue
      }
      await pollCrawlerTask(task)
    } catch (error) {
      console.warn('Poll task error:', error)
    }
  }
}

function canViewTask(task: AsyncTask) {
  if (task.taskDomain === 'crawler') return true
  return Boolean(task.sourceRoutePath && task.draftId)
}

function viewTask(task: AsyncTask) {
  if (task.taskDomain === 'avatar_video' || task.taskDomain === 'avatar_gallery') {
    if (task.sourceRoutePath && task.draftId) {
      router.push({
        path: task.sourceRoutePath,
        query: {
          draftId: task.draftId,
        },
      })
    }
    return
  }

  if (task.taskKind === 'detail_url') {
    router.push({
      path: '/data-collection/platform',
      query: {
        code: task.platformCode,
        contentKind: task.contentKind || 'video',
      },
    })
    taskStore.dismissTask(task.taskNo)
    return
  }

  router.push({
    path: '/data-collection/platform',
    query: {
      code: task.platformCode,
      restoreTaskNo: task.taskNo,
      restoreKeyword: task.keyword,
    },
  })
  taskStore.dismissTask(task.taskNo)
}

function taskTitle(task: AsyncTask, phase: 'running' | 'completed') {
  if (task.taskDomain === 'avatar_video') {
    return phase === 'running' ? '数字人视频生成中...' : task.status === 'failed' ? '数字人视频生成失败' : '数字人视频已生成'
  }
  if (task.taskDomain === 'avatar_gallery') {
    return phase === 'running' ? '模特展示图生成中...' : task.status === 'failed' ? '模特展示图生成失败' : '模特展示图已生成'
  }
  if (task.taskKind === 'detail_url') {
    return phase === 'running' ? '链接采集中...' : '链接采集已完成'
  }
  return phase === 'running' ? '关键词爬取中...' : '爬取任务已完成'
}

function taskSubtitle(task: AsyncTask) {
  if (task.taskDomain === 'avatar_video' || task.taskDomain === 'avatar_gallery') {
    const scene = task.purposeScene || task.title || '数字人'
    const draft = task.draftId ? `草稿 ${task.draftId}` : ''
    return [scene, draft].filter(Boolean).join(' · ')
  }
  if (task.taskKind === 'detail_url') {
    return `链接: ${task.sourceUrl || task.keyword}`
  }
  return `关键词: ${task.keyword}`
}

function taskDoneText(task: AsyncTask) {
  if (task.taskDomain === 'avatar_video') {
    return task.status === 'failed'
      ? (task.lastError || '数字人视频生成失败')
      : `任务状态: ${task.taskStatus || 'SUCCEEDED'}`
  }
  if (task.taskDomain === 'avatar_gallery') {
    return task.status === 'failed'
      ? (task.lastError || '模特展示图生成失败')
      : `已生成 ${task.resultUrls?.length || 0} 张图片`
  }
  if (task.taskKind === 'detail_url') {
    return task.status === 'failed' ? (task.lastError || '绑定素材库失败') : '已绑定到素材库'
  }
  return `关键词: ${task.keyword} (${task.resultCount || 0} 条结果)`
}

onMounted(() => {
  taskStore.hydrate()
  pollTimer = setInterval(() => {
    void pollActiveTasks()
  }, 3000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
  }
})
</script>

<style>
.task-list-enter-active,
.task-list-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.task-list-enter-from,
.task-list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
