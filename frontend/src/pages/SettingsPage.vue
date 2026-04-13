<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { updateSystemPrompt, resetSystemPrompt } from '@/api/users'
import { RotateCcw, Save } from 'lucide-vue-next'

const auth = useAuthStore()
const prompt = ref('')
const saving = ref(false)
const saved = ref(false)

onMounted(async () => {
  if (!auth.user) await auth.fetchUser()
  if (auth.user) prompt.value = auth.user.system_prompt
})

async function save() {
  saving.value = true
  saved.value = false
  try {
    const user = await updateSystemPrompt(prompt.value)
    auth.user = user
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } finally {
    saving.value = false
  }
}

async function reset() {
  if (!confirm('Сбросить промпт до системного?')) return
  saving.value = true
  try {
    const user = await resetSystemPrompt()
    auth.user = user
    prompt.value = user.system_prompt
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-semibold">Настройки</h1>

    <div class="rounded-lg border border-border bg-card p-6">
      <h2 class="mb-1 text-lg font-semibold">Системный промпт</h2>
      <p class="mb-4 text-sm text-muted-foreground">
        Этот промпт используется при анализе транскрипта LLM. Отредактируйте его, чтобы настроить результат под себя.
      </p>
      <textarea
        v-model="prompt"
        rows="14"
        class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring resize-none"
      />
      <div class="mt-4 flex items-center justify-between">
        <button
          @click="reset"
          :disabled="saving"
          class="flex items-center gap-1.5 rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent transition-colors disabled:opacity-60"
        >
          <RotateCcw class="h-4 w-4" />
          Сбросить до системного
        </button>
        <div class="flex items-center gap-3">
          <span v-if="saved" class="text-sm text-green-600 dark:text-green-500">Сохранено</span>
          <button
            @click="save"
            :disabled="saving"
            class="flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
          >
            <Save class="h-4 w-4" />
            {{ saving ? 'Сохранение…' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
