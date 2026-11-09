import { apiRequest } from './client.js'

export const listMaterials = () => apiRequest('/api/materials')

export function uploadMaterial(title, memo, file) {
  const form = new FormData()
  form.append('title', title)
  form.append('memo', memo)
  form.append('file', file)
  return apiRequest('/api/materials', { method: 'POST', body: form })
}

export const deleteMaterial = (id) => apiRequest(`/api/materials/${id}`, { method: 'DELETE' })
