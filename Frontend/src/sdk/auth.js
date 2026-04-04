import { Usuario } from './models'

export class AuthClient {
  constructor(http, rootClient) {
    this._http = http
    this._root = rootClient
  }

  async login(email, password) {
    const formData = new URLSearchParams()
    formData.set('username', email)
    formData.set('password', password)

    const data = await this._http.post('/auth/login', formData.toString(), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    this._http.setToken(data.access_token)
    return data
  }

  async me() {
    const data = await this._http.get('/auth/me')
    return new Usuario(this._root, data)
  }

  logout() {
    this._http.clearToken()
  }
}
