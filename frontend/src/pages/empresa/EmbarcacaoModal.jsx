import { useState } from 'react'
import Alerta from '../../components/Alerta'
import CampoTexto from '../../components/CampoTexto'
import Modal from '../../components/Modal'
import { cadastrarEmbarcacao, editarEmbarcacao } from '../../services/embarcacoes'
import { lerInteiroPositivo, NOME_MAXIMO, validarEmbarcacao } from '../../utils/frota'

// Cadastro (embarcacao = null) e edição de embarcação. `aoSalvar` recebe a embarcação devolvida pela API.
export default function EmbarcacaoModal({ embarcacao, aoFechar, aoSalvar }) {
  const editando = Boolean(embarcacao)

  const [campos, setCampos] = useState({
    nome: embarcacao?.nome ?? '',
    capacidade: embarcacao ? String(embarcacao.capacidade) : '',
    ativa: embarcacao?.ativa ?? true,
  })
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

    const errosValidacao = validarEmbarcacao(campos)
    setErros(errosValidacao)
    if (Object.keys(errosValidacao).length > 0) return

    const dados = { nome: campos.nome.trim(), capacidade: lerInteiroPositivo(campos.capacidade) }

    setEnviando(true)
    try {
      const salva = editando
        ? await editarEmbarcacao(embarcacao.id, { ...dados, ativa: campos.ativa })
        : await cadastrarEmbarcacao(dados)

      aoSalvar(salva, editando)
    } catch (erro) {
      const errosApi = {}
      for (const campo of ['nome', 'capacidade']) {
        if (erro.erros?.[campo]) errosApi[campo] = erro.erros[campo]
      }

      setErros(errosApi)
      if (Object.keys(errosApi).length === 0) setErroGeral(erro.message)
      setEnviando(false)
    }
  }

  return (
    <Modal
      titulo={editando ? 'Editar embarcação' : 'Nova embarcação'}
      aoFechar={aoFechar}
      bloqueado={enviando}
    >
      <form onSubmit={enviar} noValidate>
        {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}

        <CampoTexto
          rotulo="Nome da embarcação"
          value={campos.nome}
          onChange={(e) => alterar('nome', e.target.value)}
          erro={erros.nome}
          maxLength={NOME_MAXIMO}
          placeholder="Ex.: M/V Solimões"
          autoComplete="off"
        />

        <CampoTexto
          rotulo="Capacidade (nº de encomendas)"
          type="number"
          inputMode="numeric"
          min="1"
          step="1"
          value={campos.capacidade}
          onChange={(e) => alterar('capacidade', e.target.value)}
          erro={erros.capacidade}
          ajuda="Quantas encomendas a embarcação comporta por viagem."
        />

        {editando && (
          <div className="campo campo--caixa">
            <input
              id="embarcacao-ativa"
              type="checkbox"
              checked={campos.ativa}
              onChange={(e) => alterar('ativa', e.target.checked)}
            />
            <label htmlFor="embarcacao-ativa">Embarcação ativa</label>
          </div>
        )}

        <div className="modal__acoes">
          <button type="button" className="btn btn--contorno" onClick={aoFechar} disabled={enviando}>
            Cancelar
          </button>
          <button type="submit" className="btn btn--primario" disabled={enviando}>
            {enviando ? 'Salvando...' : editando ? 'Salvar alterações' : 'Cadastrar embarcação'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
