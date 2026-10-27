<template>
  <LegacyPageHost :html="page.html" :scope="page.scope" :title="page.title" :isolate-ids="true" />
</template>

<script setup lang="ts">
import LegacyPageHost from '../components/LegacyPageHost.vue'
import { legacyPagesByKey } from '../lib/legacy-pages'

const page = legacyPagesByKey.distribution
</script>
