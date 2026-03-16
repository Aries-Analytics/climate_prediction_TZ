import axios from 'axios'
import { API_BASE_URL } from './api'

// Extend axios config type to carry cache sentinel and retry flag
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    _fromCache?: boolean
    _retry?: boolean
  }
}

// Simple in-memory GET cache (2-minute TTL) — prevents duplicate requests across dashboard navigation
const _responseCache = new Map<string, { data: unknown; ts: number }>()
const _CACHE_TTL_MS = 2 * 60 * 1000
const _NO_CACHE = ['/auth/', '/admin/']

function _cacheKey(config: { method?: string; url?: string; params?: unknown }): string | null {
  if (config.method?.toLowerCase() !== 'get') return null
  const url = config.url ?? ''
  if (_NO_CACHE.some(p => url.includes(p))) return null
  const params = config.params ? '?' + new URLSearchParams(config.params as Record<string, string>).toString() : ''
  return url + params
}

const axiosInstance = axios.create({ baseURL: API_BASE_URL })

// Attach access token to every request
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Serve from cache if fresh
  const key = _cacheKey(config)
  if (key) {
    const hit = _responseCache.get(key)
    if (hit) {
      if (Date.now() - hit.ts < _CACHE_TTL_MS) {
        config._fromCache = true
        config.adapter = () => Promise.resolve({
          data: hit.data,
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
          request: undefined,
        })
      } else {
        _responseCache.delete(key) // lazy-evict stale entry to prevent unbounded growth
      }
    }
  }
  return config
})

// On 401: silently refresh access token and retry; on full failure redirect to login
axiosInstance.interceptors.response.use(
  (response) => {
    const key = _cacheKey(response.config)
    if (key && response.status === 200 && !response.config._fromCache) {
      _responseCache.set(key, { data: response.data, ts: Date.now() })
    }
    return response
  },
  async (error) => {
    const originalRequest = error.config

    const isAuthEndpoint =
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/login')

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem('token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          return axiosInstance(originalRequest)
        } catch {
          // Refresh failed — fall through to full logout below
        }
      }

      // Full auth failure: clear tokens and redirect cleanly
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default axiosInstance
