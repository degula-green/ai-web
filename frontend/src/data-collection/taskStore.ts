import { reactive, watch } from 'vue'
import { deleteKeywordTask } from '../api/dataCollection'

export type TaskDomain = 'crawler' | 'avatar_video' | 'avatar_gallery'
export type TaskKind = 'keyword' | 'detail_url' | 'avatar_video' | 'avatar_gallery'

export interface AsyncTask {
  taskNo: string
  keyword: string
  platformCode: string
  taskKind?: TaskKind
  taskDomain?: TaskDomain
  sourceUrl?: string
  contentKind?: 'image' | 'video'
  status: 'running' | 'completed' | 'failed'
  startTime: number
  endTime?: number
  resultCount?: number
  lastError?: string
  sourceRoutePath?: string
  hideWhileOnSource?: boolean
  draftId?: string
  purposeScene?: string
  humanType?: 'image' | 'video'
  title?: string
  taskStatus?: string
  resultUrl?: string
  resultUrls?: string[]
}

const STORAGE_KEY = 'ai_content_automation_tasks'

function normalizeTask(task: AsyncTask): AsyncTask {
  return {
    ...task,
    taskKind: task.taskKind ?? 'keyword',
    taskDomain: task.taskDomain ?? 'crawler',
    title: task.title ?? '',
    taskStatus: task.taskStatus ?? '',
    resultUrl: task.resultUrl ?? '',
    resultUrls: Array.isArray(task.resultUrls) ? task.resultUrls : [],
  }
}

export const taskStore = reactive({
  activeTasks: [] as AsyncTask[],
  recentTasks: [] as AsyncTask[],

  hydrate() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (!saved) return
      const data = JSON.parse(saved) as { activeTasks?: AsyncTask[]; recentTasks?: AsyncTask[] }
      this.activeTasks = Array.isArray(data.activeTasks) ? data.activeTasks.map(normalizeTask) : []
      this.recentTasks = Array.isArray(data.recentTasks) ? data.recentTasks.map(normalizeTask) : []
    } catch (error) {
      console.error('Failed to hydrate taskStore', error)
    }
  },

  addTask(task: Omit<AsyncTask, 'startTime' | 'status'>) {
    const newTask = normalizeTask({
      ...task,
      status: 'running',
      startTime: Date.now(),
    })

    if (newTask.taskDomain !== 'crawler' && newTask.draftId) {
      this.activeTasks = this.activeTasks.filter((item) => !(
        item.taskNo !== newTask.taskNo
        && item.taskDomain === newTask.taskDomain
        && item.draftId === newTask.draftId
      ))
      this.recentTasks = this.recentTasks.filter((item) => !(
        item.taskNo !== newTask.taskNo
        && item.taskDomain === newTask.taskDomain
        && item.draftId === newTask.draftId
      ))
    }

    const existingIdx = this.activeTasks.findIndex((item) => item.taskNo === task.taskNo)

    if (existingIdx !== -1) {
      this.activeTasks[existingIdx] = {
        ...this.activeTasks[existingIdx],
        ...newTask,
        startTime: this.activeTasks[existingIdx].startTime,
      }
    } else {
      this.activeTasks.push(newTask)
    }
    this.persist()
  },

  updateTaskStatus(taskNo: string, updates: Partial<AsyncTask>) {
    const activeIdx = this.activeTasks.findIndex((task) => task.taskNo === taskNo)
    if (activeIdx !== -1) {
      const updated = normalizeTask({ ...this.activeTasks[activeIdx], ...updates })
      if (updated.status === 'completed' || updated.status === 'failed') {
        updated.endTime = Date.now()
        this.activeTasks.splice(activeIdx, 1)
        const recentIdx = this.recentTasks.findIndex((task) => task.taskNo === taskNo)
        if (recentIdx !== -1) {
          this.recentTasks.splice(recentIdx, 1)
        }
        this.recentTasks.unshift(updated)
        this.recentTasks = this.recentTasks.slice(0, 10)
      } else {
        this.activeTasks[activeIdx] = updated
      }
      this.persist()
      return
    }

    const recentIdx = this.recentTasks.findIndex((task) => task.taskNo === taskNo)
    if (recentIdx !== -1) {
      this.recentTasks[recentIdx] = normalizeTask({ ...this.recentTasks[recentIdx], ...updates })
      this.persist()
    }
  },

  async cancelTask(taskNo: string) {
    const activeTask = this.activeTasks.find((task) => task.taskNo === taskNo)
    if (activeTask?.taskDomain === 'crawler') {
      try {
        await deleteKeywordTask(taskNo)
      } catch (error) {
        console.warn('Backend cancellation failed, but removing from UI anyway', error)
      }
    }

    const activeIdx = this.activeTasks.findIndex((task) => task.taskNo === taskNo)
    if (activeIdx !== -1) {
      const task = this.activeTasks.splice(activeIdx, 1)[0]
      task.status = 'failed'
      task.endTime = Date.now()
      task.lastError = activeTask?.taskDomain === 'crawler' ? 'User cancelled' : 'Task tracking dismissed'
      this.recentTasks.unshift(normalizeTask(task))
      this.recentTasks = this.recentTasks.slice(0, 10)
      this.persist()
    }
  },

  dismissTask(taskNo: string) {
    const recentIdx = this.recentTasks.findIndex((task) => task.taskNo === taskNo)
    if (recentIdx !== -1) {
      this.recentTasks.splice(recentIdx, 1)
      this.persist()
      return
    }

    const activeIdx = this.activeTasks.findIndex((task) => task.taskNo === taskNo)
    if (activeIdx !== -1) {
      this.activeTasks.splice(activeIdx, 1)
      this.persist()
    }
  },

  findTask(taskNo: string) {
    return this.activeTasks.find((task) => task.taskNo === taskNo)
      ?? this.recentTasks.find((task) => task.taskNo === taskNo)
      ?? null
  },

  persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      activeTasks: this.activeTasks,
      recentTasks: this.recentTasks,
    }))
  },
})

watch(() => taskStore.activeTasks, () => taskStore.persist(), { deep: true })
watch(() => taskStore.recentTasks, () => taskStore.persist(), { deep: true })
