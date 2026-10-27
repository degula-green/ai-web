<template>
  <div class="flex flex-1 w-full h-full min-h-0 bg-transparent text-text-main">
    <main class="flex-1 min-h-0 overflow-y-auto">
      <header
        class="sticky top-0 z-20 flex items-center justify-between h-16 px-8 border-b border-border bg-surface/80 backdrop-blur-md"
      >
        <div class="flex items-center gap-4">
          <h2 class="text-lg font-bold">平台授权中心</h2>
        </div>
        <div class="flex items-center gap-4">
          <button
            @click="handleRefresh()"
            class="flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors bg-white border rounded-lg shadow-sm text-text-main border-border hover:bg-surface-secondary"
          >
            <span class="text-sm material-symbols-outlined" :class="{ 'animate-spin': refreshing }">refresh</span>
            刷新状态
          </button>
          <button
            @click="showPlatformPicker = true"
            class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white transition-colors rounded-lg shadow-sm bg-primary hover:bg-primary-hover shadow-primary/20"
          >
            <span class="text-sm material-symbols-outlined">add</span>
            新增平台授权
          </button>
        </div>
      </header>

      <div class="w-full p-8 space-y-8">
        <div class="flex gap-8 border-b border-border">
          <button
            @click="activeTab = 'list'"
            :class="[
              'pb-4 text-sm transition-all relative',
              activeTab === 'list' ? 'font-bold text-primary' : 'font-medium text-text-secondary hover:text-text-main'
            ]"
          >
            平台列表
            <div v-if="activeTab === 'list'" class="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-full"></div>
          </button>
          <button
            @click="activeTab = 'history'"
            :class="[
              'pb-4 text-sm transition-all relative',
              activeTab === 'history' ? 'font-bold text-primary' : 'font-medium text-text-secondary hover:text-text-main'
            ]"
          >
            授权历史
            <div v-if="activeTab === 'history'" class="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-full"></div>
          </button>
          <button
            @click="activeTab = 'audit'"
            :class="[
              'pb-4 text-sm transition-all relative',
              activeTab === 'audit' ? 'font-bold text-primary' : 'font-medium text-text-secondary hover:text-text-main'
            ]"
          >
            安全审计
            <div v-if="activeTab === 'audit'" class="absolute bottom-0 left-0 w-full h-0.5 bg-primary rounded-full"></div>
          </button>
        </div>

        <div v-if="activeTab === 'list'" class="space-y-8 animate-in fade-in duration-500">
          <section class="p-6 border rounded-xl bg-surface border-border">
            <div class="flex items-center gap-2 mb-6">
              <span class="material-symbols-outlined text-primary">settings_suggest</span>
              <h3 class="text-base font-bold">全局发布设置</h3>
            </div>
            <div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              <div
                v-for="opt in globalOptions"
                :key="opt.title"
                class="flex items-center justify-between p-4 rounded-lg bg-background group"
              >
                <div>
                  <p class="text-sm font-bold group-hover:text-primary transition-colors">{{ opt.title }}</p>
                  <p class="text-xs text-text-secondary">{{ opt.desc }}</p>
                </div>
                <label class="relative inline-flex items-center cursor-pointer">
                  <input :checked="opt.checked" class="sr-only peer" type="checkbox" />
                  <div
                    class="w-11 h-6 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-surface after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"
                  ></div>
                </label>
              </div>
            </div>
          </section>

          <div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            <div
              v-for="p in displayPlatforms"
              :key="p.code"
              class="relative p-5 transition-all border rounded-xl hover:shadow-xl hover:shadow-primary/5 bg-surface"
              :class="[p.authStatus === 'expired' ? 'border-red-200' : 'border-border']"
            >
              <div class="flex items-start justify-between mb-4">
                <div class="flex items-center justify-center overflow-hidden w-12 h-12 rounded-lg bg-surface-secondary">
                  <div :class="['flex items-center justify-center w-10 h-10 rounded-full', p.iconBg]">
                    <span :class="['material-symbols-outlined', p.iconText]">{{ p.icon }}</span>
                  </div>
                </div>

                <span
                  v-if="p.authStatus === 'authorized'"
                  class="px-2 py-1 text-[10px] font-bold text-green-600 uppercase border border-green-200 rounded-md bg-green-50"
                >
                  已连接
                </span>
                <span
                  v-else-if="p.authStatus === 'expired'"
                  class="px-2 py-1 text-[10px] font-bold text-red-600 uppercase border border-red-200 rounded-md bg-red-50"
                >
                  需重授
                </span>
                <span
                  v-else
                  class="px-2 py-1 text-[10px] font-bold uppercase border rounded-md text-text-tertiary border-border bg-surface-secondary"
                >
                  未连接
                </span>
              </div>

              <h4 class="text-base font-bold">{{ p.name }}</h4>

              <div v-if="p.bound" class="mb-6 mt-2 text-sm text-text-secondary space-y-1">
                <p>
                  已授权账号: <span class="font-medium text-text-main">{{ p.accountCount }}</span>
                </p>
                <div class="flex items-center gap-2">
                  <img
                    v-if="p.latestAvatar"
                    :src="p.latestAvatar"
                    alt="avatar"
                    referrerpolicy="no-referrer"
                    loading="lazy"
                    class="w-6 h-6 rounded-full border border-border object-cover"
                  />
                  <span v-else class="material-symbols-outlined text-base text-text-tertiary">account_circle</span>
                  <span class="text-text-main truncate">最近账号：{{ p.accountName }}</span>
                </div>
              </div>
              <p v-else class="mb-6 mt-2 text-sm text-text-secondary">当前暂无已授权账号</p>

                <button
                  v-if="p.bound"
                  @click="openManageModal(p.code)"
                  class="w-full py-2 text-sm font-bold transition-all rounded-lg bg-surface-secondary text-text-main hover:bg-border flex items-center justify-center gap-1"
                >
                授权管理
                <span class="material-symbols-outlined text-sm">open_in_new</span>
              </button>
              <button
                v-else-if="p.authStatus === 'expired'"
                @click="handleAuth(p.code)"
                class="w-full py-2 text-sm font-bold text-orange-600 transition-colors border border-orange-200 rounded-lg bg-orange-50 hover:bg-orange-100"
              >
                重新授权
              </button>
              <button
                v-else
                @click="handleAuth(p.code)"
                class="w-full py-2 text-sm font-bold text-white transition-colors rounded-lg shadow-sm bg-primary hover:bg-primary-hover shadow-primary/20"
              >
                立即授权
              </button>
            </div>
          </div>

          <div class="flex items-start gap-4 p-4 border rounded-xl bg-primary/5 border-primary/20">
            <span class="mt-1 material-symbols-outlined text-primary">info</span>
            <div>
              <p class="text-sm font-bold text-text-main">关于平台授权安全</p>
              <p class="mt-1 text-xs text-text-secondary leading-relaxed">
                系统通过浏览器自动化获取平台会话信息，并将会话快照持久化到数据库。后续采集优先使用数据库中的授权信息，只有会话失效时才需要重新扫码授权。
              </p>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'history'" class="animate-in slide-in-from-bottom-4 duration-500 overflow-hidden">
          <div class="bg-surface border border-border rounded-xl overflow-hidden shadow-soft">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-surface-secondary/50 border-b border-border">
                  <th class="px-6 py-4 text-xs font-bold text-text-tertiary uppercase tracking-wider">平台/账号</th>
                  <th class="px-6 py-4 text-xs font-bold text-text-tertiary uppercase tracking-wider">变更事项</th>
                  <th class="px-6 py-4 text-xs font-bold text-text-tertiary uppercase tracking-wider">执行状态</th>
                  <th class="px-6 py-4 text-xs font-bold text-text-tertiary uppercase tracking-wider">执行时间</th>
                  <th class="px-6 py-4 text-xs font-bold text-text-tertiary uppercase tracking-wider">IP地址</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-border/50">
                <tr v-for="log in authHistory" :key="log.id" class="hover:bg-background/50 transition-colors">
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded bg-surface-secondary flex items-center justify-center">
                        <span class="material-symbols-outlined text-sm text-text-secondary">{{ getIconByCode(log.platformCode) }}</span>
                      </div>
                      <div>
                        <p class="text-sm font-bold underline decoration-primary/20 hover:decoration-primary transition-all decoration-2 underline-offset-4 cursor-help">
                          {{ log.accountName || '-' }}
                        </p>
                        <p class="text-[10px] text-text-tertiary uppercase">{{ log.platformCode }}</p>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <span :class="['px-2 py-0.5 rounded text-[10px] font-bold', getEventColor(log.eventType)]">
                      {{ getEventLabel(log.eventType) }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm font-medium">
                    <div class="flex items-center gap-1.5">
                      <div :class="['w-1.5 h-1.5 rounded-full', log.eventStatus === 'success' ? 'bg-green-500' : 'bg-red-500']"></div>
                      <span :class="log.eventStatus === 'success' ? 'text-green-600' : 'text-red-500'">
                        {{ log.eventStatus === 'success' ? '成功' : '失败' }}
                      </span>
                    </div>
                  </td>
                  <td class="px-6 py-4 text-sm text-text-secondary font-mono">{{ formatDate(log.createdAt) }}</td>
                  <td class="px-6 py-4 text-sm text-text-tertiary">127.0.0.1 (本地网络)</td>
                </tr>
                <tr v-if="authHistory.length === 0">
                  <td colspan="5" class="px-6 py-12 text-center text-text-tertiary font-medium">暂无授权变更历史记录</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-else class="rounded-xl border border-border bg-surface p-6 text-sm text-text-secondary">
          安全审计模块待接入。
        </div>
      </div>
    </main>
  </div>

  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="showManageModal"
      class="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4"
      @click.self="closeManageModal"
    >
      <div class="w-full max-w-2xl rounded-2xl border border-border bg-surface shadow-2xl">
        <div class="flex items-center justify-between px-6 py-4 border-b border-border">
          <div>
            <h3 class="text-lg font-bold">{{ currentPlatformName }} 授权管理</h3>
            <p class="text-xs text-text-secondary mt-1">可新增账号授权，并管理当前平台已授权账号。</p>
          </div>
          <button @click="closeManageModal" class="material-symbols-outlined text-text-tertiary hover:text-text-main">close</button>
        </div>

        <div class="px-6 py-4">
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm text-text-secondary">已授权 {{ managedAccounts.length }} 个账号</p>
            <button
              @click="addAccountInModal"
              :disabled="!managePlatformCode"
              class="px-3 py-1.5 text-sm font-medium text-white rounded-lg bg-primary hover:bg-primary-hover disabled:cursor-not-allowed disabled:bg-primary/60"
            >
              <span>新增账号授权</span>
            </button>
          </div>

          <div v-if="managedAccounts.length === 0" class="rounded-lg border border-dashed border-border p-8 text-center text-sm text-text-secondary">
            当前平台还没有已授权账号。
          </div>

          <div v-else class="space-y-3 max-h-[420px] overflow-y-auto pr-1">
            <div
              v-for="acc in managedAccounts"
              :key="acc.accountId"
              class="flex items-center justify-between rounded-xl border border-border p-3"
            >
              <div class="flex items-center gap-3 min-w-0">
                <img
                  v-if="acc.avatarUrl && !failedAvatarIds.has(acc.accountId)"
                  :src="resolveAvatarUrl(acc.avatarUrl)"
                  alt="avatar"
                  referrerpolicy="no-referrer"
                  loading="lazy"
                  class="w-10 h-10 rounded-full border border-border object-cover"
                  @error="markAvatarFailed(acc.accountId)"
                />
                <div v-else class="w-10 h-10 rounded-full border border-border flex items-center justify-center text-text-tertiary">
                  <span class="material-symbols-outlined">account_circle</span>
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-text-main truncate">{{ getAccountTitle(acc) }}</p>
                  <p class="text-xs text-text-secondary truncate">
                    账号状态：{{ getAccountStatusLabel(acc.accountStatus || acc.authStatus) }}
                    <span class="mx-1">|</span>
                    会话状态：{{ getSessionStatusLabel(acc.sessionStatus) }}
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <span :class="['px-2 py-0.5 rounded text-[10px] font-bold', getAccountStatusColor(acc.accountStatus || acc.authStatus)]">
                  {{ getAccountStatusLabel(acc.accountStatus || acc.authStatus) }}
                </span>
                <button
                  @click="handleUnbind(acc.accountId)"
                  class="px-2 py-1 text-xs font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md"
                >
                  解绑
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="showPlatformPicker"
      class="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4"
      @click.self="showPlatformPicker = false"
    >
      <div class="w-full max-w-2xl rounded-2xl border border-border bg-surface shadow-2xl">
        <div class="flex items-center justify-between px-6 py-4 border-b border-border">
          <h3 class="text-lg font-bold">新增平台授权</h3>
          <button @click="showPlatformPicker = false" class="material-symbols-outlined text-text-tertiary hover:text-text-main">close</button>
        </div>
        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            v-for="p in defaultPlatforms"
            :key="`picker-${p.code}`"
            @click="startAuthFromPicker(p.code)"
            class="flex items-center justify-between rounded-xl border border-border p-3 hover:border-primary/30 hover:bg-primary/5 transition-colors text-left"
          >
            <span class="text-sm font-medium">{{ p.name }}</span>
            <span class="material-symbols-outlined text-text-tertiary">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>

  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="showBridgeModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4"
      @click.self="closeBridgeModal"
    >
      <div class="w-full max-w-3xl rounded-2xl border border-border bg-surface shadow-2xl">
        <div class="flex items-start justify-between px-6 py-4 border-b border-border">
          <div>
            <h3 class="text-lg font-bold">使用 CookieBridge 绑定 {{ currentBridgePlatformName }}</h3>
            <p class="text-xs text-text-secondary mt-1">
              先下载并安装授权插件，登录目标平台后回到这里刷新绑定。
            </p>
          </div>
          <button @click="closeBridgeModal" class="material-symbols-outlined text-text-tertiary hover:text-text-main">close</button>
        </div>

        <div class="px-6 py-5 space-y-5">
          <div class="rounded-xl border border-blue-100 bg-blue-50/70 p-4 text-sm text-blue-900 space-y-3">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="font-bold mb-1">安装授权插件</p>
                <p class="text-xs leading-6">
                  当前浏览器不能静默安装扩展。请下载插件包，解压后在 Chrome 扩展管理页加载。
                </p>
              </div>
              <button
                @click="downloadBridgeExtension"
                :disabled="extensionDownloading"
                class="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-white hover:bg-primary-hover disabled:cursor-not-allowed disabled:bg-primary/60"
              >
                <span v-if="extensionDownloading">下载中...</span>
                <span v-else>下载授权插件</span>
              </button>
            </div>
            <div class="grid grid-cols-1 gap-2 text-xs leading-6 md:grid-cols-3">
              <div class="rounded-lg bg-white/70 p-3">
                <p class="font-bold text-blue-950">1. 下载并解压</p>
                <p>点击“下载授权插件”，解压 zip 文件。</p>
              </div>
              <div class="rounded-lg bg-white/70 p-3">
                <p class="font-bold text-blue-950">2. 加载扩展</p>
                <p>打开 <button class="font-bold underline" @click="openChromeExtensions">chrome://extensions</button>，选择“加载已解压的扩展程序”。</p>
              </div>
              <div class="rounded-lg bg-white/70 p-3">
                <p class="font-bold text-blue-950">3. 登录并刷新</p>
                <p>登录 {{ currentBridgePlatformName }} 后点插件的 Sync All，再回到这里刷新。</p>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-bold text-text-main">已连接客户端</p>
              <p class="text-xs text-text-secondary">只会把当前登录用户绑定到选中的 CookieBridge 客户端。</p>
            </div>
            <button
              @click="loadBridgeClients"
              :disabled="bridgeLoading"
              class="flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-sm font-medium hover:bg-surface-secondary disabled:cursor-not-allowed"
            >
              <span class="material-symbols-outlined text-sm" :class="{ 'animate-spin': bridgeLoading }">refresh</span>
              刷新
            </button>
          </div>

          <div v-if="bridgeError" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {{ bridgeError }}
          </div>

          <div v-if="bridgeLoading" class="rounded-xl border border-dashed border-border p-8 text-center text-sm text-text-secondary">
            正在读取 CookieBridge 客户端...
          </div>

          <div v-else-if="bridgeClients.length === 0" class="rounded-xl border border-dashed border-border p-8 text-center text-sm text-text-secondary">
            未发现已连接的 CookieBridge 客户端。
          </div>

          <div v-else class="grid grid-cols-1 gap-3 max-h-[420px] overflow-y-auto pr-1">
            <div
              v-for="client in bridgeClients"
              :key="client.clientId"
              class="rounded-xl border border-border p-4 transition-colors hover:border-primary/30"
            >
              <div class="flex items-start justify-between gap-4">
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <span
                      :class="[
                        'inline-block h-2 w-2 rounded-full',
                        client.connected ? 'bg-green-500' : 'bg-gray-300'
                      ]"
                    ></span>
                    <p class="truncate text-sm font-bold text-text-main">{{ getBridgeClientName(client) }}</p>
                  </div>
                  <p class="mt-1 truncate text-xs text-text-tertiary">
                    客户端识别码：<span class="font-mono">{{ formatBridgeClientId(client.clientId) }}</span>
                  </p>
                  <p class="mt-2 text-xs text-text-secondary">
                    {{ getBridgePlatformLabel(client) }}
                    <span class="mx-1">|</span>
                    最后连接：{{ formatBridgeTime(client.lastSeen) }}
                  </p>
                </div>

                <button
                  @click="handleBridgeClientAction(client)"
                  :disabled="!client.connected || !isBridgePlatformSupported() || bindingClientId === client.clientId"
                  class="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-white hover:bg-primary-hover disabled:cursor-not-allowed disabled:bg-primary/50"
                >
                  <span v-if="bindingClientId === client.clientId">绑定中...</span>
                  <span v-else-if="!isBridgePlatformSupported()">暂不支持</span>
                  <span v-else-if="hasBridgeCookies(client)">绑定此客户端</span>
                  <span v-else>去平台登录</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  platformAccountApi,
  type AccountShortInfo,
  type AuthHistoryItem,
  type CookieBridgeClientInfo,
} from '../api/platformAccount'

