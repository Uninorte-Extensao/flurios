import assert from 'node:assert/strict'
import { test } from 'node:test'
import { CPF_OCULTO, cpfValido, formatarCpfDigitado, mascararCpf } from './cpf.js'
import { formatarTelefoneDigitado, telefoneValido } from './telefone.js'

test('cpfValido aceita CPF válido com ou sem pontuação', () => {
  assert.equal(cpfValido('11122233396'), true)
  assert.equal(cpfValido('111.222.333-96'), true)
})

test('cpfValido rejeita dígito verificador errado, tamanho errado e repetidos', () => {
  assert.equal(cpfValido('11122233397'), false)
  assert.equal(cpfValido('1112223339'), false)
  assert.equal(cpfValido('111222333961'), false)
  assert.equal(cpfValido('11111111111'), false)
  assert.equal(cpfValido(''), false)
})

test('formatarCpfDigitado aplica a máscara de digitação', () => {
  assert.equal(formatarCpfDigitado('1112'), '111.2')
  assert.equal(formatarCpfDigitado('11122233396'), '111.222.333-96')
  assert.equal(formatarCpfDigitado('111222333961234'), '111.222.333-96')
})

test('mascararCpf nunca devolve o CPF completo', () => {
  assert.equal(mascararCpf('11122233396'), '111.***.***-96')
  assert.equal(mascararCpf('111.222.333-96'), '111.***.***-96')
  assert.equal(mascararCpf('111.***.***-96'), '111.***.***-96')
  assert.equal(mascararCpf('123'), CPF_OCULTO)
  assert.equal(mascararCpf(undefined), CPF_OCULTO)
})

test('telefone: máscara e validação', () => {
  assert.equal(formatarTelefoneDigitado('92999990000'), '(92) 99999-0000')
  assert.equal(formatarTelefoneDigitado('9233330000'), '(92) 3333-0000')
  assert.equal(formatarTelefoneDigitado(''), '')
  assert.equal(telefoneValido('(92) 99999-0000'), true)
  assert.equal(telefoneValido('(92) 3333-0000'), true)
  assert.equal(telefoneValido('9299'), false)
})
