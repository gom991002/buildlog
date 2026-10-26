import { apiRequest } from './client.js'

export const signup = (email, password, nickname) =>
  apiRequest('/api/auth/signup', { method: 'POST', body: { email, password, nickname } })

export const login = (email, password) =>
  apiRequest('/api/auth/login', { method: 'POST', body: { email, password } })

export const logout = () => apiRequest('/api/auth/logout', { method: 'POST' })

export const fetchMe = () => apiRequest('/api/auth/me')

export const changeNickname = (nickname) =>
  apiRequest('/api/users/me/nickname', { method: 'PATCH', body: { nickname } })
