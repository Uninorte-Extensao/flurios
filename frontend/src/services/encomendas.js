import { api } from './api'

// Paradas que podem ser destino (todas, menos a origem): [{ id, nome, rota_nome }]
export function listarDestinos() {
  return api.get('/rotas/destinos')
}

// Destinatários do cliente logado. O CPF já chega mascarado (123.***.***-45).
export function listarDestinatarios() {
  return api.get('/destinatarios')
}

// O CPF vai só com dígitos.
export function cadastrarDestinatario({ nome, cpf, telefone, endereco, municipio }) {
  return api.post('/destinatarios', { nome, cpf, telefone, endereco, municipio })
}

// Devolve a encomenda criada, com `codigo_rastreio` e `destino_nome`.
export function criarEncomenda({ destinatarioId, paradaDestinoId, descricao }) {
  return api.post('/encomendas', {
    destinatario_id: destinatarioId,
    parada_destino_id: paradaDestinoId,
    descricao,
  })
}
