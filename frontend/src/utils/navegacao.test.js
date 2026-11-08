import assert from 'node:assert/strict'
import { test } from 'node:test'
import { MENUS } from '../routes/menus.js'
import { dividirItensDaBarra } from './navegacao.js'
import { itensDoMenuParaUsuario } from './perfil.js'

const PERFIS_EMPRESA = ['administrador', 'atendente', 'operador_embarcacao', 'funcionario_retirada']

const itens = (n) => Array.from({ length: n }, (_, i) => ({ para: `/x/${i}` }))

test('até 4 itens ficam todos fixos, sem "Mais"', () => {
  for (const n of [0, 3, 4]) {
    const { fixos, extras } = dividirItensDaBarra(itens(n))

    assert.equal(fixos.length, n)
    assert.deepEqual(extras, [])
  }
})

test('acima de 4 itens, os 4 primeiros ficam fixos e o resto vai para o "Mais"', () => {
  const { fixos, extras } = dividirItensDaBarra(itens(7))

  assert.deepEqual(fixos.map((i) => i.para), ['/x/0', '/x/1', '/x/2', '/x/3'])
  assert.deepEqual(extras.map((i) => i.para), ['/x/4', '/x/5', '/x/6'])
})

test('a barra da empresa nunca passa de 4 fixos, para nenhum perfil', () => {
  for (const perfil of PERFIS_EMPRESA) {
    const visiveis = itensDoMenuParaUsuario(MENUS.empresa.barraInferior, { tipo: 'empresa', perfil })
    const { fixos, extras } = dividirItensDaBarra(visiveis)

    assert.ok(fixos.length <= 4, perfil)
    assert.equal(fixos.length + extras.length, visiveis.length, perfil)
  }
})

test('a barra da empresa não repete a tela do painel: Início já é o Dashboard', () => {
  const caminhos = MENUS.empresa.barraInferior.map((i) => i.para)

  assert.ok(caminhos.includes('/empresa'))
  assert.ok(!caminhos.includes('/empresa/dashboard'))
  assert.equal(new Set(caminhos).size, caminhos.length)
})

test('funcionário de retirada e administrador têm Retiradas entre os fixos; os demais não têm o item', () => {
  const fixosDe = (perfil) =>
    dividirItensDaBarra(itensDoMenuParaUsuario(MENUS.empresa.barraInferior, { tipo: 'empresa', perfil })).fixos.map(
      (i) => i.para,
    )

  assert.ok(fixosDe('funcionario_retirada').includes('/empresa/retiradas'))
  assert.ok(fixosDe('administrador').includes('/empresa/retiradas'))
  assert.ok(!fixosDe('atendente').includes('/empresa/retiradas'))
  assert.ok(!fixosDe('operador_embarcacao').includes('/empresa/retiradas'))
})

test('a barra do cliente continua com 3 itens, sem "Mais"', () => {
  assert.deepEqual(dividirItensDaBarra(MENUS.cliente.barraInferior).extras, [])
})
