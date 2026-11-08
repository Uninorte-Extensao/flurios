import { api } from './api'

// Dashboard da empresa (somente leitura). Cada função chama um endpoint; a tela os carrega
// separadamente, então a falha de um não derruba os outros. Todos exigem login da empresa.

// { total, por_status: { pendente, recebida, aguardando_embarque, embarcada, em_transito,
//   chegou_ao_destino, a_retirar, entregue, imprevisto } }
export function obterResumoEncomendas() {
  return api.get('/dashboard/resumo')
}

// { em_andamento, total, por_status: { programada, em_andamento, concluida, cancelada } }
export function obterResumoViagens() {
  return api.get('/dashboard/viagens')
}

// { total, municipios: [{ municipio, total }] }, do maior para o menor (destino real da encomenda).
export function obterEncomendasPorMunicipio() {
  return api.get('/dashboard/municipios')
}

// { total, viagens: [{ viagem_id, embarcacao_id, embarcacao_nome, rota_nome, capacidade,
//   encomendas_ativas, ocupacao }] }. Só viagens em andamento; `ocupacao` é uma proporção
// (0.5 = 50%) e pode passar de 1. A capacidade da embarcação conta encomendas.
export function obterOcupacao() {
  return api.get('/dashboard/ocupacao')
}

// { total, envios: [{ codigo_rastreio, destinatario, municipio_destino, proxima_parada | null,
//   status, progresso }] }. `progresso` é a proporção (0 a 1) das paradas da rota já registradas.
export function obterEnviosAtivos() {
  return api.get('/dashboard/envios-ativos')
}

// { total, movimentacoes: [{ codigo_rastreio, status, parada | null, data }] }, da mais recente
// para a mais antiga. `data` vem em UTC sem fuso (ver `formatarDataHora`).
export function obterMovimentacoesRecentes(limite = 10) {
  return api.get(`/dashboard/movimentacoes-recentes?limite=${limite}`)
}
