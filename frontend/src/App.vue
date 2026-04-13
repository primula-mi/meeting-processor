<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'

const auth = useAuthStore()

onMounted(async () => {
  if (auth.isAuthenticated) {
    await auth.fetchUser()
  }
})
</script>

<template>
  <AppLayout>
    <RouterView />
  </AppLayout>
</template>
