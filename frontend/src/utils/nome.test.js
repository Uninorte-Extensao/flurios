import assert from 'node:assert/strict'
import { test } from 'node:test'
import { capitalizarNome, saudacao } from './nome.js'

test('capitaliza cada palavra do nome', () => {
  assert.equal(capitalizarNome('kaue'), 'Kaue')
  assert.equal(capitalizarNome('kaue souza'), 'Kaue Souza')
})

test('nome todo em maiúsculas ou misturado também vira capitalizado', () => {
  assert.equal(capitalizarNome('KAUE SOUZA'), 'Kaue Souza')
  assert.equal(capitalizarNome('kAUe sOUza'), 'Kaue Souza')
})

test('mantém acentos e capitaliza letra acentuada no início', () => {
  assert.equal(capitalizarNome('kauê souza'), 'Kauê Souza')
  assert.equal(capitalizarNome('érica ângela'), 'Érica Ângela')
})

test('preposições ficam em minúscula, menos no começo do nome', () => {
  assert.equal(capitalizarNome('maria da silva'), 'Maria da Silva')
  assert.equal(capitalizarNome('JOÃO DOS SANTOS E SOUZA'), 'João dos Santos e Souza')
  assert.equal(capitalizarNome('da silva'), 'Da Silva')
})

test('nomes com hífen e apóstrofo', () => {
  assert.equal(capitalizarNome('ana-maria'), 'Ana-Maria')
  assert.equal(capitalizarNome("d'ávila"), "D'Ávila")
})

test('espaços sobrando são removidos', () => {
  assert.equal(capitalizarNome('  kaue   souza  '), 'Kaue Souza')
})

test('nome vazio ou ausente', () => {
  assert.equal(capitalizarNome(''), '')
  assert.equal(capitalizarNome(null), '')
  assert.equal(capitalizarNome(undefined), '')
})

test('saudação', () => {
  assert.equal(saudacao('kaue'), 'Olá, Kaue')
  assert.equal(saudacao('KAUE SOUZA'), 'Olá, Kaue Souza')
  assert.equal(saudacao(''), 'Olá')
  assert.equal(saudacao(undefined), 'Olá')
})
