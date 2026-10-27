<template>
  <div class="h-screen w-full flex bg-white overflow-hidden font-sans">
    <div class="relative hidden lg:flex flex-col w-[66.666%] overflow-hidden bg-gradient-to-br from-[#4A85F6] via-[#3B66D6] to-[#2B3CA0]">
      <div
        class="absolute inset-0 z-0 opacity-20 pointer-events-none"
        style="background-image: linear-gradient(rgba(255, 255, 255, 0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.2) 1px, transparent 1px); background-size: 40px 40px;"
      ></div>

      <div class="absolute top-10 left-12 z-10 flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-md bg-white flex items-center justify-center shadow-sm">
          <span class="material-symbols-outlined text-[#3B66D6] text-[20px]">auto_fix_high</span>
        </div>
        <span class="text-white font-bold text-xl tracking-wide">AI 内容自动化</span>
      </div>

      <div class="flex-1 flex flex-col justify-center items-center text-center px-12 z-10 mt-[-5%]">
        <h1 class="text-white font-bold text-[44px] tracking-wider mb-6 drop-shadow-md">
          AI 内容自动化平台
        </h1>
        <p class="text-white/90 text-[18px] leading-relaxed max-w-xl mb-8 tracking-wide font-light">
          登录后自动拉取当前用户、权限与会话信息，支持账号密码和验证码两种方式。
        </p>
      </div>
    </div>

    <div class="flex-1 flex flex-col relative w-full lg:w-[33.333%] bg-white min-w-[400px]">
      <div class="absolute top-8 right-8 flex flex-col gap-3">
        <button class="w-10 h-10 rounded-full flex items-center justify-center bg-gray-50 text-slate-300 shadow-sm border border-gray-100">
          <span class="material-symbols-outlined text-[20px]">grid_view</span>
        </button>
        <button class="w-10 h-10 rounded-full flex items-center justify-center bg-gray-50 text-slate-300 shadow-sm border border-gray-100">
          <span class="material-symbols-outlined text-[20px]">translate</span>
        </button>
      </div>

      <div class="flex-1 flex flex-col justify-center px-10 xl:px-14 max-w-[440px] mx-auto w-full">
        <div class="mb-8 mt-12">
          <h2 class="text-[32px] font-bold text-gray-900 mb-2 tracking-tight">
            {{ viewMode === 'login' ? '欢迎回来' : '开启创意之旅' }}
          </h2>
          <p class="text-gray-500 text-[15px]">
            {{ viewMode === 'login' ? '请登录您的账号' : '创建一个新账号以开始使用' }}
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <template v-if="viewMode === 'register'">
            <div class="relative">
              <input
                v-model="nickname"
                type="text"
                placeholder="您的昵称"
                class="w-full h-12 px-4 border border-gray-200 rounded-sm text-[14px] text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#1E62D0] focus:ring-1 focus:ring-[#1E62D0] transition-colors"
                required
              >
            </div>
          </template>

          <template v-if="mode === 'sms' || viewMode === 'register'">
            <div class="relative">
              <input
                v-model="contactInfo"
                type="text"
                :placeholder="viewMode === 'register' ? '手机号或邮箱（注册标识）' : '手机号或邮箱'"
                class="w-full h-12 px-4 border border-gray-200 rounded-sm text-[14px] text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#1E62D0] focus:ring-1 focus:ring-[#1E62D0] transition-colors"
              >
            </div>

            <div class="relative flex">
              <input
                v-model="verificationCode"
                type="text"
                placeholder="验证码"
                class="flex-1 h-12 px-4 border border-gray-200 border-r-0 rounded-l-sm text-[14px] text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#1E62D0] focus:ring-1 focus:ring-[#1E62D0] transition-colors z-10 focus:z-20"
              >
              <button
                type="button"
                :disabled="sendingCode || cooldownSeconds > 0"
                @click="handleSendCode"
                class="h-12 px-4 border border-gray-200 rounded-r-sm bg-white hover:bg-gray-50 text-[13px] text-gray-700 font-medium transition-colors whitespace-nowrap focus:outline-none focus:border-[#1E62D0] focus:ring-1 focus:ring-[#1E62D0] z-10 focus:z-20 disabled:bg-gray-100 disabled:text-gray-400"
              >
                {{ codeButtonText }}
              </button>
            </div>

            <div v-if="viewMode === 'register'" class="relative">
              <input
                v-model="password"
                type="password"
                placeholder="请设置密码"
                class="w-full h-12 px-4 border border-gray-200 rounded-sm text-[14px] text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#1E62D0] focus:ring-1 focus:ring-[#1E62D0] transition-colors"
              >
            </div>
          </template>

          <template v-else-if="viewMode === 'login'">
            <div class="relative">
              <input
                v-model="accountStr"
                type="text"
                placeholder="用户名 / 手机号 / 邮箱"
                class="w-full h-12 px-4 border border-gray-200 rounded-sm text-[14px] text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#1E62D0] focus:ring-1 focus:ring-[#1E62D0] transition-colors"
              >
            </div>

            <div class="relative">
              <input
                v-model="password"
                type="password"
                placeholder="请输入密码"
                class="w-full h-12 px-4 border border-gray-200 rounded-sm text-[14px] text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#1E62D0] focus:ring-1 focus:ring-[#1E62D0] transition-colors"
              >
            </div>

            <div class="flex justify-end pt-1">
              <span class="text-[#1E62D0] text-[13px] hover:underline cursor-pointer" @click="mode = 'sms'">
                密码不通时可切换验证码登录
              </span>
            </div>
          </template>

          <div class="flex items-start pt-2 mb-2">
            <label class="flex items-start cursor-pointer group mt-0.5">
              <div class="relative flex items-center justify-center mt-[1px]">
                <input
                  v-model="agreed"
                  type="checkbox"
                  class="peer sr-only"
                >
                <div class="w-[14px] h-[14px] border border-gray-300 rounded-[2px] peer-checked:bg-[#1E62D0] peer-checked:border-[#1E62D0] transition-colors flex items-center justify-center">
                  <svg class="w-3 h-3 text-white opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
              <span class="ml-2 text-[13px] text-gray-600 leading-tight">
                我已阅读并同意 <a href="#" class="text-[#1E62D0] hover:underline">隐私政策</a> 和 <a href="#" class="text-[#1E62D0] hover:underline">服务条款</a>
              </span>
            </label>
          </div>

          <div v-if="debugMessage" class="rounded-sm bg-slate-50 border border-slate-200 px-3 py-2 text-[12px] text-slate-600">
            {{ debugMessage }}
          </div>

          <div v-if="errorMessage" class="rounded-sm bg-red-50 border border-red-100 px-3 py-2 text-[13px] text-red-600">
            {{ errorMessage }}
          </div>

          <div class="pt-3 space-y-3.5">
            <button
              type="submit"
              :disabled="submitting"
              class="w-full h-[42px] bg-[#1055c6] hover:bg-[#0c44a3] text-white text-[14px] font-medium rounded-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-[#1E62D0] disabled:bg-[#7ea2df]"
            >
              {{ submitting ? '处理中...' : viewMode === 'register' ? '立即注册' : (mode === 'sms' ? '验证码登录' : '账号登录') }}
            </button>
            <button
              v-if="viewMode === 'login'"
              type="button"
              @click="toggleMode"
              class="w-full h-[42px] bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700 text-[14px] font-medium rounded-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-200"
            >
              {{ mode === 'sms' ? '切换账号密码登录' : '切换验证码登录' }}
            </button>
          </div>

          <div class="text-center pt-4 border-t border-gray-100 mt-4">
            <p class="text-[13px] text-gray-500">
              {{ viewMode === 'login' ? '还没有账号？' : '已经有账号？' }}
              <span 
                class="text-[#1E62D0] font-medium hover:underline cursor-pointer ml-1"
                @click="viewMode = viewMode === 'login' ? 'register' : 'login'; errorMessage = ''; debugMessage = '';"
              >
                {{ viewMode === 'login' ? '立即注册' : '返回登录' }}
              </span>
            </p>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { authStore, getAuthErrorMessage } from '../../auth/store'
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()