type Tab = 'list' | 'history' | 'audit'
type PlatformCode =
  | 'douyin'
  | 'xiaohongshu'
  | 'kuaishou'
  | 'bilibili'
  | 'weibo'
  | 'tieba'
  | 'zhihu'

interface PlatformMeta {
  code: PlatformCode
  name: string
  icon: string
  iconBg: string
  iconText: string
}

const activeTab = ref<Tab>('list')
const refreshing = ref(false)
const showManageModal = ref(false)
const managePlatformCode = ref<string | null>(null)
const showPlatformPicker = ref(false)
const showBridgeModal = ref(false)
const bridgePlatformCode = ref<string | null>(null)
const bridgeClients = ref<CookieBridgeClientInfo[]>([])
const bridgeLoading = ref(false)
const bridgeError = ref('')
const bindingClientId = ref<string | null>(null)
const extensionDownloading = ref(false)

const globalOptions = [
  { title: '自动回复评论', desc: '使用AI自动回复粉丝留言', checked: true },
  { title: '智能去除水印', desc: '发布前自动清理视频水印', checked: true },
  { title: '自动标签优化', desc: '根据趋势自动匹配话题', checked: false },
]

const defaultPlatforms: PlatformMeta[] = [
  { code: 'douyin', name: '抖音', icon: 'music_note', iconBg: 'bg-surface-secondary', iconText: 'text-text-secondary' },
  { code: 'xiaohongshu', name: '小红书', icon: 'auto_awesome', iconBg: 'bg-red-100', iconText: 'text-red-500' },
  { code: 'kuaishou', name: '快手', icon: 'bolt', iconBg: 'bg-orange-100', iconText: 'text-orange-600' },
  { code: 'bilibili', name: 'B站', icon: 'tv', iconBg: 'bg-blue-100', iconText: 'text-blue-500' },
  { code: 'weibo', name: '微博', icon: 'alternate_email', iconBg: 'bg-yellow-100', iconText: 'text-yellow-700' },
  { code: 'tieba', name: '贴吧', icon: 'forum', iconBg: 'bg-indigo-100', iconText: 'text-indigo-600' },
  { code: 'zhihu', name: '知乎', icon: 'psychology', iconBg: 'bg-sky-100', iconText: 'text-sky-600' },
]

