import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = false
let queue: Array<(token: string) => void> = []

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (!refresh) {
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }
      if (refreshing) {
        return new Promise((resolve) => {
          queue.push((token: string) => {
            original.headers.Authorization = `Bearer ${token}`
            resolve(api(original))
          })
        })
      }
      refreshing = true
      try {
        const { data } = await axios.post(`${API_URL}/auth/refresh/`, { refresh })
        localStorage.setItem('access_token', data.access)
        if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
        queue.forEach((cb) => cb(data.access))
        queue = []
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        localStorage.clear()
        window.location.href = '/login'
      } finally {
        refreshing = false
      }
    }
    return Promise.reject(error)
  }
)
