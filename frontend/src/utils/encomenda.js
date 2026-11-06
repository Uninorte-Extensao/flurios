import { cpfValido } from './cpf.js'
import { telefoneValido } from './telefone.js'

export const DESCRICAO_MAXIMA = 255
export const NOVO_DESTINATARIO = 'novo'

// Valida o formulário "Nova encomenda". Devolve { campo: 'mensagem' } (vazio = válido).
export function validarEncomenda(campos) {
  const erros = {}

  if (!campos.destinoId) erros.destinoId = 'Escolha o destino.'

  if (!campos.destinatarioId) {
    erros.destinatarioId = 'Escolha um destinatário ou cadastre um novo.'
  }

  if (campos.destinatarioId === NOVO_DESTINATARIO) {
    if (!campos.destNome.trim()) erros.destNome = 'Informe o nome do destinatário.'

    if (!campos.destCpf.trim()) erros.destCpf = 'Informe o CPF do destinatário.'
    else if (!cpfValido(campos.destCpf)) erros.destCpf = 'CPF inválido.'

    if (!campos.destTelefone.trim()) erros.destTelefone = 'Informe o telefone do destinatário.'
    else if (!telefoneValido(campos.destTelefone)) {
      erros.destTelefone = 'Informe um telefone com DDD.'
    }

    if (!campos.destEndereco.trim()) erros.destEndereco = 'Informe o endereço do destinatário.'
    if (!campos.destMunicipio.trim()) erros.destMunicipio = 'Informe o município do destinatário.'
  }

  const descricao = campos.descricao.trim()
  if (!descricao) erros.descricao = 'Descreva o que será enviado.'
  else if (descricao.length > DESCRICAO_MAXIMA) {
    erros.descricao = `A descrição deve ter no máximo ${DESCRICAO_MAXIMA} caracteres.`
  }

  return erros
}

// Agrupa os destinos por rota, mantendo a ordem recebida da API:
// [{ rota: 'Manaus - Coari', destinos: [{ id, nome, rota_nome }] }]
export function agruparDestinosPorRota(destinos) {
  const grupos = []

  for (const destino of destinos) {
    let grupo = grupos.find((g) => g.rota === destino.rota_nome)
    if (!grupo) {
      grupo = { rota: destino.rota_nome, destinos: [] }
      grupos.push(grupo)
    }
    grupo.destinos.push(destino)
  }

  return grupos
}