const serverAccounts = ref<AccountShortInfo[]>([])
const failedAvatarIds = ref(new Set<number>())

function resolveAvatarUrl(url?: string | null): string {
  const normalized = (url || '').trim()
  if (!normalized) return ''
  if (normalized.startsWith('//')) return `https:${normalized}`
  return normalized
}

function markAvatarFailed(accountId: number) {
  failedAvatarIds.value = new Set([...failedAvatarIds.value, accountId])
}

const authHistory = ref<AuthHistoryItem[]>([])

const accountsByPlatform = computed<Record<string, AccountShortInfo[]>>(() => {
  return serverAccounts.value.reduce<Record<string, AccountShortInfo[]>>((acc, item) => {
    if (!acc[item.platformCode]) acc[item.platformCode] = []
    acc[item.platformCode].push(item)
    return acc
  }, {})
})

const displayPlatforms = computed(() => {
  return defaultPlatforms.map((p) => {
    const list = accountsByPlatform.value[p.code] || []
    const latest = list[0]
    const hasAuthorized = list.some((item) => (item.authStatus || '').toLowerCase() === 'authorized')
    const hasExpired = list.some((item) => {
      const status = (item.authStatus || '').toLowerCase()
      return status === 'expired' || status === 'need_reauth'
    })

    return {
      ...p,
      bound: list.length > 0,
      accountCount: list.length,
      accountName: getAccountTitle(latest),
      latestAvatar: latest?.avatarUrl,
      authStatus: hasAuthorized ? 'authorized' : hasExpired ? 'expired' : 'need_reauth',
    }
  })
})

