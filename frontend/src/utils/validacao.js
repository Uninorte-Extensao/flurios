const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function emailValido(valor) {
  return EMAIL.test(String(valor).trim())
}
