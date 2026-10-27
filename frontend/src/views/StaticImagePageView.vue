<template>
  <section class="h-full overflow-auto bg-[#f5f7fb] px-6 py-6">
    <div class="mx-auto max-w-[1440px]">
      <div class="mb-4">
        <div v-if="breadcrumb" class="text-sm text-slate-400">{{ breadcrumb }}</div>
        <h1 class="mt-1 text-3xl font-semibold text-slate-900">{{ title }}</h1>
      </div>

      <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <img :src="imageSrc" :alt="title" class="block w-full h-auto" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  breadcrumb?: string
  imageSrc: string
}>()
</script>
