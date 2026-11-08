import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  caminhoViagem,
  ENVIOS_POR_VEZ,
  envioSemViagem,
  formatarNumero,
  larguraBarra,
  limitarEnvios,
  listarPorStatus,
  maiorTotal,
  ORDEM_STATUS_ENCOMENDA,
  ORDEM_STATUS_VIAGEM,
  percentual,
  percentualDoMaior,
  percentualDoTotal,
  textoOcupacao,
  textoProximaParada,
  totalDoStatus,
  varianteOcupacao,
  varianteProgresso,
} from './dashboard.js'

test('a ordem dos status da encomenda segue o fluxo e termina em imprevisto', () => {
  assert.equal(ORDEM_STATUS_ENCOMENDA.length, 9)
  assert.equal(ORDEM_STATUS_ENCOMENDA[0], 'pendente')
  assert.equal(ORDEM_STATUS_ENCOMENDA[7], 'entregue')
  assert.equal(ORDEM_STATUS_ENCOMENDA.at(-1), 'imprevisto')
  assert.deepEqual(ORDEM_STATUS_VIAGEM, ['programada', 'em_andamento', 'concluida', 'cancelada'])
})

test('listarPorStatus segue a ordem, zera o que falta e mantém status desconhecidos no final', () => {
  const lista = listarPorStatus({ entregue: 5, pendente: 2, novo_status: 1 }, ORDEM_STATUS_ENCOMENDA)

  assert.equal(lista.length, 10)
  assert.deepEqual(lista[0], { status: 'pendente', total: 2 })
  assert.deepEqual(lista[1], { status: 'recebida', total: 0 })
  assert.deepEqual(lista[7], { status: 'entregue', total: 5 })
  assert.deepEqual(lista.at(-1), { status: 'novo_status', total: 1 })
})

test('listarPorStatus aceita resposta vazia', () => {
  assert.deepEqual(listarPorStatus(undefined, ORDEM_STATUS_VIAGEM).map((i) => i.total), [0, 0, 0, 0])
})

test('totalDoStatus devolve zero quando o status não existe', () => {
  assert.equal(totalDoStatus({ em_transito: 4 }, 'em_transito'), 4)
  assert.equal(totalDoStatus({ em_transito: 4 }, 'a_retirar'), 0)
  assert.equal(totalDoStatus(null, 'a_retirar'), 0)
})

test('percentual arredonda e não limita acima de 100', () => {
  assert.equal(percentual(0.5), 50)
  assert.equal(percentual(0.3333), 33)
  assert.equal(percentual(0.875), 88)
  assert.equal(percentual(1.25), 125)
  assert.equal(percentual(0), 0)
  assert.equal(percentual(undefined), 0)
  assert.equal(percentual('abc'), 0)
})

test('larguraBarra nunca sai de 0 a 100', () => {
  assert.equal(larguraBarra(125), 100)
  assert.equal(larguraBarra(-5), 0)
  assert.equal(larguraBarra(40), 40)
})

test('percentualDoTotal e percentualDoMaior não dividem por zero', () => {
  assert.equal(percentualDoTotal(1, 4), 25)
  assert.equal(percentualDoTotal(0, 0), 0)
  assert.equal(percentualDoMaior(3, 12), 25)
  assert.equal(percentualDoMaior(12, 12), 100)
  assert.equal(percentualDoMaior(0, 0), 0)
})

test('maiorTotal acha a base das barras relativas', () => {
  assert.equal(maiorTotal([{ total: 3 }, { total: 12 }, { total: 7 }]), 12)
  assert.equal(maiorTotal([]), 0)
})

test('a ocupação passa a coral só acima da capacidade', () => {
  assert.equal(varianteOcupacao(0.5), 'azul')
  assert.equal(varianteOcupacao(1), 'azul')
  assert.equal(varianteOcupacao(1.2), 'coral')
})

test('o progresso fica verde só quando completo', () => {
  assert.equal(varianteProgresso(0), 'azul')
  assert.equal(varianteProgresso(0.75), 'azul')
  assert.equal(varianteProgresso(1), 'verde')
})

test('textoOcupacao usa nº de encomendas como capacidade', () => {
  assert.equal(textoOcupacao({ encomendas_ativas: 7, capacidade: 20 }), '7 de 20 encomendas')
  assert.equal(textoOcupacao({ encomendas_ativas: 1, capacidade: 1 }), '1 de 1 encomenda')
})

test('limitarEnvios mostra os primeiros e conta os escondidos', () => {
  const envios = Array.from({ length: 25 }, (_, i) => ({ codigo_rastreio: `FLX-${i}` }))

  const primeira = limitarEnvios(envios, ENVIOS_POR_VEZ)
  assert.equal(primeira.visiveis.length, 10)
  assert.equal(primeira.restantes, 15)

  const todos = limitarEnvios(envios, 30)
  assert.equal(todos.visiveis.length, 25)
  assert.equal(todos.restantes, 0)
})

test('formatarNumero usa separador de milhar em português', () => {
  assert.equal(formatarNumero(3150).replace(/\s/g, ' '), '3.150')
  assert.equal(formatarNumero(0), '0')
})

test('caminhoViagem leva ao detalhe da viagem', () => {
  assert.equal(caminhoViagem(7), '/empresa/viagens/7')
})

test('próxima parada: a parada, "Sem viagem" ou "No destino"', () => {
  assert.equal(textoProximaParada({ proxima_parada: 'Tefé', progresso: 0.5 }), 'Tefé')
  assert.equal(textoProximaParada({ proxima_parada: null, progresso: 0 }), 'Sem viagem')
  assert.equal(textoProximaParada({ proxima_parada: null, progresso: 1 }), 'No destino')
})

test('envio sem viagem = sem próxima parada e progresso 0; no destino (100%) não é sem viagem', () => {
  assert.equal(envioSemViagem({ proxima_parada: null, progresso: 0 }), true)
  assert.equal(envioSemViagem({ proxima_parada: 'Manaus', progresso: 0 }), false)
  assert.equal(envioSemViagem({ proxima_parada: null, progresso: 1 }), false)
})
