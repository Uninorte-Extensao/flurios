import { useCallback, useState } from 'react'
import Alerta from '../../components/Alerta'
import CampoSelecao from '../../components/CampoSelecao'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import Modal from '../../components/Modal'
import { useCarga } from '../../hooks/useCarga'
import { listarEmbarcacoes } from '../../services/embarcacoes'
import { obterRota } from '../../services/rotas'
import { associarEncomenda, listarViagens } from '../../services/viagens'
import { formatarDataHora } from '../../utils/data'
import { ROTULOS_STATUS, viagemAceitaEncomenda } from '../../utils/gestaoEncomenda'
import './Encomendas.css'

const STATUS_VIAGEM = { programada: 'programada', em_andamento: 'em andamento' }

// Viagens programadas ou em andamento cuja rota contém o destino. A lista de viagens só traz ids,
// então as rotas (com paradas) e as embarcações são buscadas à parte.
async function carregarElegiveis(paradaDestinoId) {
  const [viagens, embarcacoes] = await Promise.all([listarViagens(), listarEmbarcacoes()])
  const ativas = viagens.filter((v) => v.status in STATUS_VIAGEM)
  const rotas = await Promise.all([...new Set(ativas.map((v) => v.rota_id))].map(obterRota))
  const rotaPorId = Object.fromEntries(rotas.map((r) => [r.id, r]))
  const encomenda = { parada_destino_id: paradaDestinoId }

  return ativas
    .filter((v) => viagemAceitaEncomenda(v, rotaPorId[v.rota_id], encomenda))
    .map((v) => ({
      ...v,
      rota_nome: rotaPorId[v.rota_id].nome,
      embarcacao_nome: embarcacoes.find((e) => e.id === v.embarcacao_id)?.nome ?? '—',
    }))
}

const descricaoViagem = (v) =>
  `Viagem #${v.id} · ${v.embarcacao_nome} · ${v.rota_nome} · saída ${formatarDataHora(v.data_saida)} (${STATUS_VIAGEM[v.status]})`

// Associa uma encomenda (recebida ou aguardando embarque) a uma viagem elegível.
// `aoAssociada(viagemId)` roda depois do sucesso; os 409 do backend aparecem na própria janela.
export default function AssociarViagemModal({ encomenda, aoFechar, aoAssociada }) {
  const destinoId = encomenda.parada_destino_id
  const carregar = useCallback(() => carregarElegiveis(destinoId), [destinoId])
  const { carregando, erro, dados, recarregar } = useCarga(carregar)

  const [viagemId, setViagemId] = useState('')
  const [erroAcao, setErroAcao] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setErroAcao('')

    if (!viagemId) {
      setErroAcao('Escolha a viagem.')
      return
    }

    setEnviando(true)
    try {
      await associarEncomenda(Number(viagemId), encomenda.id)
      aoAssociada(Number(viagemId))
    } catch (falha) {
      setErroAcao(falha.message)
      setEnviando(false)
    }
  }

  const pronto = !carregando && !erro
  const elegiveis = dados ?? []

  return (
    <Modal titulo="Associar à viagem" aoFechar={aoFechar} bloqueado={enviando}>
      <p className="encomenda__texto">
        Encomenda <strong>{encomenda.codigo_rastreio}</strong> · destino{' '}
        <strong>{encomenda.destino_nome ?? '—'}</strong> · {ROTULOS_STATUS[encomenda.status]}
      </p>

      {carregando && <Carregando />}
      {erro && <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />}

      {pronto && elegiveis.length === 0 && (
        <Alerta tipo="info">
          Nenhuma viagem programada ou em andamento passa por {encomenda.destino_nome ?? 'este destino'}.
          Programe uma viagem com uma rota que contenha o destino.
        </Alerta>
      )}

      {pronto && elegiveis.length > 0 && (
        <form onSubmit={enviar} noValidate>
          {erroAcao && <Alerta tipo="erro">{erroAcao}</Alerta>}

          <CampoSelecao
            rotulo="Viagem"
            value={viagemId}
            onChange={(e) => {
              setViagemId(e.target.value)
              setErroAcao('')
            }}
            ajuda="Só aparecem viagens programadas ou em andamento cuja rota contém o destino da encomenda."
          >
            <option value="">Escolha a viagem</option>
            {elegiveis.map((v) => (
              <option key={v.id} value={v.id}>
                {descricaoViagem(v)}
              </option>
            ))}
          </CampoSelecao>

          <div className="modal__acoes">
            <button type="button" className="btn btn--contorno" onClick={aoFechar} disabled={enviando}>
              Cancelar
            </button>
            <button type="submit" className="btn btn--primario" disabled={enviando}>
              {enviando ? 'Associando...' : 'Associar'}
            </button>
          </div>
        </form>
      )}

      {!(pronto && elegiveis.length > 0) && (
        <div className="modal__acoes">
          <button type="button" className="btn btn--contorno" onClick={aoFechar}>
            Fechar
          </button>
        </div>
      )}
    </Modal>
  )
}
