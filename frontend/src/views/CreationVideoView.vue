<template>
  <div class="h-full w-full relative group/host">
    <LegacyPageHost
      :html="page.html"
      :scope="page.scope"
      :title="page.title"
      @ready="handleReady"
    />
  </div>
</template>

<script setup lang="ts">
import LegacyPageHost from '../components/LegacyPageHost.vue'
import { legacyPagesByKey } from '../lib/legacy-pages'

const page = legacyPagesByKey['creation-video']

function handleReady(scopeApi: Record<string, (...args: unknown[]) => unknown>) {
  scopeApi.switchMode?.('video')
  scopeApi.switchVideoView?.('script')
}
</script>
