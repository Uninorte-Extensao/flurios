import { useCallback, useState } from 'react'
import Alerta from '../../components/Alerta'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import Modal from '../../components/Modal'
import StatusBadge from '../../components/StatusBadge'
import { useCarga } from '../../hooks/useCarga'
import { listarEncomendasDaEmpresa } from '../../services/encomendas'
import { associarEncomenda } from '../../services/viagens'
import { mascararCpf } from '../../utils/cpf'
import './Encomendas.css'

const LIMITE = 100

// Elegíveis para esta viagem: recebida ou aguardando embarque, sem viagem ativa e com destino na rota.
function carregarElegiveis(rotaId) {
  return listarEncomendasDaEmpresa({
    status: ['recebida', 'aguardando_embarque'],
    semViagemAtiva: true,
    rotaId,
    limite: LIMITE,
  })
}

// Associa encomendas elegíveis a uma viagem programada ou em andamento. A janela fica aberta para
// associar várias em sequência. `aoAssociar()` avisa a tela da viagem; `aoConflito()` pede que ela
// confira a viagem de novo (os 409 do backend aparecem aqui, em português).
export default function AssociarEncomendaModal({ viagem, aoFechar, aoAssociar, aoConflito }) {
  const carregar = useCallback(() => carregarElegiveis(viagem.rota_id), [viagem.rota_id])
  const { carregando, erro, dados, recarregar, definirDados } = useCarga(carregar)

  const [emCurso, setEmCurso] = useState(null)
  const [erroAcao, setErroAcao] = useState('')
  const [sucesso, setSucesso] = useState('')

  async function associar(encomenda) {
    setErroAcao('')
    setSucesso('')
    setEmCurso(encomenda.id)
    try {
      await associarEncomenda(viagem.id, encomenda.id)
      definirDados((atual) => ({
        ...atual,
        itens: atual.itens.filter((i) => i.id !== encomenda.id),
        total: atual.total - 1,
      }))
      setSucesso(`Encomenda ${encomenda.codigo_rastreio} associada à viagem.`)
      aoAssociar()
    } catch (falha) {
      setErroAcao(falha.message)
      if (falha.status === 409 || falha.status === 404) {
        // A situação mudou (outra pessoa associou, viagem encerrada, lotação...): confere de novo.
        aoConflito()
        carregarElegiveis(viagem.rota_id)
          .then((atual) => definirDados(() => atual))
          .catch(() => {})
      }
    } finally {
      setEmCurso(null)
    }
  }

  const pronto = !carregando && !erro
  const itens = dados?.itens ?? []

  return (
    <Modal titulo="Associar encomendas" aoFechar={aoFechar} bloqueado={emCurso !== null} className="modal--largo">
      <p className="texto-suave encomenda__texto">
        Encomendas <strong>Recebida</strong> ou <strong>Aguardando embarque</strong>, sem viagem ativa e com
        destino na rota desta viagem.
      </p>

      {erroAcao && <Alerta tipo="erro">{erroAcao}</Alerta>}
      {sucesso && <Alerta tipo="sucesso">{sucesso}</Alerta>}

      {carregando && <Carregando />}
      {erro && <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />}

      {pronto && itens.length === 0 && (
        <Alerta tipo="info">Nenhuma encomenda elegível para esta viagem no momento.</Alerta>
      )}

      {pronto && itens.length > 0 && (
        <>
          <ul className="associar__lista" aria-label="Encomendas elegíveis">
            {itens.map((e) => (
              <li key={e.id} className="associar__item">
                <span className="associar__info">
                  <strong>{e.codigo_rastreio}</strong>
                  <span>{e.descricao}</span>
                  <small className="texto-suave">
                    Destino: {e.destino_nome ?? '—'} · {e.destinatario.nome} · CPF{' '}
                    {mascararCpf(e.destinatario.cpf)}
                  </small>
                </span>
                <StatusBadge status={e.status} />
                <button
                  type="button"
                  className="btn btn--primario"
                  onClick={() => associar(e)}
                  disabled={emCurso !== null}
                >
                  {emCurso === e.id ? 'Associando...' : 'Associar'}
                </button>
              </li>
            ))}
          </ul>

          {dados.total > itens.length && (
            <p className="campo__ajuda">
              Mostrando {itens.length} de {dados.total} encomendas elegíveis. Associe estas para ver as próximas.
            </p>
          )}
        </>
      )}

      <div className="modal__acoes">
        <button type="button" className="btn btn--contorno" onClick={aoFechar} disabled={emCurso !== null}>
          Fechar
        </button>
      </div>
    </Modal>
  )
}
