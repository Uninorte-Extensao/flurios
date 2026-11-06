import { somenteDigitos } from './cpf.js'

// Máscara de digitação: (92) 99999-0000 (celular) ou (92) 3333-0000 (fixo)
export function formatarTelefoneDigitado(valor) {
  const d = somenteDigitos(valor).slice(0, 11)

  if (d.length <= 2) return d.length ? `(${d}` : ''
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`
  if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`
}

export function telefoneValido(valor) {
  const d = somenteDigitos(valor)
  return d.length === 10 || d.length === 11
}
