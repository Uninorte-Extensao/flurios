import { useState } from 'react'
import Alerta from '../../components/Alerta'
import Modal from '../../components/Modal'
import { desassociarEncomenda } from '../../services/viagens'

// Tira uma encomenda de uma viagem programada. `aoRemovida()` roda no sucesso; nos 409/404
// `aoConflito()` pede que a tela da viagem confira tudo de novo (a mensagem fica na própria janela).
export default function DesassociarEncomendaModal({ viagem, encomenda, aoFechar, aoRemovida, aoConflito }) {
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function confirmar() {
    setErro('')
    setEnviando(true)
    try {
      await desassociarEncomenda(viagem.id, encomenda.id)
      aoRemovida()
    } catch (falha) {
      setErro(falha.message)
      setEnviando(false)
      if (falha.status === 409 || falha.status === 404) aoConflito()
    }
  }

  return (
    <Modal titulo="Remover da viagem" aoFechar={aoFechar} bloqueado={enviando}>
      {erro && <Alerta tipo="erro">{erro}</Alerta>}

      <p>
        Remover a encomenda <strong>{encomenda.codigo_rastreio}</strong> da viagem #{viagem.id}?
      </p>
      <Alerta tipo="info">
        A encomenda volta para <strong>Recebida</strong> e a mudança gera uma movimentação no histórico.
        Depois disso ela pode ser associada a outra viagem.
      </Alerta>

      <div className="modal__acoes">
        <button type="button" className="btn btn--contorno" onClick={aoFechar} disabled={enviando}>
          Voltar
        </button>
        <button type="button" className="btn btn--perigo" onClick={confirmar} disabled={enviando}>
          {enviando ? 'Removendo...' : 'Remover da viagem'}
        </button>
      </div>
    </Modal>
  )
}
