<template>
  <div ref="root" class="legacy-page-host"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { renderLegacyFragment } from '../lib/legacy-dom'

const props = defineProps<{
  html: string
  scope: string
  title?: string
  isolateIds?: boolean
}>()

const emit = defineEmits<{
  ready: [scopeApi: Record<string, (...args: unknown[]) => unknown>]
}>()

const root = ref<HTMLElement | null>(null)
let cleanup = () => {}

onMounted(() => {
  if (!root.value) {
    return
  }

  const result = renderLegacyFragment({
    container: root.value,
    html: props.html,
    scope: props.scope,
    isolateIds: props.isolateIds ?? false,
    executeScripts: true,
  })

  document.title = props.title ?? result.title
  cleanup = result.cleanup
  emit('ready', result.scopeApi)
})

onBeforeUnmount(() => {
  cleanup()
})
</script>

<style scoped>
.legacy-page-host {
  width: 100%;
  min-height: 100%;
  height: 100%;
}
</style>
