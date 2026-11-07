import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  ehManaus,
  lerInteiroPositivo,
  NOME_MAXIMO,
  ordenarParadas,
  origemEhManaus,
  podeRemoverParada,
  proximaOrdem,
  sugestaoParada,
  validarEmbarcacao,
  validarParada,
  validarRota,
} from './frota.js'
import { ehAdministrador } from './perfil.js'

const MANAUS = { id: 1, rota_id: 1, nome: 'Manaus', ordem: 1 }
const COARI = { id: 2, rota_id: 1, nome: 'Coari', ordem: 2 }

test('ehManaus ignora caixa, acento e espaços', () => {
  assert.equal(ehManaus('Manaus'), true)
  assert.equal(ehManaus('  MANAUS '), true)
  assert.equal(ehManaus('Mánaus'), true)
  assert.equal(ehManaus('Manacapuru'), false)
  assert.equal(ehManaus(''), false)
})

test('lerInteiroPositivo só aceita inteiros maiores que zero', () => {
  assert.equal(lerInteiroPositivo('12'), 12)
  assert.equal(lerInteiroPositivo(' 3 '), 3)
  for (const invalido of ['0', '-1', '1.5', '1,5', 'abc', '', null, undefined, '1e3']) {
    assert.equal(lerInteiroPositivo(invalido), null, String(invalido))
  }
})

test('embarcação válida não tem erros', () => {
  assert.deepEqual(validarEmbarcacao({ nome: 'M/V Solimões', capacidade: '120' }), {})
})

test('embarcação exige nome e capacidade inteira maior que zero', () => {
  assert.equal(validarEmbarcacao({ nome: '  ', capacidade: '10' }).nome, 'Informe o nome da embarcação.')
  assert.equal(validarEmbarcacao({ nome: 'A', capacidade: '' }).capacidade, 'Informe a capacidade.')
  assert.match(validarEmbarcacao({ nome: 'A', capacidade: '0' }).capacidade, /maior que zero/)
  assert.match(validarEmbarcacao({ nome: 'A', capacidade: '2,5' }).capacidade, /inteiro/)
})

test('nome acima do limite é recusado', () => {
  const erros = validarEmbarcacao({ nome: 'x'.repeat(NOME_MAXIMO + 1), capacidade: '5' })
  assert.match(erros.nome, /no máximo 100/)
  assert.deepEqual(validarRota({ nome: 'x'.repeat(NOME_MAXIMO) }), {})
})

test('rota exige nome', () => {
  assert.equal(validarRota({ nome: '' }).nome, 'Informe o nome da rota.')
})

test('proximaOrdem sugere a seguinte à maior ordem', () => {
  assert.equal(proximaOrdem([]), 1)
  assert.equal(proximaOrdem([MANAUS, COARI]), 3)
  assert.equal(proximaOrdem([MANAUS, { ...COARI, ordem: 5 }]), 6)
})

test('ordenarParadas ordena sem alterar a lista original', () => {
  const original = [COARI, MANAUS]
  assert.deepEqual(ordenarParadas(original), [MANAUS, COARI])
  assert.deepEqual(original, [COARI, MANAUS])
})

test('a primeira parada de uma rota vazia precisa ser Manaus com ordem 1', () => {
  assert.deepEqual(validarParada({ nome: 'Manaus', ordem: '1' }, []), {})
  assert.equal(
    validarParada({ nome: 'Coari', ordem: '1' }, []).nome,
    'A parada de ordem 1 deve ser Manaus.',
  )
  assert.match(validarParada({ nome: 'Coari', ordem: '2' }, []).ordem, /Cadastre primeiro a parada de ordem 1/)
})

test('parada nova não pode repetir a ordem de outra', () => {
  assert.match(validarParada({ nome: 'Tefé', ordem: '2' }, [MANAUS, COARI]).ordem, /Já existe uma parada/)
  assert.deepEqual(validarParada({ nome: 'Tefé', ordem: '3' }, [MANAUS, COARI]), {})
})

test('parada exige nome e ordem inteira maior que zero', () => {
  const erros = validarParada({ nome: '', ordem: 'x' }, [MANAUS])
  assert.equal(erros.nome, 'Informe o nome da parada.')
  assert.match(erros.ordem, /número inteiro/)
  assert.equal(validarParada({ nome: 'A', ordem: '' }, [MANAUS]).ordem, 'Informe a ordem da parada.')
})

test('origemEhManaus confere a parada de ordem 1', () => {
  assert.equal(origemEhManaus([MANAUS, COARI]), true)
  assert.equal(origemEhManaus([{ ...MANAUS, nome: 'Itacoatiara' }, COARI]), false)
  assert.equal(origemEhManaus([COARI]), false)
  assert.equal(origemEhManaus([]), false)
})

test('a origem só pode ser removida quando é a única parada', () => {
  assert.equal(podeRemoverParada(MANAUS, [MANAUS, COARI]), false)
  assert.equal(podeRemoverParada(MANAUS, [MANAUS]), true)
  assert.equal(podeRemoverParada(COARI, [MANAUS, COARI]), true)
})

test('ordem 1 que não é Manaus pode ser removida para corrigir a rota', () => {
  const errada = { ...MANAUS, nome: 'Itacoatiara' }
  assert.equal(podeRemoverParada(errada, [errada, COARI]), true)
})

test('sugestaoParada começa por Manaus e depois sugere a próxima ordem', () => {
  assert.deepEqual(sugestaoParada([]), { nome: 'Manaus', ordem: 1 })
  assert.deepEqual(sugestaoParada([COARI]), { nome: 'Manaus', ordem: 1 })
  assert.deepEqual(sugestaoParada([MANAUS, COARI]), { nome: '', ordem: 3 })
})

test('só empresa com perfil administrador é administrador', () => {
  assert.equal(ehAdministrador({ tipo: 'empresa', perfil: 'administrador' }), true)
  assert.equal(ehAdministrador({ tipo: 'empresa', perfil: 'atendente' }), false)
  assert.equal(ehAdministrador({ tipo: 'cliente', perfil: null }), false)
  assert.equal(ehAdministrador(null), false)
})
