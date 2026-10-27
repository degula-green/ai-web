<script setup lang="ts">
defineProps<{
  loading?: boolean
}>()

defineEmits<{
  (e: 'push'): void
}>()
</script>
