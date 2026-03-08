import axios from 'axios'
import { API_BASE_URL } from './api'

const axiosInstance = axios.create({ baseURL: API_BASE_URL })

// Attach access token to every request
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401: silently refresh access token and retry; on full failure redirect to login
axiosInstance.interceptors.response.use(
  (response) => response,
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
