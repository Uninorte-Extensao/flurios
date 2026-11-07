import { useState } from 'react'
import Alerta from '../../components/Alerta'
import CampoTexto from '../../components/CampoTexto'
import Modal from '../../components/Modal'
import { cadastrarRota } from '../../services/rotas'
import { NOME_MAXIMO, ORIGEM_NOME, validarRota } from '../../utils/frota'

// Cadastro de rota. `aoSalvar` recebe a rota criada; as paradas são cadastradas no detalhe dela.
export default function RotaModal({ aoFechar, aoSalvar }) {
  const [nome, setNome] = useState('')
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setErroGeral('')

    const errosValidacao = validarRota({ nome })
    setErros(errosValidacao)
    if (Object.keys(errosValidacao).length > 0) return

    setEnviando(true)
    try {
      aoSalvar(await cadastrarRota({ nome: nome.trim() }))
    } catch (erro) {
      if (erro.erros?.nome) setErros({ nome: erro.erros.nome })
      else setErroGeral(erro.message)
      setEnviando(false)
    }
  }

  return (
    <Modal titulo="Nova rota" aoFechar={aoFechar} bloqueado={enviando}>
      <form onSubmit={enviar} noValidate>
        {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}

        <CampoTexto
          rotulo="Nome da rota"
          value={nome}
          onChange={(e) => {
            setNome(e.target.value)
            setErros({})
          }}
          erro={erros.nome}
          maxLength={NOME_MAXIMO}
          placeholder={`Ex.: ${ORIGEM_NOME} - Coari`}
          autoComplete="off"
          ajuda="Depois de criar a rota, você cadastra as paradas dela."
        />

        <div className="modal__acoes">
          <button type="button" className="btn btn--contorno" onClick={aoFechar} disabled={enviando}>
            Cancelar
          </button>
          <button type="submit" className="btn btn--primario" disabled={enviando}>
            {enviando ? 'Salvando...' : 'Cadastrar rota'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
