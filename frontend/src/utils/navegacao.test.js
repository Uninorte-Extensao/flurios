import assert from 'node:assert/strict'
import { test } from 'node:test'
import { MENUS } from '../routes/menus.js'
import { barraTemMais, caminhoDaBusca, dividirItensDaBarra } from './navegacao.js'
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

test('o painel tem um único item no menu lateral da empresa, sem "Dashboard"', () => {
  const caminhos = MENUS.empresa.itens.map((i) => i.para)
  const rotulos = MENUS.empresa.itens.map((i) => i.rotulo)

  assert.equal(caminhos.filter((c) => c === '/empresa').length, 1)
  assert.ok(!caminhos.includes('/empresa/dashboard'))
  assert.ok(!rotulos.includes('Dashboard'))
  assert.equal(new Set(caminhos).size, caminhos.length)
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

test('a barra do cliente tem 3 itens fixos e nenhum extra: o "Mais" abre só Suporte e Sair', () => {
  const { fixos, extras } = dividirItensDaBarra(MENUS.cliente.barraInferior)

  assert.equal(fixos.length, 3)
  assert.deepEqual(extras, [])
  assert.equal(barraTemMais(extras, MENUS.cliente.suporte, () => {}), true)
})

test('"Mais" existe com item sobrando, com Suporte ou com Sair; sem nenhum dos três, não', () => {
  const item = { para: '/x' }

  assert.equal(barraTemMais([item], null, null), true)
  assert.equal(barraTemMais([], { para: '/suporte' }, null), true)
  assert.equal(barraTemMais([], null, () => {}), true)
  assert.equal(barraTemMais([], null, null), false)
})

test('toda área tem Suporte definido para o "Mais" abrir', () => {
  for (const area of Object.values(MENUS)) assert.ok(area.suporte?.para)
})

test('busca do header da empresa abre o detalhe da encomenda com o código normalizado', () => {
  assert.equal(caminhoDaBusca('empresa', 'flx4k9ab3c1z'), '/empresa/encomendas/FLX4K9AB3C1Z')
  assert.equal(caminhoDaBusca('empresa', '  FLX4K9AB3C1Z  '), '/empresa/encomendas/FLX4K9AB3C1Z')
})

test('busca do header do cliente continua abrindo o detalhe do cliente', () => {
  assert.equal(caminhoDaBusca('cliente', 'flx123'), '/cliente/encomendas/FLX123')
})

test('busca vazia ou de área desconhecida não navega', () => {
  assert.equal(caminhoDaBusca('empresa', ''), null)
  assert.equal(caminhoDaBusca('empresa', '   '), null)
  assert.equal(caminhoDaBusca('empresa', null), null)
  assert.equal(caminhoDaBusca('outra', 'FLX1'), null)
})

test('busca escapa caracteres que quebrariam a URL do detalhe', () => {
  assert.equal(caminhoDaBusca('empresa', 'a/b?c#d'), '/empresa/encomendas/A%2FB%3FC%23D')
})
