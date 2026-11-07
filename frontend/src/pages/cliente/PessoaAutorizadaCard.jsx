import { UserRound } from 'lucide-react'
import { useEffect, useState } from 'react'
import Alerta from '../../components/Alerta'
import CampoTexto from '../../components/CampoTexto'
import Card from '../../components/Card'
import { buscarPessoaAutorizada, definirPessoaAutorizada } from '../../services/encomendas'
import { formatarCpfDigitado, mascararCpf, somenteDigitos } from '../../utils/cpf'
import { podeDefinirPessoaAutorizada, validarPessoaAutorizada } from '../../utils/encomenda'

const FORMULARIO_VAZIO = { usarDestinatario: false, nome: '', cpf: '' }

// Card "Retirada": mostra a pessoa autorizada (CPF sempre mascarado) e permite cadastrar ou trocar.
export default function PessoaAutorizadaCard({ encomenda, destinatario }) {
  const [carga, setCarga] = useState({ carregando: true, erro: '', pessoa: null })
  const [editando, setEditando] = useState(false)
  const [campos, setCampos] = useState(FORMULARIO_VAZIO)
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [salva, setSalva] = useState(false)

  useEffect(() => {
    let ativo = true

    buscarPessoaAutorizada(encomenda.id)
      .then((pessoa) => {
        if (ativo) setCarga({ carregando: false, erro: '', pessoa })
      })
      .catch((erro) => {
        if (ativo) setCarga({ carregando: false, erro: erro.message, pessoa: null })
      })

    return () => {
      ativo = false
    }
  }, [encomenda.id])

  const { carregando, erro, pessoa } = carga
  const podeDefinir = !carregando && !erro && podeDefinirPessoaAutorizada(encomenda.status, Boolean(pessoa))

  function abrir() {
    setCampos(FORMULARIO_VAZIO)
    setErros({})
    setErroGeral('')
    setSalva(false)
    setEditando(true)
  }

  function alterar(evento) {
    const { name, value, type, checked } = evento.target
    let novoValor = value
    if (type === 'checkbox') novoValor = checked
    else if (name === 'cpf') novoValor = formatarCpfDigitado(value)

    setCampos((atual) => ({ ...atual, [name]: novoValor }))
    setErros((atual) => ({ ...atual, [name]: undefined }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    setErroGeral('')

    const encontrados = validarPessoaAutorizada(campos)
    setErros(encontrados)
    if (Object.keys(encontrados).length > 0) return

    setEnviando(true)
    try {
      const nova = await definirPessoaAutorizada(encomenda.id, {
        destinatarioEAPessoa: campos.usarDestinatario,
        nome: campos.nome.trim(),
        cpf: somenteDigitos(campos.cpf),
      })
      setCarga({ carregando: false, erro: '', pessoa: nova })
      setEditando(false)
      setSalva(true)
    } catch (falha) {
      const porCampo = {}
      for (const campo of ['nome', 'cpf']) {
        if (falha.erros?.[campo]) porCampo[campo] = falha.erros[campo]
      }
      setErros(porCampo)
      if (Object.keys(porCampo).length === 0) setErroGeral(falha.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Card titulo="Retirada">
      {carregando && <p className="texto-suave">Carregando...</p>}
      {erro && <Alerta tipo="erro">{erro}</Alerta>}
      {salva && <Alerta tipo="sucesso">Pessoa autorizada salva.</Alerta>}

      {!carregando && !erro && !editando && (
        <div className="detalhe__pessoa">
          <UserRound size={20} aria-hidden="true" />
          {pessoa ? (
            <div>
              <small className="texto-suave">Pessoa autorizada:</small>
              <strong>{pessoa.nome}</strong>
              <small className="texto-suave">CPF {mascararCpf(pessoa.cpf)}</small>
            </div>
          ) : (
            <p className="texto-suave">
              Nenhuma pessoa autorizada cadastrada. Ela é obrigatória para a retirada da encomenda.
            </p>
          )}
        </div>
      )}

      {podeDefinir && !editando && (
        <button type="button" className="btn btn--contorno btn--bloco detalhe__botao" onClick={abrir}>
          {pessoa ? 'Trocar pessoa autorizada' : 'Cadastrar pessoa autorizada'}
        </button>
      )}

      {!carregando && !erro && !podeDefinir && pessoa && encomenda.status === 'a_retirar' && (
        <p className="texto-suave detalhe__nota">
          A encomenda já está a retirar: a pessoa autorizada não pode mais ser trocada.
        </p>
      )}

      {editando && (
        <form onSubmit={enviar} noValidate>
          {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}

          {destinatario && (
            <label className="detalhe__opcao">
              <input
                type="checkbox"
                name="usarDestinatario"
                checked={campos.usarDestinatario}
                onChange={alterar}
              />
              <span>O destinatário ({destinatario.nome}) é quem vai retirar</span>
            </label>
          )}

          {!campos.usarDestinatario && (
            <>
              <CampoTexto
                rotulo="Nome da pessoa autorizada"
                name="nome"
                autoComplete="off"
                value={campos.nome}
                onChange={alterar}
                erro={erros.nome}
              />
              <CampoTexto
                rotulo="CPF da pessoa autorizada"
                name="cpf"
                inputMode="numeric"
                autoComplete="off"
                placeholder="000.000.000-00"
                value={campos.cpf}
                onChange={alterar}
                erro={erros.cpf}
              />
            </>
          )}

          <div className="detalhe__acoes">
            <button type="submit" className="btn btn--primario" disabled={enviando}>
              {enviando ? 'Salvando...' : 'Salvar'}
            </button>
            <button
              type="button"
              className="btn btn--contorno"
              onClick={() => setEditando(false)}
              disabled={enviando}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}
    </Card>
  )
}
