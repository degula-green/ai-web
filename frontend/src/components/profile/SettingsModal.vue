<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="fixed inset-0 z-[1000] flex items-center justify-center p-4 sm:p-6" style="font-family: Inter, sans-serif;">
        <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" @click="close"></div>
        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-4xl flex overflow-hidden flex-col md:flex-row max-h-[85vh]">
          
          <!-- Sidebar Tabs -->
          <div class="w-full md:w-64 bg-gray-50/50 border-r border-gray-100 p-4 shrink-0 overflow-y-auto">
            <h2 class="text-[15px] font-bold text-gray-800 mb-4 px-3 py-2">设置</h2>
            <nav class="space-y-0.5">
              <button 
                v-for="tab in tabs" 
                :key="tab.id"
                @click="activeTab = tab.id"
                :class="[
                  'w-full flex items-center gap-3 px-3 py-2 rounded-xl text-[14px] transition-colors',
                  activeTab === tab.id ? 'bg-gray-200 text-gray-900 font-medium' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                ]"
              >
                <span class="material-symbols-outlined text-[18px]">{{ tab.icon }}</span>
                {{ tab.label }}
              </button>
            </nav>
          </div>

          <!-- Main Content -->
          <div class="flex-1 overflow-y-auto relative p-6 sm:p-10 bg-white min-h-[500px]">
             <!-- close btn -->
             <button @click="close" class="absolute top-6 right-6 p-1.5 rounded-full hover:bg-gray-100 text-gray-500 transition">
               <span class="material-symbols-outlined text-[20px]">close</span>
             </button>

             <!-- Profile Tab -->
             <div v-if="activeTab === 'profile'" class="max-w-[480px] space-y-8">
                <h3 class="text-xl font-bold text-gray-900 pb-4 border-b border-gray-100">个人资料</h3>
                
                <div class="flex items-center gap-6">
                  <div class="relative group cursor-pointer inline-block" @click="triggerAvatarUpload">
                    <img v-if="profileForm.avatarUrl || user?.avatarUrl" :src="profileForm.avatarUrl || user?.avatarUrl || undefined" alt="Avatar" class="w-20 h-20 rounded-full object-cover ring-1 ring-gray-200 shadow-sm" />
                    <div v-else class="w-20 h-20 rounded-full bg-[#f3f4f6] text-gray-500 flex items-center justify-center text-2xl font-semibold ring-1 ring-gray-200 shadow-sm">
                      {{ initials }}
                    </div>
                    <div class="absolute inset-0 bg-black/40 rounded-full opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center transition-opacity text-white text-xs font-medium">
                       <span class="material-symbols-outlined text-[20px] mb-0.5">photo_camera</span>
                       更改
                    </div>
                    <input type="file" ref="fileInput" class="hidden" accept="image/png, image/jpeg, image/gif, image/webp" @change="onFileChange" />
                  </div>
                  <div class="flex flex-col justify-center">
                    <span v-if="isUploading" class="text-[13px] text-gray-500 flex items-center gap-1.5"><span class="material-symbols-outlined animate-spin text-[16px]">sync</span> 上传中...</span>
                    <button v-else @click="triggerAvatarUpload" class="text-sm font-medium text-gray-700 px-4 py-2 border border-gray-200 rounded-full hover:bg-gray-50 transition shadow-sm">上传新头像</button>
                  </div>
                </div>

                <div class="space-y-4">
                   <div>
                     <label class="block text-[13px] font-medium text-gray-700 mb-1.5 focus-within:text-black">显示名称</label>
                     <input v-model="profileForm.nickname" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 text-[15px] text-gray-900 placeholder:text-gray-400 transition-all font-medium py-[10px]" placeholder="您的昵称" />
                   </div>
                   <div>
                     <label class="block text-[13px] font-medium text-gray-700 mb-1.5">用户名</label>
                     <input v-model="profileForm.username" type="text" class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 text-[15px] text-gray-900 placeholder:text-gray-400 transition-all font-medium py-[10px]" placeholder="登录用的唯一标识" />
                   </div>
                   <p class="text-[13px] text-gray-500 mt-2 leading-relaxed">个人资料有助于他人识别你的身份。你的姓名和用户名也将用于系统的互动环节。</p>
                </div>

                <div class="flex justify-end pt-4">
                  <button @click="saveProfile" :disabled="isSaving" class="bg-gray-900 hover:bg-black text-white px-6 py-[10px] rounded-full text-[14px] font-medium transition-colors shadow-sm disabled:opacity-50">
                    {{ isSaving ? '保存中...' : '保存' }}
                  </button>
                </div>
             </div>

             <!-- Security Tab -->
             <div v-if="activeTab === 'security'" class="max-w-[480px] space-y-8">
                <h3 class="text-xl font-bold text-gray-900 pb-4 border-b border-gray-100">保护你的账户</h3>
                
                <div class="space-y-3 pt-2">
                  <div class="flex items-center justify-between py-3 border-b border-gray-50 group">
                    <div>
                      <div class="text-[14px] text-gray-900 font-medium">手机号码</div>
                      <div class="text-[13px] text-gray-500 mt-[2px]">{{ user?.phone || '未绑定' }}</div>
                    </div>
                    <button @click="promptUpdate('phone')" class="text-[14px] font-medium text-gray-500 hover:text-gray-900 transition-colors">更改</button>
                  </div>
                  
                  <div class="flex items-center justify-between py-3 border-b border-gray-50 group">
                    <div>
                      <div class="text-[14px] text-gray-900 font-medium">验证邮箱</div>
                      <div class="text-[13px] text-gray-500 mt-[2px]">{{ user?.email || '未绑定' }}</div>
                    </div>
                    <button @click="promptUpdate('email')" class="text-[14px] font-medium text-gray-500 hover:text-gray-900 transition-colors">更改</button>
                  </div>

                  <div class="flex items-center justify-between py-3 border-b border-gray-50 group">
                    <div>
                      <div class="text-[14px] text-gray-900 font-medium">多因素身份验证 (MFA)</div>
                      <div class="text-[13px] text-gray-500 mt-[2px]">添加 MFA 为登录过程提供额外保护。</div>
                    </div>
                    <button class="px-3 py-1.5 border border-gray-200 rounded-full text-[13px] font-medium text-gray-700 bg-white hover:bg-gray-50 transition shadow-sm" @click="alertNotImpl">设置 MFA</button>
                  </div>
                </div>
             </div>

             <!-- General Tab placeholder -->
             <div v-if="activeTab === 'general'" class="max-w-[480px] space-y-8">
                <h3 class="text-xl font-bold text-gray-900 pb-4 border-b border-gray-100">常规选项</h3>
                <div class="space-y-3 pt-2">
                   <div class="flex items-center justify-between py-3 border-b border-gray-50">
                      <div class="text-[14px] font-medium text-gray-900">系统外观</div>
                      <div class="text-[14px] text-gray-500 flex items-center gap-1 cursor-pointer">系统默认 <span class="material-symbols-outlined text-[16px]">expand_more</span></div>
                   </div>
                   <div class="flex items-center justify-between py-3 border-b border-gray-50">
                      <div class="text-[14px] font-medium text-gray-900">界面语言</div>
                      <div class="text-[14px] text-gray-500 flex items-center gap-1 cursor-pointer">自动检测 <span class="material-symbols-outlined text-[16px]">expand_more</span></div>
                   </div>
                   <div class="flex items-center justify-between py-3 border-b border-gray-50">
                      <div class="text-[14px] font-medium text-gray-900">时区</div>
                      <div class="text-[14px] text-gray-500 flex items-center gap-1 cursor-pointer">UTC+08 (CN) <span class="material-symbols-outlined text-[16px]">expand_more</span></div>
                   </div>
                </div>
             </div>

          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { authStore } from '../../auth/store'