const viewMode = ref<'login' | 'register'>('login')
const mode = ref<'sms' | 'account'>('sms')
const agreed = ref(false)
const contactInfo = ref('')
const verificationCode = ref('')
const accountStr = ref('')
const nickname = ref('')
const password = ref('')
const submitting = ref(false)
const sendingCode = ref(false)
const cooldownSeconds = ref(0)
const errorMessage = ref('')
const debugMessage = ref('')

let cooldownTimer: number | null = null

const codeButtonText = computed(() => {
  if (sendingCode.value) {
    return '发送中...'
  }

  if (cooldownSeconds.value > 0) {
    return `${cooldownSeconds.value}s 后重试`
  }

  return '发送验证码'
})

const toggleMode = () => {
  errorMessage.value = ''
  debugMessage.value = ''
  mode.value = mode.value === 'sms' ? 'account' : 'sms'
}

const startCooldown = (seconds = 60) => {
  cooldownSeconds.value = seconds

  if (cooldownTimer) {
    window.clearInterval(cooldownTimer)
  }

  cooldownTimer = window.setInterval(() => {
    cooldownSeconds.value -= 1
    if (cooldownSeconds.value <= 0 && cooldownTimer) {
      window.clearInterval(cooldownTimer)
      cooldownTimer = null
    }
  }, 1000)
}

