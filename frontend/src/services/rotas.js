import { api } from './api'

// Cada rota: { id, nome, criado_em }. Ordenadas por nome.
export function listarRotas() {
  return api.get('/rotas')
}

export function cadastrarRota({ nome }) {
  return api.post('/rotas', { nome })
}

// { id, nome, criado_em, paradas: [{ id, rota_id, nome, ordem }] } com as paradas em ordem.
export function obterRota(id) {
  return api.get(`/rotas/${id}`)
}

// 409 quando já existe uma parada com a mesma ordem na rota.
export function cadastrarParada(rotaId, { nome, ordem }) {
  return api.post(`/rotas/${rotaId}/paradas`, { nome, ordem })
}

export function removerParada(rotaId, paradaId) {
  return api.delete(`/rotas/${rotaId}/paradas/${paradaId}`)
}