import { uploadAvatar } from '../../api/auth'

const props = defineProps<{
  modelValue: boolean
  defaultTab?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const activeTab = ref(props.defaultTab || 'general')
const isSaving = ref(false)
const isUploading = ref(false)
const user = computed(() => authStore.state.user)
const initials = computed(() => authStore.initials.value)
const fileInput = ref<HTMLInputElement | null>(null)

const tabs = [
  { id: 'general', label: '常规', icon: 'settings' },
  { id: 'profile', label: '个人资料', icon: 'account_circle' },
  { id: 'security', label: '安全', icon: 'shield_lock' },
]

const profileForm = ref({
  nickname: '',
  username: '',
  avatarUrl: ''
})

watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    if (props.defaultTab) activeTab.value = props.defaultTab
    profileForm.value.nickname = user.value?.nickname || ''
    profileForm.value.username = user.value?.username || ''
    profileForm.value.avatarUrl = ''
  }
})

const close = () => {
  emit('update:modelValue', false)
}

const triggerAvatarUpload = () => {
  if (!isUploading.value) {
    fileInput.value?.click()
  }
}

const onFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  if (file.size > 5 * 1024 * 1024) {
    alert('头像不能超过 5MB')
    target.value = ''
    return
  }

  isUploading.value = true
  try {
    const res = await uploadAvatar(file)
    profileForm.value.avatarUrl = res.url
    // Optional: Auto-save avatar when uploaded, or wait for user to click "Save"
    // For best UX, wait for "Save" but preview it now using profileForm.avatarUrl.
  } catch (error: any) {
    alert(error.message || '上传失败')
  } finally {
    isUploading.value = false
    target.value = ''
  }
}

const saveProfile = async () => {
  if (isSaving.value) return
  isSaving.value = true
  try {
    const payload: { nickname?: string; username?: string; avatarUrl?: string } = {
      nickname: profileForm.value.nickname,
      avatarUrl: profileForm.value.avatarUrl || undefined,
    }
    const username = profileForm.value.username.trim()
    if (username) {
      payload.username = username
    }
    await authStore.updateProfile(payload)
    // Brief toast could be better, using simple alert for demonstration.
    // Replace with a real toast in production if desired.
    close() 
  } catch (error: any) {
    alert(error.message || '保存失败')
  } finally {
    isSaving.value = false
  }
}

const promptUpdate = async (field: 'phone' | 'email') => {
  const current = field === 'phone' ? (user.value?.phone || '') : (user.value?.email || '')
  const label = field === 'phone' ? '新手机号码' : '新验证邮箱'
  const newValue = window.prompt(`请输入${label}：`, current)
  
  if (newValue !== null && newValue !== current) {
    try {
      await authStore.updateProfile({ [field]: newValue })
    } catch(err: any) {
      alert(`绑定失败: ${err.message}`)
    }
  }
}

const alertNotImpl = () => {
  alert('暂未开放 MFA 参数配置')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
/* Ensure clean placeholder color in modern browsers */
input::placeholder {
  color: #9ca3af;
  font-weight: 400;
}
</style>
