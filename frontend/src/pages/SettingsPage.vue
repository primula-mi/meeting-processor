<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  updateSystemPrompt,
  resetSystemPrompt,
  updateLLMSettings,
  getAvailableModels,
  updateTranscriptionSettings,
  getAvailableTranscriptionProviders,
  type AvailableModels,
  type AvailableTranscriptionProviders,
} from '@/api/users'
import { RotateCcw, Save, Bot, Cpu, Mic } from 'lucide-vue-next'

const auth = useAuthStore()

// System prompt
const prompt = ref('')
const savingPrompt = ref(false)
const savedPrompt = ref(false)

// LLM settings
const availableModels = ref<AvailableModels | null>(null)
const selectedProvider = ref('')
const selectedModel = ref('')
const savingLLM = ref(false)
const savedLLM = ref(false)

// Transcription settings
const transcriptionProviders = ref<AvailableTranscriptionProviders | null>(null)
const selectedTranscription = ref('')
const savingTranscription = ref(false)
const savedTranscription = ref(false)

const currentProviderModels = computed(() => {
  if (!availableModels.value || !selectedProvider.value) return []
  return availableModels.value.providers[selectedProvider.value]?.models || []
})

const providerEntries = computed(() => {
  if (!availableModels.value) return []
  return Object.entries(availableModels.value.providers)
})

const selectedTranscriptionInfo = computed(() => {
  if (!transcriptionProviders.value) return null
  return transcriptionProviders.value.providers.find((p) => p.id === selectedTranscription.value)
})

watch(selectedProvider, () => {
  const models = currentProviderModels.value
  if (models.length > 0 && !models.find((m) => m.id === selectedModel.value)) {
    selectedModel.value = models[0].id
  }
})

onMounted(async () => {
  if (!auth.user) await auth.fetchUser()
  if (auth.user) {
    prompt.value = auth.user.system_prompt
  }

  // Load LLM models
  try {
    availableModels.value = await getAvailableModels()
    if (auth.user) {
      selectedProvider.value =
        auth.user.llm_provider || availableModels.value.default_provider
      selectedModel.value = auth.user.llm_model || ''
    }
    if (!selectedModel.value && currentProviderModels.value.length > 0) {
      selectedModel.value = currentProviderModels.value[0].id
    }
  } catch {
    // LLM models endpoint unavailable
  }

  // Load transcription providers
  try {
    transcriptionProviders.value = await getAvailableTranscriptionProviders()
    if (auth.user) {
      selectedTranscription.value =
        auth.user.transcription_provider || transcriptionProviders.value.default_provider
    }
  } catch {
    // Transcription providers endpoint unavailable
  }
})

async function savePrompt() {
  savingPrompt.value = true
  savedPrompt.value = false
  try {
    const user = await updateSystemPrompt(prompt.value)
    auth.user = user
    savedPrompt.value = true
    setTimeout(() => { savedPrompt.value = false }, 2000)
  } finally {
    savingPrompt.value = false
  }
}

async function resetPrompt() {
  if (!confirm('Сбросить промпт до системного?')) return
  savingPrompt.value = true
  try {
    const user = await resetSystemPrompt()
    auth.user = user
    prompt.value = user.system_prompt
  } finally {
    savingPrompt.value = false
  }
}

async function saveLLMSettings() {
  savingLLM.value = true
  savedLLM.value = false
  try {
    const user = await updateLLMSettings(selectedProvider.value, selectedModel.value)
    auth.user = user
    savedLLM.value = true
    setTimeout(() => { savedLLM.value = false }, 2000)
  } finally {
    savingLLM.value = false
  }
}

