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
  start: (aids: string[], path: string, opts: DlOptions) =>
    api.post('/download', { aids, path, ...opts }).then(r => r.data),
  progress: (taskId: string) => api.get('/download/progress', { params: { task_id: taskId } }).then(r => r.data),
}

export const fsApi = {
  browse: (path: string) => api.get('/fs/browse', { params: { path } }).then(r => r.data),
  default: () => api.get('/fs/default').then(r => r.data),
}
