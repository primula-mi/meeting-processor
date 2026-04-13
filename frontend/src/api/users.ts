import api from './client'

export interface User {
  id: number
  yandex_id: string | null
  bitrix24_id: string | null
  email: string | null
  name: string | null
  system_prompt: string
  created_at: string
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
