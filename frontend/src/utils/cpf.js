// Utilitários de CPF. LGPD: nunca logar CPF e nunca exibir completo (use mascararCpf).

export const CPF_OCULTO = '***.***.***-**'

export function somenteDigitos(texto) {
  return String(texto ?? '').replace(/\D/g, '')
}

function calcularDigito(parcial) {
  const peso = parcial.length + 1
  const soma = [...parcial].reduce((total, digito, i) => total + Number(digito) * (peso - i), 0)
  const resto = (soma * 10) % 11
  return String(resto < 10 ? resto : 0)
}

export function cpfValido(valor) {
  const cpf = somenteDigitos(valor)

  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false

  const dv1 = calcularDigito(cpf.slice(0, 9))
  const dv2 = calcularDigito(cpf.slice(0, 9) + dv1)

  return cpf.slice(9) === dv1 + dv2
}

// Máscara de digitação do campo: 000.000.000-00
export function formatarCpfDigitado(valor) {
  const d = somenteDigitos(valor).slice(0, 11)
  const base = [d.slice(0, 3), d.slice(3, 6), d.slice(6, 9)].filter(Boolean).join('.')
  return d.length > 9 ? `${base}-${d.slice(9)}` : base
}

// Máscara de EXIBIÇÃO: 123.***.***-45. Qualquer formato inesperado é ocultado por inteiro.
export function mascararCpf(valor) {
  const texto = String(valor ?? '')

  if (/^\d{3}\.\*{3}\.\*{3}-\d{2}$/.test(texto)) return texto

  const cpf = somenteDigitos(texto)
  if (cpf.length !== 11) return CPF_OCULTO

  return `${cpf.slice(0, 3)}.***.***-${cpf.slice(9)}`
}
