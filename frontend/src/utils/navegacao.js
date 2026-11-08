// Barra inferior do mobile: no máximo 4 itens fixos; se sobrar item, entra o botão "Mais".
export const MAX_ITENS_FIXOS = 4

// Separa os itens da barra em fixos (os primeiros) e extras (os que vão para o "Mais").
// A ordem da lista em `menus.js` é a prioridade: o que importa mais fica antes.
export function dividirItensDaBarra(itens, maxFixos = MAX_ITENS_FIXOS) {
  if (itens.length <= maxFixos) return { fixos: itens, extras: [] }

  return { fixos: itens.slice(0, maxFixos), extras: itens.slice(maxFixos) }
}
