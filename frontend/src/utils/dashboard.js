// Regras de exibição do dashboard. Tudo aqui vale só na tela (o backend devolve os números crus).

// Ordem do fluxo da encomenda (mesma do CLAUDE.md), com `imprevisto` por último.
export const ORDEM_STATUS_ENCOMENDA = [
  'pendente',
  'recebida',
  'aguardando_embarque',
  'embarcada',
  'em_transito',
  'chegou_ao_destino',
  'a_retirar',
  'entregue',
  'imprevisto',
]

export const ORDEM_STATUS_VIAGEM = ['programada', 'em_andamento', 'concluida', 'cancelada']

// Quantos envios ativos a tabela mostra por vez (a API devolve todos, sem paginação).
export const ENVIOS_POR_VEZ = 10

// Quantas movimentações recentes são pedidas à API.
export const LIMITE_MOVIMENTACOES = 10

// { status: total } -> [{ status, total }] na ordem dada. Status fora da ordem conhecida vão ao
// final (um status novo no backend continua aparecendo), e status ausente conta como zero.
export function listarPorStatus(porStatus, ordem) {
  const dados = porStatus ?? {}
  const conhecidos = ordem.map((status) => ({ status, total: dados[status] ?? 0 }))
  const extras = Object.keys(dados)
    .filter((status) => !ordem.includes(status))
    .map((status) => ({ status, total: dados[status] }))

  return [...conhecidos, ...extras]
}

export function totalDoStatus(porStatus, status) {
  return porStatus?.[status] ?? 0
}

// Proporção (0.5) -> percentual inteiro (50). Sem limite: 1.25 vira 125.
export function percentual(proporcao) {
  const valor = Number(proporcao)

  return Number.isFinite(valor) ? Math.round(valor * 100) : 0
}

// Largura de uma barra de progresso: o texto mostra o valor real, a barra nunca passa de 100%.
export function larguraBarra(percentualInteiro) {
  return Math.min(100, Math.max(0, percentualInteiro))
}

// Parte de `valor` em `total`, em percentual inteiro (total zero -> 0).
export function percentualDoTotal(valor, total) {
  return total > 0 ? Math.round((valor / total) * 100) : 0
}

// Barras relativas (municípios, status): a maior vale 100%; sem nenhum valor, 0%.
export function percentualDoMaior(valor, maior) {
  return maior > 0 ? Math.round((valor / maior) * 100) : 0
}

// Ocupação acima da capacidade vira coral; dentro dela, azul.
export function varianteOcupacao(proporcao) {
  return proporcao > 1 ? 'coral' : 'azul'
}

// Progresso completo (todas as paradas registradas) vira verde; antes disso, azul.
export function varianteProgresso(proporcao) {
  return proporcao >= 1 ? 'verde' : 'azul'
}

export function textoOcupacao(viagem) {
  const { encomendas_ativas: ativas, capacidade } = viagem

  return `${ativas} de ${capacidade} ${capacidade === 1 ? 'encomenda' : 'encomendas'}`
}

// Maior `total` da lista: é a base (100%) das barras relativas.
export function maiorTotal(itens) {
  return itens.reduce((maior, item) => Math.max(maior, item.total), 0)
}

// Mostra só os primeiros `quantidade` envios; `restantes` diz quantos ficam escondidos.
export function limitarEnvios(envios, quantidade) {
  return { visiveis: envios.slice(0, quantidade), restantes: Math.max(0, envios.length - quantidade) }
}

// 3150 -> "3.150"
export function formatarNumero(valor) {
  return Number(valor).toLocaleString('pt-BR')
}

export const caminhoViagem = (id) => `/empresa/viagens/${id}`
