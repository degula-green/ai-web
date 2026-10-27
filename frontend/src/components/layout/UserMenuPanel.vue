<template>
  <div class="relative w-full">
    <div
      ref="triggerRef"
      class="sidebar-user cursor-pointer hover:bg-surface-secondary transition-colors"
      @click="toggleMenu"
    >
      <div class="user-avatar overflow-hidden">
        <img v-if="avatarUrl" :src="avatarUrl" class="w-full h-full object-cover" alt="Avatar" />
        <span v-else>{{ initials }}</span>
      </div>
      <div class="user-info">
        <p>{{ displayName }}</p>
        <span>{{ roleLabel }}</span>
      </div>
      <button class="user-settings" title="账户菜单" @click.stop="toggleMenu">
        <span class="material-symbols-outlined">more_vert</span>
      </button>
    </div>

    <Transition name="slide-up-fade">
      <div
        v-if="isOpen"
        ref="popoverRef"
        class="absolute bottom-[calc(100%+8px)] left-2 w-[calc(100%-16px)] bg-white rounded-2xl border border-gray-100 shadow-[0_10px_30px_-5px_rgba(0,0,0,0.1)] z-[100] overflow-hidden flex flex-col"
      >
        <div class="px-4 py-3 border-b border-gray-50 flex items-center gap-3 bg-gray-50/50">
          <div class="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-bold text-sm shadow-inner shrink-0 overflow-hidden">
            <img v-if="avatarUrl" :src="avatarUrl" class="w-full h-full object-cover" alt="Avatar" />
            <span v-else>{{ initials }}</span>
          </div>
          <div class="min-w-0">
            <div class="font-bold text-gray-900 text-sm truncate">{{ displayName }}</div>
            <div class="text-xs text-gray-500 truncate mt-0.5">{{ accountLabel }}</div>
          </div>
        </div>

        <div class="p-1.5 flex flex-col gap-0.5">
          <button @click="openSettingsModal('profile')" class="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-100 text-gray-700 text-sm font-medium transition-colors text-left">
            <span class="material-symbols-outlined text-[18px] text-gray-400">person</span>
            个人资料
          </button>
          <button @click="openSettingsModal('general')" class="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-100 text-gray-700 text-sm font-medium transition-colors text-left">
            <span class="material-symbols-outlined text-[18px] text-gray-400">settings</span>
            系统设置
          </button>
          <button @click="showPlaceholder('帮助中心')" class="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-100 text-gray-700 text-sm font-medium transition-colors text-left">
            <span class="material-symbols-outlined text-[18px] text-gray-400">help</span>
            帮助中心
          </button>
        </div>

        <div class="p-1.5 border-t border-gray-50">
          <button @click="handleLogout" class="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-red-50 text-red-600 text-sm font-medium transition-colors text-left group">
            <span class="material-symbols-outlined text-[18px] text-red-400 group-hover:text-red-600 transition-colors">logout</span>
            退出登录
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { authStore, getAuthErrorMessage } from '../../auth/store'
import { computed, onMounted, onUnmounted, ref, inject } from 'vue'
import { useRouter } from 'vue-router'

const isOpen = ref(false)
const triggerRef = ref<HTMLElement | null>(null)
const popoverRef = ref<HTMLElement | null>(null)
const router = useRouter()
const openSettings = inject('openSettings') as (tab: string) => void

const displayName = computed(() => authStore.displayName.value)
const initials = computed(() => authStore.initials.value)
const avatarUrl = computed(() => authStore.state.user?.avatarUrl)
const roleLabel = computed(() => authStore.state.roles[0]?.roleName || authStore.state.user?.userType || '已登录')
const accountLabel = computed(() => {
  const user = authStore.state.user
  return user?.email || user?.phone || (user?.username ? `@${user.username}` : '未设置账号')
})

const toggleMenu = () => {
  isOpen.value = !isOpen.value
}

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as Node
  if (triggerRef.value && triggerRef.value.contains(target)) return
  if (popoverRef.value && popoverRef.value.contains(target)) return
  isOpen.value = false
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})

const openSettingsModal = (tab: string) => {
  isOpen.value = false
  if (openSettings) {
    openSettings(tab)
  }
}

const showPlaceholder = (label: string) => {
  isOpen.value = false
  window.alert(`${label}暂未开放`)
}

const handleLogout = async () => {
  if (!window.confirm('确定要退出登录吗？')) {
    return
  }

  try {
    await authStore.logout()
    router.replace('/register')
  } catch (error) {
    window.alert(getAuthErrorMessage(error))
  } finally {
    isOpen.value = false
  }
}
</script>

<style scoped>
.sidebar-user {
  padding: 14px 16px;
  border-top: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #2563EB;
  color: white;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-info p {
  font-size: 13px;
  font-weight: 600;
  color: #1E293B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0;
}

.user-info span {
  font-size: 11px;
  color: #64748B;
}

.user-settings {
  background: none;
  border: none;
  cursor: pointer;
  color: #94A3B8;
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 6px;
  transition: color 0.15s, background 0.15s;
}

.user-settings:hover {
  color: #2563EB;
  background: #F1F5F9;
}

.user-settings .material-symbols-outlined {
  font-size: 18px;
}

.slide-up-fade-enter-active,
.slide-up-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-fade-enter-from,
.slide-up-fade-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.96);
}
</style>
