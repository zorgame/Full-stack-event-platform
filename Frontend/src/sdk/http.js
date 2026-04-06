import axios from 'axios'
import { normalizeAxiosError } from './errors'

export class HttpClient {
  constructor(options = {}) {
    this._token = options.token ?? null
    this._axios = axios.create({
      baseURL: options.baseURL,
      timeout: options.timeout ?? 15000,
      headers: {
        ...(options.headers ?? {}),
      },
    })

    this._axios.interceptors.request.use((config) => {
      if (this._token) {
        config.headers.Authorization = `Bearer ${this._token}`
      }
      return config
    })

    this._axios.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(normalizeAxiosError(error)),
    )
  }

  setToken(token) {
    this._token = token || null
  }

  clearToken() {
    this._token = null
  }

  get token() {
    return this._token
  }

  _normalizeConfigForBody(data, config) {
    const cfg = config ? { ...config, headers: { ...(config.headers ?? {}) } } : { headers: {} }
    const isFormData = typeof FormData !== 'undefined' && data instanceof FormData

    if (!isFormData) {
      if (!('Content-Type' in cfg.headers) && !('content-type' in cfg.headers)) {
        cfg.headers['Content-Type'] = 'application/json'
      }
      return cfg
    }

    if ('Content-Type' in cfg.headers) {
      delete cfg.headers['Content-Type']
    }

    if ('content-type' in cfg.headers) {
      delete cfg.headers['content-type']
    }

    return cfg
  }

  async get(url, config) {
    const response = await this._axios.get(url, config)
    return response.data
  }

  async post(url, data, config) {
    const normalizedConfig = this._normalizeConfigForBody(data, config)
    const response = await this._axios.post(url, data, normalizedConfig)
    return response.data
  }

  async put(url, data, config) {
    const normalizedConfig = this._normalizeConfigForBody(data, config)
    const response = await this._axios.put(url, data, normalizedConfig)
    return response.data
  }

  async patch(url, data, config) {
    const normalizedConfig = this._normalizeConfigForBody(data, config)
    const response = await this._axios.patch(url, data, normalizedConfig)
    return response.data
  }

  async delete(url, config) {
    const response = await this._axios.delete(url, config)
    return response.data
  }
}
