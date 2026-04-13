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

// Toggle this to show the Bitrix24 login button once a paid Bitrix24 plan is
// available and BITRIX24_* env vars are configured on the backend.
const BITRIX24_ENABLED = false

async function loginWith(provider: 'yandex' | 'bitrix24') {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/auth/${provider}/login`)
    window.location.href = data.url
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    error.value = err.response?.data?.detail || 'Не удалось получить ссылку для входа'
    loading.value = false
  }
}

onMounted(async () => {
  // Backend redirects here after OAuth with ?access_token=... or ?error=...
  const token = route.query.access_token as string | undefined
  const errMsg = route.query.error as string | undefined

  if (errMsg) {
    error.value = errMsg
    // Clean the URL
    router.replace({ name: 'login' })
    return
  }

  if (token) {
    auth.setToken(token)
    await auth.fetchUser()
    router.replace('/')
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
        @click="loginWith('yandex')"
        :disabled="loading"
        class="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
      >
        {{ loading ? 'Загрузка…' : 'Войти через Яндекс' }}
      </button>

      <button
        v-if="BITRIX24_ENABLED"
        @click="loginWith('bitrix24')"
        :disabled="loading"
        class="mt-2 w-full rounded-md border border-border px-4 py-2.5 text-sm font-medium hover:bg-accent disabled:opacity-60 transition-colors"
      >
        Войти через Bitrix24
      </button>

      <p class="mt-3 text-center text-xs text-muted-foreground">
        Доступ только для сотрудников компании
      </p>

      <p v-if="error" class="mt-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
        {{ error }}
      </p>
    </div>
  </div>
</template>
