import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const loginApi = {
  check: () => api.get('/login/check').then(r => r.data),
  qrcode: () => api.post('/login/qrcode').then(r => r.data),
  status: (key: string) => api.get('/login/status', { params: { qrcode_key: key } }).then(r => r.data),
}

export const parseApi = {
  parse: (url: string) => api.post('/parse', { url }).then(r => r.data),
  parseCollection: (url: string) => api.post('/parse/collection', { url }).then(r => r.data),
}

export interface DlOptions {
  auto_mkdir: boolean
  mkdir_up: boolean
  mkdir_collection: boolean
  up_name: string
  collection_title: string
}

export const downloadApi = {
  start: (aids: string[], path: string, opts: DlOptions, title = '') =>
    api.post('/download', { aids, path, title, ...opts }).then(r => r.data),
  progress: (taskId: string) => api.get('/download/progress', { params: { task_id: taskId } }).then(r => r.data),
  pause: (taskId: string) => api.post('/download/pause', { task_id: taskId }).then(r => r.data),
  resume: (taskId: string) => api.post('/download/resume', { task_id: taskId }).then(r => r.data),
  remove: (taskId: string) => api.post('/download/delete', { task_id: taskId }).then(r => r.data),
  tasks: () => api.get('/download/tasks').then(r => r.data as { ok: boolean; data: DlTask[] }),
  settings: () => api.get('/download/settings').then(r => r.data as { ok: boolean; data: DlSettings }),
  putSettings: (patch: Partial<DlSettings>) => api.put('/download/settings', patch).then(r => r.data),
}

export interface DlTask {
  task_id: string
  title: string
  path: string
  status: 'queued' | 'running' | 'paused' | 'done'
  total: number
  done: number
  success: number
  failed: { aid: string; error: string }[]
  current: string
  created_at: number
  updated_at: number
}

export interface DlSettings {
  max_parallel: number
  auto_resume: boolean
}

export const fsApi = {
  browse: (path: string) => api.get('/fs/browse', { params: { path } }).then(r => r.data),
  default: () => api.get('/fs/default').then(r => r.data),
}

export interface UpdateInfo {
  current: string
  latest?: string
  has_update?: boolean
  notes?: string
  page_url: string
  mode: 'auto' | 'manual' | 'dev'
  channel?: string
  asset_name?: string
  asset_size?: number
  error?: string
}

export const updateApi = {
  check: (force = false, proxy = '') =>
    api.get('/update/check', { params: { force, proxy: proxy || undefined } }).then(r => r.data as UpdateInfo),
  apply: (proxy = '') => api.post('/update/apply', { proxy }).then(r => r.data),
  progress: () => api.get('/update/progress').then(r => r.data as { stage: string; percent: number; error: string; version: string; channel: string }),
  health: () => api.get('/health', { timeout: 3000 }).then(r => r.data),
}