const resolveRedirect = () => {
  const redirect = route.query.redirect
  return typeof redirect === 'string' && redirect ? redirect : '/dashboard'
}

const validateAgreement = () => {
  if (!agreed.value) {
    errorMessage.value = '请先阅读并同意隐私政策和服务条款'
    return false
  }

  return true
}

const handleSendCode = async () => {
  errorMessage.value = ''
  debugMessage.value = ''

  if (!validateAgreement()) {
    return
  }

  if (!contactInfo.value.trim()) {
    errorMessage.value = '请输入手机号或邮箱'
    return
  }

  sendingCode.value = true
  try {
    const data = await authStore.sendCode(contactInfo.value, viewMode.value === 'register' ? 'register' : 'login')
    debugMessage.value = data.debugCode ? `开发环境验证码：${data.debugCode}` : '验证码已发送，请查收'
    startCooldown(Math.min(data.expireSeconds, 60))
  } catch (error) {
    errorMessage.value = getAuthErrorMessage(error)
  } finally {
    sendingCode.value = false
  }
}

const handleSubmit = async () => {
  errorMessage.value = ''
  debugMessage.value = ''

  if (!validateAgreement()) {
    return
  }

  if (viewMode.value === 'register') {
    if (!contactInfo.value || !verificationCode.value || !nickname.value) {
      errorMessage.value = '请填写完整注册信息'
      return
    }

    submitting.value = true
    try {
      await authStore.register(contactInfo.value, verificationCode.value, password.value, nickname.value)
      // register() in store now handles auto-login if status is correct
      if (authStore.isAuthenticated.value) {
        await router.replace(resolveRedirect())
      } else {
        viewMode.value = 'login'
        errorMessage.value = '注册成功，请登录'
      }
    } catch (error) {
      errorMessage.value = getAuthErrorMessage(error)
    } finally {
      submitting.value = false
    }
    return
  }

  const identity = mode.value === 'sms' ? contactInfo.value.trim() : accountStr.value.trim()
  const credential = mode.value === 'sms' ? verificationCode.value.trim() : password.value.trim()

  if (!identity || !credential) {
    errorMessage.value = mode.value === 'sms' ? '请输入手机号/邮箱和验证码' : '请输入账号和密码'
    return
  }

  submitting.value = true
  try {
    await authStore.login(identity, credential)
    await router.replace(resolveRedirect())
  } catch (error) {
    errorMessage.value = getAuthErrorMessage(error)
  } finally {
    submitting.value = false
  }
}

onBeforeUnmount(() => {
  if (cooldownTimer) {
    window.clearInterval(cooldownTimer)
  }
})
</script>

<style scoped>
input:focus,
button:focus {
  z-index: 20;
}
</style>