async function saveTranscriptionSettings() {
  savingTranscription.value = true
  savedTranscription.value = false
  try {
    const user = await updateTranscriptionSettings(selectedTranscription.value)
    auth.user = user
    savedTranscription.value = true
    setTimeout(() => { savedTranscription.value = false }, 2000)
  } finally {
    savingTranscription.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-semibold">Настройки</h1>

    <!-- LLM Provider & Model -->
    <div v-if="availableModels" class="mb-6 rounded-lg border border-border bg-card p-6">
      <h2 class="mb-1 flex items-center gap-2 text-lg font-semibold">
        <Bot class="h-5 w-5" />
        Модель LLM
      </h2>
      <p class="mb-4 text-sm text-muted-foreground">
        Выберите провайдер и модель для анализа транскриптов.
      </p>

      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-sm font-medium">Провайдер</label>
          <div class="flex gap-2">
            <button
              v-for="[key, info] in providerEntries"
              :key="key"
              @click="selectedProvider = key"
              class="flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-colors"
              :class="
                selectedProvider === key
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border hover:bg-accent'
              "
            >
              <span class="flex items-center justify-center gap-1.5">
                <Cpu v-if="key === 'ollama'" class="h-4 w-4" />
                {{ info.name }}
              </span>
            </button>
          </div>
          <p
            v-if="selectedProvider === 'ollama' && availableModels.providers.ollama && !availableModels.providers.ollama.available"
            class="mt-2 text-xs text-destructive"
          >
            Ollama недоступен. Убедитесь, что сервер запущен.
          </p>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium">Модель</label>
          <select
            v-if="currentProviderModels.length > 0"
            v-model="selectedModel"
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option v-for="m in currentProviderModels" :key="m.id" :value="m.id">
              {{ m.name }}
            </option>
          </select>
          <input
            v-else
            v-model="selectedModel"
            type="text"
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            :placeholder="selectedProvider === 'ollama' ? 'llama3' : 'gpt-4o'"
          />
        </div>
      </div>

      <div class="mt-4 flex items-center justify-end gap-3">
        <span v-if="savedLLM" class="text-sm text-green-600 dark:text-green-500">Сохранено</span>
        <button
          @click="saveLLMSettings"
          :disabled="savingLLM"
          class="flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
        >
          <Save class="h-4 w-4" />
          {{ savingLLM ? 'Сохранение…' : 'Сохранить' }}
        </button>
      </div>
    </div>

    <!-- Transcription Provider -->
    <div v-if="transcriptionProviders" class="mb-6 rounded-lg border border-border bg-card p-6">
      <h2 class="mb-1 flex items-center gap-2 text-lg font-semibold">
        <Mic class="h-5 w-5" />
        Транскрибация
      </h2>
      <p class="mb-4 text-sm text-muted-foreground">
        Выберите сервис для расшифровки аудио- и видеозаписей.
      </p>

      <div class="grid gap-3 sm:grid-cols-3">
        <button
          v-for="p in transcriptionProviders.providers"
          :key="p.id"
          @click="selectedTranscription = p.id"
          :disabled="!p.available"
          class="rounded-md border p-4 text-left transition-colors"
          :class="[
            selectedTranscription === p.id
              ? 'border-primary bg-primary/5 ring-1 ring-primary'
              : p.available
                ? 'border-border hover:bg-accent'
                : 'border-border opacity-50 cursor-not-allowed',
          ]"
        >
          <div class="mb-1 text-sm font-medium">{{ p.name }}</div>
          <div class="text-xs text-muted-foreground">{{ p.description }}</div>
          <div class="mt-2 flex items-center gap-2">
            <span
              v-if="p.has_diarization"
              class="inline-block rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400"
            >
              спикеры
            </span>
            <span
              v-if="!p.available"
              class="inline-block rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
            >
              не настроен
            </span>
          </div>
        </button>
      </div>

      <p v-if="selectedTranscriptionInfo && !selectedTranscriptionInfo.has_diarization" class="mt-3 text-xs text-muted-foreground">
        Выбранный провайдер не поддерживает разделение по спикерам — транскрипт будет без ролей.
      </p>

      <div class="mt-4 flex items-center justify-end gap-3">
        <span v-if="savedTranscription" class="text-sm text-green-600 dark:text-green-500">Сохранено</span>
        <button
          @click="saveTranscriptionSettings"
          :disabled="savingTranscription"
          class="flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
        >
          <Save class="h-4 w-4" />
          {{ savingTranscription ? 'Сохранение…' : 'Сохранить' }}
        </button>
      </div>
    </div>

    <!-- System Prompt -->
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
          @click="resetPrompt"
          :disabled="savingPrompt"
          class="flex items-center gap-1.5 rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent transition-colors disabled:opacity-60"
        >
          <RotateCcw class="h-4 w-4" />
          Сбросить до системного
        </button>
        <div class="flex items-center gap-3">
          <span v-if="savedPrompt" class="text-sm text-green-600 dark:text-green-500">Сохранено</span>
          <button
            @click="savePrompt"
            :disabled="savingPrompt"
            class="flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
          >
            <Save class="h-4 w-4" />
            {{ savingPrompt ? 'Сохранение…' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
