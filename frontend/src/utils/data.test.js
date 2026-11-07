import assert from 'node:assert/strict'
import { test } from 'node:test'
import { formatarData, formatarDataHora, lerDataApi } from './data.js'

test('data sem fuso é lida como UTC e exibida no horário de Manaus (UTC-4)', () => {
  assert.equal(formatarDataHora('2026-11-07T15:30:00'), '07/11/2026 às 11:30')
})

test('data com fuso explícito é respeitada', () => {
  assert.equal(formatarDataHora('2026-11-07T15:30:00Z'), '07/11/2026 às 11:30')
  assert.equal(formatarDataHora('2026-11-07T15:30:00+00:00'), '07/11/2026 às 11:30')
})

test('a data muda de dia quando a hora UTC passa da meia-noite em Manaus', () => {
  assert.equal(formatarData('2026-11-08T02:00:00'), '07/11/2026')
})

test('frações de segundo (microssegundos) são aceitas', () => {
  assert.equal(formatarDataHora('2026-11-07T15:30:00.123456'), '07/11/2026 às 11:30')
})

test('valor vazio ou inválido vira traço', () => {
  assert.equal(lerDataApi(null), null)
  assert.equal(formatarData('lixo'), '—')
  assert.equal(formatarDataHora(undefined), '—')
})
