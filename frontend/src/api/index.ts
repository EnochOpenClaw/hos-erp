import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,  // send session cookies
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

export default api