const managedAccounts = computed(() => {
  if (!managePlatformCode.value) return []
  return accountsByPlatform.value[managePlatformCode.value] || []
})

const currentPlatformName = computed(() => {
  return defaultPlatforms.find((p) => p.code === managePlatformCode.value)?.name || '平台'
})

const currentBridgePlatformName = computed(() => {
  return defaultPlatforms.find((p) => p.code === bridgePlatformCode.value)?.name || '平台'
})

const fetchAccounts = async () => {
  try {
    const res = await platformAccountApi.listAccounts()
    serverAccounts.value = res.list
  } catch (err) {
    console.error('获取账号列表失败:', err)
  }
}

const fetchHistory = async () => {
  try {
    const res = await platformAccountApi.getAuthHistory()
    authHistory.value = res.list
  } catch (err) {
    console.error('获取历史记录失败:', err)
  }
}

const handleRefresh = async () => {
  refreshing.value = true
  await fetchAccounts()
  if (activeTab.value === 'history') await fetchHistory()
  setTimeout(() => {
    refreshing.value = false
  }, 500)
}

const openManageModal = (platformCode: string) => {
  managePlatformCode.value = platformCode
  showManageModal.value = true
}

const closeManageModal = () => {
  showManageModal.value = false
}

const openCookieBridgeModal = async (platformCode: string) => {
  bridgePlatformCode.value = platformCode
  bridgeError.value = ''
  showBridgeModal.value = true
  await loadBridgeClients()
}

