import assert from 'node:assert/strict'
import { test } from 'node:test'
import { rotuloDoStatus, STATUS } from './status.js'

test('rotuloDoStatus devolve o texto em português, com acento', () => {
  assert.equal(rotuloDoStatus('concluida'), 'Concluída')
  assert.equal(rotuloDoStatus('em_andamento'), 'Em andamento')
  assert.equal(rotuloDoStatus('em_transito'), 'Em trânsito')
})

test('status desconhecido volta como veio', () => {
  assert.equal(rotuloDoStatus('novo_status'), 'novo_status')
})

test('nenhum rótulo mostra o valor técnico da API', () => {
  for (const [chave, { rotulo }] of Object.entries(STATUS)) {
    assert.ok(!rotulo.includes('_'), chave)
    assert.notEqual(rotulo, chave)
  }
})
