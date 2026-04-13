<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMeetings, deleteMeeting, type MeetingList } from '@/api/meetings'
import { Plus, Trash2, FileAudio, FileVideo, FileText, Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-vue-next'
import UploadDialog from '@/components/UploadDialog.vue'

const router = useRouter()
const meetings = ref<MeetingList[]>([])
const loading = ref(false)
const showUpload = ref(false)
let pollInterval: ReturnType<typeof setInterval> | null = null

async function load() {
  try {
    meetings.value = await getMeetings()
  } catch (e) {
    console.error(e)
  }
}

async function handleDelete(id: number, event: Event) {
  event.stopPropagation()
  if (!confirm('Удалить совещание?')) return
  await deleteMeeting(id)
  await load()
}

function openMeeting(id: number) {
  router.push(`/meetings/${id}`)
}

function onUploaded() {
  showUpload.value = false
  load()
}

const statusLabels: Record<string, string> = {
  pending: 'Ожидание',
  transcribing: 'Транскрибация',
  processing: 'Анализ',
  done: 'Готово',
  failed: 'Ошибка',
}

const inputTypeIcons: Record<string, unknown> = {
  audio: FileAudio,
  video: FileVideo,
  text: FileText,
}

const statusIcons: Record<string, unknown> = {
  pending: Clock,
  transcribing: Loader2,
  processing: Loader2,
  done: CheckCircle2,
  failed: XCircle,
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('ru-RU')
}

onMounted(() => {
  load()
  pollInterval = setInterval(() => {
    const hasInProgress = meetings.value.some(
      (m) => m.status === 'pending' || m.status === 'transcribing' || m.status === 'processing'
    )
    if (hasInProgress) load()
  }, 5000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div>
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-semibold">Совещания</h1>
      <button
        @click="showUpload = true"
        class="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
      >
        <Plus class="h-4 w-4" />
        Новое совещание
      </button>
    </div>

    <div v-if="meetings.length === 0 && !loading" class="rounded-lg border border-dashed border-border p-12 text-center">
      <p class="text-muted-foreground">У вас пока нет совещаний</p>
      <button
        @click="showUpload = true"
        class="mt-4 text-sm text-primary hover:underline"
      >
        Загрузить первое
      </button>
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="meeting in meetings"
        :key="meeting.id"
        @click="openMeeting(meeting.id)"
        class="group flex cursor-pointer items-center justify-between rounded-lg border border-border bg-card p-4 hover:bg-accent transition-colors"
      >
        <div class="flex items-center gap-4 min-w-0 flex-1">
          <component
            :is="inputTypeIcons[meeting.input_type]"
            class="h-5 w-5 text-muted-foreground flex-shrink-0"
          />
          <div class="min-w-0 flex-1">
            <div class="truncate font-medium">{{ meeting.title }}</div>
            <div class="text-xs text-muted-foreground">{{ formatDate(meeting.created_at) }}</div>
          </div>
        </div>
        <div class="flex items-center gap-4 flex-shrink-0">
          <div
            class="flex items-center gap-1.5 text-xs"
            :class="{
              'text-muted-foreground': meeting.status === 'pending',
              'text-blue-500': meeting.status === 'transcribing' || meeting.status === 'processing',
              'text-green-600 dark:text-green-500': meeting.status === 'done',
              'text-destructive': meeting.status === 'failed',
            }"
          >
            <component
              :is="statusIcons[meeting.status]"
              class="h-4 w-4"
              :class="{ 'animate-spin': meeting.status === 'transcribing' || meeting.status === 'processing' }"
            />
            {{ statusLabels[meeting.status] }}
          </div>
          <button
            @click="handleDelete(meeting.id, $event)"
            class="rounded-md p-1.5 text-muted-foreground opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive transition-all"
          >
            <Trash2 class="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>

    <UploadDialog v-if="showUpload" @close="showUpload = false" @uploaded="onUploaded" />
  </div>
</template>