const closeBridgeModal = () => {
  showBridgeModal.value = false
  bridgeError.value = ''
  bindingClientId.value = null
}

const loadBridgeClients = async () => {
  bridgeLoading.value = true
  bridgeError.value = ''
  try {
    const res = await platformAccountApi.listCookieBridgeAccounts()
    bridgeClients.value = res.list
  } catch (err: any) {
    bridgeClients.value = []
    bridgeError.value = err?.data?.msg || err?.data?.detail || err?.message || 'CookieBridge 服务不可用'
  } finally {
    bridgeLoading.value = false
  }
}

const downloadBridgeExtension = async () => {
  extensionDownloading.value = true
  bridgeError.value = ''
  try {
    const url = platformAccountApi.getCookieBridgeExtensionDownloadUrl()
    const link = document.createElement('a')
    link.href = url
    link.download = 'CookieBridge-extension.zip'
    link.target = '_blank'
    link.rel = 'noopener'
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (err: any) {
    bridgeError.value = err?.message || '下载授权插件失败'
  } finally {
    extensionDownloading.value = false
  }
}

const openChromeExtensions = () => {
  bridgeError.value = '浏览器安全限制不允许网页直接打开 chrome://extensions，请复制地址到地址栏：chrome://extensions'
}

const bindBridgeClient = async (client: CookieBridgeClientInfo) => {
  if (!bridgePlatformCode.value || !client.clientId) return
  bindingClientId.value = client.clientId
  try {
    await platformAccountApi.bindCookieBridgeClient({
      platformCode: bridgePlatformCode.value,
      clientId: client.clientId,
      setDefault: true,
    })
    closeBridgeModal()
    await fetchAccounts()
    if (activeTab.value === 'history') await fetchHistory()
    alert('CookieBridge 账号绑定成功')
  } catch (err: any) {
    bridgeError.value = err?.data?.msg || err?.data?.detail || err?.message || '绑定失败'
  } finally {
    bindingClientId.value = null
  }
}

const handleBridgeClientAction = async (client: CookieBridgeClientInfo) => {
  if (!client.connected) {
    bridgeError.value = 'CookieBridge 客户端未连接，请先打开插件并点击 Sync All'
    return
  }
  if (!isBridgePlatformSupported()) {
    bridgeError.value = `CookieBridge 暂不支持 ${currentBridgePlatformName.value}，当前采集授权先使用抖音、小红书、快手、B站、微博、贴吧、知乎。`
    return
  }
  if (!hasBridgeCookies(client)) {
    openPlatformLogin()
    bridgeError.value = `已打开 ${currentBridgePlatformName.value} 登录页。请在同一个 Chrome 中登录后，回到 CookieBridge 插件点击 Sync All，再刷新这里。`
    return
  }
  await bindBridgeClient(client)
}

const handleAuth = async (platformCode: string) => {
  await openCookieBridgeModal(platformCode)
}

const addAccountInModal = async () => {
  if (!managePlatformCode.value) return
  await handleAuth(managePlatformCode.value)
}

const startAuthFromPicker = async (platformCode: string) => {
  showPlatformPicker.value = false
  await handleAuth(platformCode)
}

const handleUnbind = async (accountId: number) => {
  if (!confirm('确认要解绑此账号吗？解绑后该账号会被标记为需重新授权。')) return
  try {
    await platformAccountApi.unbindAccount(accountId)
    await fetchAccounts()
    if (activeTab.value === 'history') await fetchHistory()
  } catch (err) {
    console.error('解绑失败:', err)
    alert('解绑失败')
  }
}

const getAccountTitle = (acc?: AccountShortInfo) => {
  if (!acc) return '-'
  return acc.nickname || acc.accountName || acc.platformUid || `账号#${acc.accountId}`
}

const getAccountStatusLabel = (status?: string | null) => {
  const normalized = (status || '').toLowerCase()
  return (
    {
      authorized: '已授权',
      active: '正常',
      expired: '已过期',
      need_reauth: '需重新授权',
      needs_rebind: '需重新绑定',
      account_mismatch: '账号已切换',
      invalid: '无效',
      revoked: '已解绑',
      disabled: '已停用',
      risk: '异常',
    } as Record<string, string>
  )[normalized] || '未知'
}

const getSessionStatusLabel = (status?: string | null) => {
  const normalized = (status || '').toLowerCase()
  return (
    {
      active: '正常',
      expired: '已过期',
      invalid: '无效',
      revoked: '已解绑',
      account_mismatch: '账号已切换',
    } as Record<string, string>
  )[normalized] || '未同步'
}

const getBridgePlatformCode = (platformCode?: string | null) => {
  const key = (platformCode || '').toLowerCase()
  return (
    {
      douyin: 'dy',
      xiaohongshu: 'xhs',
      bilibili: 'bili',
      weibo: 'wb',
      kuaishou: 'ks',
    } as Record<string, string>
  )[key] || key
}

const isBridgePlatformSupported = () => {
  return ['dy', 'xhs', 'ks', 'bili', 'wb', 'tieba', 'zhihu'].includes(getBridgePlatformCode(bridgePlatformCode.value))
}

const getBridgePlatformInfo = (client: CookieBridgeClientInfo) => {
  const bridgeCode = getBridgePlatformCode(bridgePlatformCode.value)
  return client.platforms?.[bridgeCode] || {}
}

const hasBridgeCookies = (client: CookieBridgeClientInfo) => {
  return Boolean(getBridgePlatformInfo(client).has_cookies)
}

const getBridgeClientName = (client: CookieBridgeClientInfo) => {
  const bridgeCode = getBridgePlatformCode(bridgePlatformCode.value)
  const nickname = client.nicknames?.[bridgeCode]
  if (nickname) return nickname
  if (hasBridgeCookies(client)) return `${currentBridgePlatformName.value}已登录账号`
  return `${currentBridgePlatformName.value}浏览器客户端`
}

const formatBridgeClientId = (clientId?: string) => {
  if (!clientId) return '-'
  if (clientId.length <= 12) return clientId
  return `${clientId.slice(0, 8)}...${clientId.slice(-6)}`
}

const getBridgePlatformLabel = (client: CookieBridgeClientInfo) => {
  if (!isBridgePlatformSupported()) return `CookieBridge 暂不支持 ${currentBridgePlatformName.value}`
  const info = getBridgePlatformInfo(client)
  if (info.has_cookies) return `${currentBridgePlatformName.value} Cookie 已就绪`
  return `未检测到 ${currentBridgePlatformName.value} Cookie，请先登录`
}

const openPlatformLogin = () => {
  const bridgeCode = getBridgePlatformCode(bridgePlatformCode.value)
  const urlMap: Record<string, string> = {
    dy: 'https://www.douyin.com',
    xhs: 'https://www.xiaohongshu.com',
    ks: 'https://www.kuaishou.com',
    bili: 'https://www.bilibili.com',
    wb: 'https://weibo.com',
    tieba: 'https://tieba.baidu.com',
    zhihu: 'https://www.zhihu.com',
  }
  const url = urlMap[bridgeCode]
  if (!url) {
    bridgeError.value = `暂未配置 ${currentBridgePlatformName.value} 登录地址`
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

const formatBridgeTime = (value?: number | null) => {
  if (!value) return '-'
  const date = new Date(value * 1000)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
}

const getIconByCode = (code: string) => defaultPlatforms.find((p) => p.code === code)?.icon || 'key'

const getEventLabel = (type: string) =>
  ({
    bind: '新建绑定',
    refresh: '手动同步',
    expire: '自动过期',
    revoke: '解除绑定',
  })[type] || type

const getEventColor = (type: string) =>
  ({
    bind: 'bg-green-100 text-green-700',
    refresh: 'bg-blue-100 text-blue-700',
    expire: 'bg-orange-100 text-orange-700',
    revoke: 'bg-red-100 text-red-700',
  })[type] || 'bg-gray-100 text-gray-700'

const getAccountStatusColor = (status: string) => {
  const normalized = (status || '').toLowerCase()
  if (normalized === 'authorized' || normalized === 'active') return 'bg-green-100 text-green-700'
  if (normalized === 'expired' || normalized === 'need_reauth' || normalized === 'needs_rebind') return 'bg-orange-100 text-orange-700'
  if (normalized === 'risk' || normalized === 'revoked' || normalized === 'disabled' || normalized === 'account_mismatch' || normalized === 'invalid') return 'bg-red-100 text-red-700'
  return 'bg-gray-100 text-gray-700'
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  if (Number.isNaN(date.getTime())) return dateStr
  return date.toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
}

watch(activeTab, async (val) => {
  if (val === 'history') await fetchHistory()
})

onMounted(async () => {
  await fetchAccounts()
})

</script>

<style scoped>
.shadow-soft {
  box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
}

.animate-in {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
