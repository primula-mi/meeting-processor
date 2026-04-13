<script setup lang="ts">
import { ref } from 'vue'
import { uploadMeeting, createTextMeeting } from '@/api/meetings'
import { X, Upload } from 'lucide-vue-next'

const emit = defineEmits<{
  close: []
  uploaded: []
}>()

const mode = ref<'file' | 'text'>('file')
const title = ref('')
const text = ref('')
const file = ref<File | null>(null)
const uploading = ref(false)
const error = ref('')

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    file.value = target.files[0]
    if (!title.value) {
      title.value = target.files[0].name.replace(/\.[^.]+$/, '')
    }
  }
}

async function submit() {
  if (!title.value.trim()) {
    error.value = 'Введите название совещания'
    return
  }

  uploading.value = true
  error.value = ''
  try {
    if (mode.value === 'file') {
      if (!file.value) {
        error.value = 'Выберите файл'
        uploading.value = false
        return
      }
      await uploadMeeting(title.value, file.value)
    } else {
      if (!text.value.trim()) {
        error.value = 'Введите текст'
        uploading.value = false
        return
      }
      await createTextMeeting(title.value, text.value)
    }
    emit('uploaded')
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    error.value = err.response?.data?.detail || 'Ошибка загрузки'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="emit('close')">
    <div class="w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-lg">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold">Новое совещание</h2>
        <button @click="emit('close')" class="rounded-md p-1 text-muted-foreground hover:bg-accent">
          <X class="h-4 w-4" />
        </button>
      </div>

      <div class="mb-4 flex gap-2 rounded-md bg-muted p-1">
        <button
          @click="mode = 'file'"
          class="flex-1 rounded px-3 py-1.5 text-sm font-medium transition-colors"
          :class="mode === 'file' ? 'bg-background shadow-sm' : 'text-muted-foreground'"
        >
          Файл
        </button>
        <button
          @click="mode = 'text'"
          class="flex-1 rounded px-3 py-1.5 text-sm font-medium transition-colors"
          :class="mode === 'text' ? 'bg-background shadow-sm' : 'text-muted-foreground'"
        >
          Текст
        </button>
      </div>

      <div class="mb-4">
        <label class="mb-1 block text-sm font-medium">Название</label>
        <input
          v-model="title"
          type="text"
          class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="Совещание 01.04.2026"
        />
      </div>

      <div v-if="mode === 'file'" class="mb-4">
        <label class="mb-1 block text-sm font-medium">Файл</label>
        <label class="flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed border-border p-6 hover:bg-accent transition-colors">
          <Upload class="mb-2 h-6 w-6 text-muted-foreground" />
          <span class="text-sm text-muted-foreground">
            {{ file ? file.name : 'Нажмите, чтобы выбрать файл' }}
          </span>
          <span class="mt-1 text-xs text-muted-foreground">
            .mp3, .wav, .ogg, .m4a, .mp4, .mkv, .webm, .txt, .docx
          </span>
          <input
            type="file"
            class="hidden"
            accept=".mp3,.wav,.ogg,.m4a,.mp4,.mkv,.webm,.txt,.docx"
            @change="onFileChange"
          />
        </label>
      </div>

      <div v-else class="mb-4">
        <label class="mb-1 block text-sm font-medium">Текст транскрипта</label>
        <textarea
          v-model="text"
          rows="8"
          class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
          placeholder="Вставьте текст транскрипта совещания…"
        />
      </div>

      <p v-if="error" class="mb-3 text-sm text-destructive">{{ error }}</p>

      <div class="flex justify-end gap-2">
        <button
          @click="emit('close')"
          class="rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent transition-colors"
        >
          Отмена
        </button>
        <button
          @click="submit"
          :disabled="uploading"
          class="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
        >
          {{ uploading ? 'Загрузка…' : 'Загрузить' }}
        </button>
      </div>
    </div>
  </div>
</template>
