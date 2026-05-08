import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// Attach CSRF token from cookie on mutation requests
api.interceptors.request.use((config) => {
  if (config.method !== 'get') {
    const csrfCookie = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrftoken='))
    if (csrfCookie) {
      config.headers['X-CSRFToken'] = csrfCookie.split('=')[1]
    }
  }
  return config
})

export type { PaginatedResponse } from './resources'
export * from './resources'