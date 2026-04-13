<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api/client'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const error = ref('')

async function loginWithBitrix24() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/auth/login')
    window.location.href = data.url
  } catch (e) {
    error.value = 'Не удалось получить ссылку для входа'
    loading.value = false
  }
}

onMounted(async () => {
  // Handle OAuth callback: ?code=... or ?access_token=...
  const code = route.query.code as string | undefined
  const token = route.query.access_token as string | undefined

  if (token) {
    auth.setToken(token)
    await auth.fetchUser()
    router.replace('/')
    return
  }

  if (code) {
    loading.value = true
    try {
      const { data } = await api.get('/auth/callback', { params: { code } })
      auth.setToken(data.access_token)
      await auth.fetchUser()
      router.replace('/')
    } catch {
      error.value = 'Ошибка авторизации'
    } finally {
      loading.value = false
    }
    return
  }

  if (auth.isAuthenticated) {
    router.replace('/')
  }
})
</script>

<template>
  <div class="flex min-h-[80vh] items-center justify-center">
    <div class="w-full max-w-md rounded-lg border border-border bg-card p-8 shadow-sm">
      <h1 class="mb-2 text-2xl font-semibold text-foreground">
        Meeting Processor
      </h1>
      <p class="mb-6 text-sm text-muted-foreground">
        Автоматическая обработка записей совещаний
      </p>
      <button
        @click="loginWithBitrix24"
        :disabled="loading"
        class="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
      >
        {{ loading ? 'Загрузка…' : 'Войти через Bitrix24' }}
      </button>
      <p v-if="error" class="mt-4 text-sm text-destructive">{{ error }}</p>
    </div>
  </div>
</template>
