<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getMeeting, type MeetingDetail } from '@/api/meetings'
import { ArrowLeft, Copy, Download, ChevronDown, ChevronUp, Loader2 } from 'lucide-vue-next'
import { marked } from 'marked'

const route = useRoute()
const router = useRouter()
const meeting = ref<MeetingDetail | null>(null)
const activeTab = ref<'summary' | 'tasks'>('summary')
const showTranscript = ref(false)
let pollInterval: ReturnType<typeof setInterval> | null = null

async function load() {
  const id = Number(route.params.id)
  try {
    meeting.value = await getMeeting(id)
  } catch {
    router.push('/')
  }
}

const isProcessing = computed(() => {
  const s = meeting.value?.status
  return s === 'pending' || s === 'transcribing' || s === 'processing'
})

const statusLabels: Record<string, string> = {
  pending: 'В очереди',
  transcribing: 'Идёт транскрибация',
  processing: 'Идёт анализ',
  done: 'Готово',
  failed: 'Ошибка',
}

const summaryHtml = computed(() => {
  if (!meeting.value?.result_json?.summary) return ''
  return marked.parse(meeting.value.result_json.summary) as string
})

async function copyResult() {
  if (!meeting.value?.result_json) return
  const text = JSON.stringify(meeting.value.result_json, null, 2)
  await navigator.clipboard.writeText(text)
}

function downloadJson() {
  if (!meeting.value?.result_json) return
  const blob = new Blob([JSON.stringify(meeting.value.result_json, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${meeting.value.title}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function downloadTxt() {
  if (!meeting.value?.result_json) return
  const r = meeting.value.result_json
  let txt = `# ${meeting.value.title}\n\n`
  txt += `## Выжимка\n${r.summary}\n\n`
  txt += `## Решения\n`
  r.decisions.forEach((d, i) => { txt += `${i + 1}. ${d}\n` })
  txt += `\n## Задачи\n`
  r.tasks.forEach((t, i) => {
    txt += `${i + 1}. ${t.task}\n`
    if (t.assignee) txt += `   Ответственный: ${t.assignee}\n`
    if (t.deadline) txt += `   Срок: ${t.deadline}\n`
  })
  const blob = new Blob([txt], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${meeting.value.title}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  load()
  pollInterval = setInterval(() => {
    if (isProcessing.value) load()
  }, 5000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div v-if="meeting">
    <button
      @click="router.push('/')"
      class="mb-4 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
    >
      <ArrowLeft class="h-4 w-4" />
      Назад
    </button>

    <h1 class="mb-2 text-2xl font-semibold">{{ meeting.title }}</h1>
    <p class="mb-6 text-sm text-muted-foreground">
      {{ new Date(meeting.created_at).toLocaleString('ru-RU') }}
    </p>

    <div v-if="isProcessing" class="rounded-lg border border-border bg-card p-12 text-center">
      <Loader2 class="mx-auto mb-3 h-8 w-8 animate-spin text-muted-foreground" />
      <p class="text-lg font-medium">{{ statusLabels[meeting.status] }}</p>
      <p class="mt-2 text-sm text-muted-foreground">
        Процесс может занять несколько минут
      </p>
    </div>

    <div v-else-if="meeting.status === 'failed'" class="rounded-lg border border-destructive/30 bg-destructive/5 p-6">
      <p class="font-medium text-destructive">Ошибка обработки</p>
      <p v-if="meeting.error_message" class="mt-2 text-sm text-muted-foreground">
        {{ meeting.error_message }}
      </p>
    </div>

    <div v-else-if="meeting.status === 'done' && meeting.result_json">
      <div class="mb-4 flex items-center justify-between">
        <div class="flex gap-1 rounded-md border border-border bg-card p-1">
          <button
            @click="activeTab = 'summary'"
            class="rounded px-4 py-1.5 text-sm font-medium transition-colors"
            :class="activeTab === 'summary' ? 'bg-accent' : 'text-muted-foreground hover:text-foreground'"
          >
            Выжимка и решения
          </button>
          <button
            @click="activeTab = 'tasks'"
            class="rounded px-4 py-1.5 text-sm font-medium transition-colors"
            :class="activeTab === 'tasks' ? 'bg-accent' : 'text-muted-foreground hover:text-foreground'"
          >
            Задачи ({{ meeting.result_json.tasks.length }})
          </button>
        </div>
        <div class="flex gap-2">
          <button
            @click="copyResult"
            class="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent transition-colors"
          >
            <Copy class="h-4 w-4" />
            Копировать
          </button>
          <button
            @click="downloadTxt"
            class="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent transition-colors"
          >
            <Download class="h-4 w-4" />
            .txt
          </button>
          <button
            @click="downloadJson"
            class="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-accent transition-colors"
          >
            <Download class="h-4 w-4" />
            .json
          </button>
        </div>
      </div>

      <div v-if="activeTab === 'summary'" class="space-y-6">
        <div class="rounded-lg border border-border bg-card p-6">
          <h2 class="mb-3 text-lg font-semibold">Выжимка</h2>
          <div class="prose prose-sm max-w-none dark:prose-invert" v-html="summaryHtml" />
        </div>
        <div v-if="meeting.result_json.decisions.length" class="rounded-lg border border-border bg-card p-6">
          <h2 class="mb-3 text-lg font-semibold">Принятые решения</h2>
          <ol class="list-decimal space-y-2 pl-5 text-sm">
            <li v-for="(d, i) in meeting.result_json.decisions" :key="i">{{ d }}</li>
          </ol>
        </div>
      </div>

      <div v-else-if="activeTab === 'tasks'" class="rounded-lg border border-border bg-card overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-muted/50">
            <tr>
              <th class="px-4 py-2 text-left font-medium">Задача</th>
              <th class="px-4 py-2 text-left font-medium">Ответственный</th>
              <th class="px-4 py-2 text-left font-medium">Срок</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(t, i) in meeting.result_json.tasks"
              :key="i"
              class="border-t border-border"
            >
              <td class="px-4 py-3">{{ t.task }}</td>
              <td class="px-4 py-3 text-muted-foreground">{{ t.assignee || '—' }}</td>
              <td class="px-4 py-3 text-muted-foreground">{{ t.deadline || '—' }}</td>
            </tr>
            <tr v-if="meeting.result_json.tasks.length === 0">
              <td colspan="3" class="px-4 py-6 text-center text-muted-foreground">
                Задачи не выявлены
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="meeting.transcript" class="mt-6 rounded-lg border border-border bg-card">
        <button
          @click="showTranscript = !showTranscript"
          class="flex w-full items-center justify-between p-4 text-left font-medium hover:bg-accent transition-colors"
        >
          <span>Исходный транскрипт</span>
          <ChevronDown v-if="!showTranscript" class="h-4 w-4" />
          <ChevronUp v-else class="h-4 w-4" />
        </button>
        <div v-if="showTranscript" class="border-t border-border p-4">
          <pre class="whitespace-pre-wrap text-sm text-muted-foreground">{{ meeting.transcript }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
