<template>
  <section class="h-full overflow-auto bg-[#f5f7fb] px-6 py-6">
    <div class="mx-auto max-w-[1280px]">
      <div class="mb-6">
        <div v-if="breadcrumb" class="text-sm text-slate-400">{{ breadcrumb }}</div>
        <h1 class="mt-1 text-3xl font-semibold text-slate-900">{{ title }}</h1>
        <p class="mt-2 text-sm text-slate-500">{{ description }}</p>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div class="grid gap-4 md:grid-cols-3">
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-5">
            <div class="text-sm font-medium text-slate-400">当前状态</div>
            <div class="mt-3 text-lg font-semibold text-slate-900">入口已保留</div>
            <div class="mt-2 text-sm text-slate-500">导航、路由和页面壳已经接好。</div>
          </div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-5">
            <div class="text-sm font-medium text-slate-400">下一步</div>
            <div class="mt-3 text-lg font-semibold text-slate-900">等待业务页落地</div>
            <div class="mt-2 text-sm text-slate-500">后续可以直接替换成正式页面实现。</div>
          </div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-5">
            <div class="text-sm font-medium text-slate-400">路由状态</div>
            <div class="mt-3 text-lg font-semibold text-slate-900">可正常跳转</div>
            <div class="mt-2 text-sm text-slate-500">当前用于信息架构占位。</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    breadcrumb?: string
    description?: string
  }>(),
  {
    description: '该模块暂时保留当前入口，后续再接正式功能页面。',
  },
)
</script>
