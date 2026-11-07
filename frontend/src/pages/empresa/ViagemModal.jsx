import { useState } from 'react'
import Alerta from '../../components/Alerta'
import CampoSelecao from '../../components/CampoSelecao'
import CampoTexto from '../../components/CampoTexto'
import Modal from '../../components/Modal'
import { programarViagem } from '../../services/viagens'
import { dataManausParaApi, validarViagem } from '../../utils/viagem'

// Programar viagem. `embarcacoes` e `rotas` são as listas completas; só embarcações ativas são
// oferecidas (regra só da tela: o backend aceita embarcação inativa). `aoProgramada` recebe a viagem criada.
export default function ViagemModal({ embarcacoes, rotas, aoFechar, aoProgramada }) {
  const ativas = embarcacoes.filter((e) => e.ativa)
  const semOpcoes = ativas.length === 0 || rotas.length === 0

  const [campos, setCampos] = useState({ embarcacaoId: '', rotaId: '', dataSaida: '' })
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState('')
  const [enviando, setEnviando] = useState(false)

  function alterar(campo, valor) {
    setCampos((atual) => ({ ...atual, [campo]: valor }))
    setErros((atual) => ({ ...atual, [campo]: undefined }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    setErroGeral('')

    const errosValidacao = validarViagem(campos)
    setErros(errosValidacao)
    if (Object.keys(errosValidacao).length > 0) return

    setEnviando(true)
    try {
      const nova = await programarViagem({
        embarcacaoId: Number(campos.embarcacaoId),
        rotaId: Number(campos.rotaId),
        dataSaida: dataManausParaApi(campos.dataSaida),
      })

      aoProgramada(nova)
    } catch (erro) {
      const errosApi = {}
      for (const [campoApi, campo] of [
        ['embarcacao_id', 'embarcacaoId'],
        ['rota_id', 'rotaId'],
        ['data_saida', 'dataSaida'],
      ]) {
        if (erro.erros?.[campoApi]) errosApi[campo] = erro.erros[campoApi]
      }

      setErros(errosApi)
      if (Object.keys(errosApi).length === 0) setErroGeral(erro.message)
      setEnviando(false)
    }
  }

  return (
    <Modal titulo="Programar viagem" aoFechar={aoFechar} bloqueado={enviando}>
      <form onSubmit={enviar} noValidate>
        {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}

        {ativas.length === 0 && (
          <Alerta tipo="info">
            Não há embarcação ativa. Peça a um administrador para cadastrar ou ativar uma embarcação.
          </Alerta>
        )}
        {rotas.length === 0 && (
          <Alerta tipo="info">Não há rota cadastrada. Peça a um administrador para cadastrar uma rota.</Alerta>
        )}

        <CampoSelecao
          rotulo="Embarcação"
          value={campos.embarcacaoId}
          onChange={(e) => alterar('embarcacaoId', e.target.value)}
          erro={erros.embarcacaoId}
          disabled={ativas.length === 0}
        >
          <option value="">Escolha a embarcação</option>
          {ativas.map((e) => (
            <option key={e.id} value={e.id}>
              {e.nome} (capacidade {e.capacidade})
            </option>
          ))}
        </CampoSelecao>

        <CampoSelecao
          rotulo="Rota"
          value={campos.rotaId}
          onChange={(e) => alterar('rotaId', e.target.value)}
          erro={erros.rotaId}
          disabled={rotas.length === 0}
        >
          <option value="">Escolha a rota</option>
          {rotas.map((r) => (
            <option key={r.id} value={r.id}>
              {r.nome}
            </option>
          ))}
        </CampoSelecao>

        <CampoTexto
          rotulo="Saída de Manaus"
          type="datetime-local"
          value={campos.dataSaida}
          onChange={(e) => alterar('dataSaida', e.target.value)}
          erro={erros.dataSaida}
          ajuda="Data e horário de Manaus."
        />

        <div className="modal__acoes">
          <button type="button" className="btn btn--contorno" onClick={aoFechar} disabled={enviando}>
            Cancelar
          </button>
          <button type="submit" className="btn btn--primario" disabled={enviando || semOpcoes}>
            {enviando ? 'Programando...' : 'Programar viagem'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
