import api from './client'

export interface MeetingList {
  id: number
  title: string
  input_type: 'audio' | 'video' | 'text'
  status: 'pending' | 'transcribing' | 'processing' | 'done' | 'failed'
  created_at: string
}

export interface TaskItem {
  task: string
  assigner: string
  assignee: string
  deadline: string
}

export interface MeetingResult {
  summary: string
  tasks: TaskItem[]
  decisions: string[]
}

export interface MeetingDetail extends MeetingList {
  original_file_url: string | null
  transcript: string | null
  result_json: MeetingResult | null
  error_message: string | null
}

export async function getMeetings(): Promise<MeetingList[]> {
  const { data } = await api.get('/meetings/')
  return data
}

export async function getMeeting(id: number): Promise<MeetingDetail> {
  const { data } = await api.get(`/meetings/${id}`)
  return data
}

export async function uploadMeeting(title: string, file: File): Promise<MeetingDetail> {
  const formData = new FormData()
  formData.append('title', title)
  formData.append('file', file)
  const { data } = await api.post('/meetings/upload', formData)
  return data
}

export async function createTextMeeting(title: string, text: string): Promise<MeetingDetail> {
  const formData = new FormData()
  formData.append('title', title)
  formData.append('text', text)
  const { data } = await api.post('/meetings/text', formData)
  return data
}

export async function deleteMeeting(id: number): Promise<void> {
  await api.delete(`/meetings/${id}`)
}
