import assert from 'node:assert/strict'
import { test } from 'node:test'
import { ehAdministrador, itensDoMenuParaUsuario } from './perfil.js'

const ITENS = [
  { para: '/empresa/encomendas' },
  { para: '/empresa/retiradas', perfis: ['administrador', 'funcionario_retirada'] },
]

test('item de menu com perfis só aparece para esses perfis', () => {
  const caminhos = (perfil) => itensDoMenuParaUsuario(ITENS, { tipo: 'empresa', perfil }).map((i) => i.para)

  assert.deepEqual(caminhos('administrador'), ['/empresa/encomendas', '/empresa/retiradas'])
  assert.deepEqual(caminhos('funcionario_retirada'), ['/empresa/encomendas', '/empresa/retiradas'])
  assert.deepEqual(caminhos('atendente'), ['/empresa/encomendas'])
  assert.deepEqual(caminhos('operador_embarcacao'), ['/empresa/encomendas'])
  assert.deepEqual(itensDoMenuParaUsuario(ITENS, null).map((i) => i.para), ['/empresa/encomendas'])
})

test('ehAdministrador só vale para empresa administradora', () => {
  assert.equal(ehAdministrador({ tipo: 'empresa', perfil: 'administrador' }), true)
  assert.equal(ehAdministrador({ tipo: 'empresa', perfil: 'atendente' }), false)
})
