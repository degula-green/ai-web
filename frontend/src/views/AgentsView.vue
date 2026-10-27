<template>
  <LegacyPageHost
    :html="page.html"
    :scope="page.scope"
    :title="page.title"
    @ready="handleReady"
  />
</template>

<script setup lang="ts">
import LegacyPageHost from '../components/LegacyPageHost.vue'
import { legacyPagesByKey } from '../lib/legacy-pages'

const page = legacyPagesByKey.agents

function handleReady(scopeApi: Record<string, (...args: unknown[]) => unknown>) {
  scopeApi.selectAgent?.('copywriter')
}
</script>
