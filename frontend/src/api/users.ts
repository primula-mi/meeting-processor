import api from './client'

export interface User {
  id: number
  yandex_id: string | null
  bitrix24_id: string | null
  email: string | null
  name: string | null
  system_prompt: string
  llm_provider: string | null
  llm_model: string | null
  transcription_provider: string | null
  created_at: string
}

export interface ModelInfo {
  id: string
  name: string
}

export interface ProviderInfo {
  name: string
  models: ModelInfo[]
  available?: boolean
}

export interface AvailableModels {
  default_provider: string
  providers: Record<string, ProviderInfo>
}

export interface TranscriptionProviderInfo {
  id: string
  name: string
  description: string
  available: boolean
  has_diarization: boolean
}

export interface AvailableTranscriptionProviders {
  default_provider: string
  providers: TranscriptionProviderInfo[]
}

export async function getMe(): Promise<User> {
  const { data } = await api.get('/users/me')
  return data
}

export async function updateSystemPrompt(system_prompt: string): Promise<User> {
  const { data } = await api.put('/users/me/system-prompt', { system_prompt })
  return data
}

export async function resetSystemPrompt(): Promise<User> {
  const { data } = await api.post('/users/me/system-prompt/reset')
  return data
}

export async function updateLLMSettings(llm_provider: string, llm_model: string): Promise<User> {
  const { data } = await api.put('/users/me/llm-settings', { llm_provider, llm_model })
  return data
}

export async function getAvailableModels(): Promise<AvailableModels> {
  const { data } = await api.get('/users/me/available-models')
  return data
}

export async function updateTranscriptionSettings(transcription_provider: string): Promise<User> {
  const { data } = await api.put('/users/me/transcription-settings', { transcription_provider })
  return data
}

export async function getAvailableTranscriptionProviders(): Promise<AvailableTranscriptionProviders> {
  const { data } = await api.get('/users/me/available-transcription-providers')
  return data
}
