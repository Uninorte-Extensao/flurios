import { normalizarCodigo } from './encomenda.js'

// Barra inferior do mobile: no máximo 4 itens fixos; se sobrar item, entra o botão "Mais".
export const MAX_ITENS_FIXOS = 4

// Separa os itens da barra em fixos (os primeiros) e extras (os que vão para o "Mais").
// A ordem da lista em `menus.js` é a prioridade: o que importa mais fica antes.
export function dividirItensDaBarra(itens, maxFixos = MAX_ITENS_FIXOS) {
  if (itens.length <= maxFixos) return { fixos: itens, extras: [] }

  return { fixos: itens.slice(0, maxFixos), extras: itens.slice(maxFixos) }
}

// Telas de detalhe da encomenda: a busca do header leva o código digitado até elas.
const DETALHE_DA_ENCOMENDA = {
  cliente: '/cliente/encomendas',
  empresa: '/empresa/encomendas',
}

// Caminho aberto pela busca do header de cada área. Código vazio (ou área sem busca) não navega: null.
// O código vai em maiúsculas e escapado na URL, como o cliente já fazia.
export function caminhoDaBusca(area, texto) {
  const base = DETALHE_DA_ENCOMENDA[area]
  const codigo = normalizarCodigo(texto)

  if (!base || !codigo) return null

  return `${base}/${encodeURIComponent(codigo)}`
}
