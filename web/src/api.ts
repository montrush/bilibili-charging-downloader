import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const loginApi = {
  check: () => api.get('/login/check').then(r => r.data),
  qrcode: () => api.post('/login/qrcode').then(r => r.data),
  status: (key: string) => api.get('/login/status', { params: { qrcode_key: key } }).then(r => r.data),
}

export const parseApi = {
  parse: (url: string) => api.post('/parse', { url }).then(r => r.data),
}

export const downloadApi = {
  start: (aids: string[], path: string) => api.post('/download', { aids, path }).then(r => r.data),
  progress: (taskId: string) => api.get('/download/progress', { params: { task_id: taskId } }).then(r => r.data),
}
