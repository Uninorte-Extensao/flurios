import { Check, Copy } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import CampoAreaTexto from '../../components/CampoAreaTexto'
import CampoSelecao from '../../components/CampoSelecao'
import CampoTexto from '../../components/CampoTexto'
import Card from '../../components/Card'
import Carregando from '../../components/Carregando'
import StatusBadge from '../../components/StatusBadge'
import {
  cadastrarDestinatario,
  criarEncomenda,
  listarDestinatarios,
  listarDestinos,
} from '../../services/encomendas'
import { formatarCpfDigitado, mascararCpf, somenteDigitos } from '../../utils/cpf'
import {
  agruparDestinosPorRota,
  DESCRICAO_MAXIMA,
  NOVO_DESTINATARIO,
  validarEncomenda,
} from '../../utils/encomenda'
import { formatarTelefoneDigitado } from '../../utils/telefone'
import './NovaEncomenda.css'

// A origem é sempre Manaus (parada de ordem 1 das rotas); não é enviada à API.
const ORIGEM = 'Manaus'

const CAMPOS_VAZIOS = {
  destinoId: '',
  destinatarioId: '',
  descricao: '',
  destNome: '',
  destCpf: '',
  destTelefone: '',
  destEndereco: '',
  destMunicipio: '',
}

// Nome do campo na API -> nome do campo no formulário.
const CAMPOS_DA_API = {
  parada_destino_id: 'destinoId',
  destinatario_id: 'destinatarioId',
  descricao: 'descricao',
  nome: 'destNome',
  cpf: 'destCpf',
  telefone: 'destTelefone',
  endereco: 'destEndereco',
  municipio: 'destMunicipio',
}

function errosDaApi(erro) {
  const erros = {}
  for (const [campoApi, mensagem] of Object.entries(erro.erros ?? {})) {
    if (CAMPOS_DA_API[campoApi]) erros[CAMPOS_DA_API[campoApi]] = mensagem
  }
  return erros
}

function CodigoGerado({ encomenda, destinatario, aoCadastrarOutra }) {
  const [copiado, setCopiado] = useState(false)
  const [erroCopia, setErroCopia] = useState(false)

  async function copiar() {
    try {
      await navigator.clipboard.writeText(encomenda.codigo_rastreio)
      setCopiado(true)
      setErroCopia(false)
    } catch {
      setCopiado(false)
      setErroCopia(true)
    }
  }

  return (
    <Card titulo="Encomenda cadastrada" className="nova-encomenda__sucesso">
      <Alerta tipo="sucesso">
        Pronto! Guarde o código de rastreio abaixo para acompanhar sua encomenda.
      </Alerta>

      <p className="texto-suave">Código de rastreio</p>
      <p className="codigo-rastreio">
        {encomenda.codigo_rastreio}
      </p>

      <div className="nova-encomenda__acoes">
        <button type="button" className="btn btn--contorno" onClick={copiar}>
          {copiado ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
          {copiado ? 'Código copiado' : 'Copiar código'}
        </button>
        <Link
          to={`/cliente/encomendas/${encomenda.codigo_rastreio}`}
          className="btn btn--primario"
        >
          Acompanhar encomenda
        </Link>
      </div>
      {erroCopia && (
        <p className="campo__erro" role="alert">
          Não foi possível copiar automaticamente. Selecione o código e copie manualmente.
        </p>
      )}

      <dl className="resumo">
        <div>
          <dt>Origem</dt>
          <dd>{ORIGEM}</dd>
        </div>
        <div>
          <dt>Destino</dt>
          <dd>{encomenda.destino_nome}</dd>
        </div>
        {destinatario && (
          <div>
            <dt>Destinatário</dt>
            <dd>
              {destinatario.nome} · CPF {mascararCpf(destinatario.cpf)}
            </dd>
          </div>
        )}
        <div>
          <dt>Descrição</dt>
          <dd>{encomenda.descricao}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>
            <StatusBadge status={encomenda.status} />
          </dd>
        </div>
      </dl>

      <button type="button" className="btn btn--contorno" onClick={aoCadastrarOutra}>
        Cadastrar outra encomenda
      </button>
    </Card>
  )
}

export default function NovaEncomenda() {
  const [carga, setCarga] = useState({ carregando: true, erro: '', destinos: [], destinatarios: [] })
  const [campos, setCampos] = useState(CAMPOS_VAZIOS)
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [criada, setCriada] = useState(null)

  useEffect(() => {
    let ativo = true

    Promise.all([listarDestinos(), listarDestinatarios()])
      .then(([destinos, destinatarios]) => {
        if (!ativo) return
        setCarga({ carregando: false, erro: '', destinos, destinatarios })
        // Sem destinatários salvos, o formulário já abre pedindo os dados de um novo.
        if (destinatarios.length === 0) {
          setCampos((atual) => ({ ...atual, destinatarioId: NOVO_DESTINATARIO }))
        }
      })
      .catch((erro) => {
        if (ativo) setCarga({ carregando: false, erro: erro.message, destinos: [], destinatarios: [] })
      })

    return () => {
      ativo = false
    }
  }, [])

  function alterar(evento) {
    const { name, value } = evento.target
    const formatadores = { destCpf: formatarCpfDigitado, destTelefone: formatarTelefoneDigitado }
    const novoValor = formatadores[name] ? formatadores[name](value) : value

    setCampos((atual) => ({ ...atual, [name]: novoValor }))
    setErros((atual) => ({ ...atual, [name]: undefined }))
  }

  function limpar() {
    setCriada(null)
    setErros({})
    setErroGeral('')
    setCampos({
      ...CAMPOS_VAZIOS,
      destinatarioId: carga.destinatarios.length === 0 ? NOVO_DESTINATARIO : '',
    })
  }

  async function enviar(evento) {
    evento.preventDefault()
    setErroGeral('')

    const errosEncontrados = validarEncomenda(campos)
    setErros(errosEncontrados)
    if (Object.keys(errosEncontrados).length > 0) return

    setEnviando(true)
    let destinatarioId = campos.destinatarioId

    try {
      if (destinatarioId === NOVO_DESTINATARIO) {
        let novo
        try {
          novo = await cadastrarDestinatario({
            nome: campos.destNome.trim(),
            cpf: somenteDigitos(campos.destCpf),
            telefone: somenteDigitos(campos.destTelefone),
            endereco: campos.destEndereco.trim(),
            municipio: campos.destMunicipio.trim(),
          })
        } catch (erro) {
          const porCampo = errosDaApi(erro)
          setErros(porCampo)
          if (Object.keys(porCampo).length === 0) setErroGeral(erro.message)
          return
        }

        // Já fica salvo e selecionado: se a encomenda falhar, tentar de novo não duplica o destinatário.
        destinatarioId = String(novo.id)
        setCarga((atual) => ({ ...atual, destinatarios: [...atual.destinatarios, novo] }))
        setCampos((atual) => ({
          ...atual,
          destinatarioId,
          destNome: '',
          destCpf: '',
          destTelefone: '',
          destEndereco: '',
          destMunicipio: '',
        }))
      }

      try {
        const encomenda = await criarEncomenda({
          destinatarioId: Number(destinatarioId),
          paradaDestinoId: Number(campos.destinoId),
          descricao: campos.descricao.trim(),
        })
        setCriada({ encomenda, destinatarioId: Number(destinatarioId) })
      } catch (erro) {
        const porCampo = errosDaApi(erro)
        setErros(porCampo)
        if (Object.keys(porCampo).length === 0) setErroGeral(erro.message)
      }
    } finally {
      setEnviando(false)
    }
  }

  if (carga.carregando) return <Carregando />

  if (criada) {
    return (
      <>
        <h1 className="pagina__titulo">Nova encomenda</h1>
        <p className="pagina__subtitulo">Sua encomenda foi registrada no sistema.</p>
        <CodigoGerado
          encomenda={criada.encomenda}
          destinatario={carga.destinatarios.find((d) => d.id === criada.destinatarioId)}
          aoCadastrarOutra={limpar}
        />
      </>
    )
  }

  const grupos = agruparDestinosPorRota(carga.destinos)
  const novoDestinatario = campos.destinatarioId === NOVO_DESTINATARIO

  return (
    <>
      <h1 className="pagina__titulo">Nova encomenda</h1>
      <p className="pagina__subtitulo">Informe o destino, o destinatário e o que será enviado.</p>

      {carga.erro && <Alerta tipo="erro">{carga.erro}</Alerta>}
      {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}

      <div className="nova-encomenda">
        <Card>
          <form onSubmit={enviar} noValidate>
            <h2 className="nova-encomenda__secao">Trajeto</h2>
            <div className="nova-encomenda__linha">
              <CampoTexto rotulo="Origem" name="origem" value={ORIGEM} readOnly />
              <CampoSelecao
                rotulo="Destino"
                name="destinoId"
                value={campos.destinoId}
                onChange={alterar}
                erro={erros.destinoId}
              >
                <option value="">Selecione o destino</option>
                {grupos.map((grupo) => (
                  <optgroup key={grupo.rota} label={grupo.rota}>
                    {grupo.destinos.map((destino) => (
                      <option key={destino.id} value={destino.id}>
                        {destino.nome}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </CampoSelecao>
            </div>

            <h2 className="nova-encomenda__secao">Destinatário</h2>
            <CampoSelecao
              rotulo="Quem vai receber"
              name="destinatarioId"
              value={campos.destinatarioId}
              onChange={alterar}
              erro={erros.destinatarioId}
            >
              <option value="">Selecione o destinatário</option>
              {carga.destinatarios.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.nome} · {d.municipio} · CPF {mascararCpf(d.cpf)}
                </option>
              ))}
              <option value={NOVO_DESTINATARIO}>+ Cadastrar novo destinatário</option>
            </CampoSelecao>

            {novoDestinatario && (
              <>
                <CampoTexto
                  rotulo="Nome do destinatário"
                  name="destNome"
                  autoComplete="off"
                  value={campos.destNome}
                  onChange={alterar}
                  erro={erros.destNome}
                />
                <div className="nova-encomenda__linha">
                  <CampoTexto
                    rotulo="CPF do destinatário"
                    name="destCpf"
                    inputMode="numeric"
                    autoComplete="off"
                    placeholder="000.000.000-00"
                    value={campos.destCpf}
                    onChange={alterar}
                    erro={erros.destCpf}
                  />
                  <CampoTexto
                    rotulo="Telefone do destinatário"
                    name="destTelefone"
                    type="tel"
                    autoComplete="off"
                    placeholder="(92) 99999-0000"
                    value={campos.destTelefone}
                    onChange={alterar}
                    erro={erros.destTelefone}
                  />
                </div>
                <div className="nova-encomenda__linha">
                  <CampoTexto
                    rotulo="Endereço"
                    name="destEndereco"
                    autoComplete="off"
                    value={campos.destEndereco}
                    onChange={alterar}
                    erro={erros.destEndereco}
                  />
                  <CampoTexto
                    rotulo="Município"
                    name="destMunicipio"
                    autoComplete="off"
                    value={campos.destMunicipio}
                    onChange={alterar}
                    erro={erros.destMunicipio}
                  />
                </div>
              </>
            )}

            <h2 className="nova-encomenda__secao">Encomenda</h2>
            <CampoAreaTexto
              rotulo="Descrição"
              name="descricao"
              maxLength={DESCRICAO_MAXIMA}
              placeholder="Ex.: caixa de ferramentas, 2 sacos de farinha..."
              value={campos.descricao}
              onChange={alterar}
              erro={erros.descricao}
              ajuda={`${campos.descricao.length}/${DESCRICAO_MAXIMA} caracteres`}
            />

            <button
              type="submit"
              className="btn btn--primario btn--bloco"
              disabled={enviando || Boolean(carga.erro)}
            >
              {enviando ? 'Cadastrando...' : 'Cadastrar encomenda'}
            </button>
          </form>
        </Card>

        <Card titulo="Como funciona">
          <ul className="nova-encomenda__dicas texto-suave">
            <li>Toda encomenda sai de {ORIGEM} e tem um único destino.</li>
            <li>
              Para enviar a cidades diferentes, cadastre uma encomenda para cada destino. Cada uma
              recebe seu próprio código de rastreio.
            </li>
            <li>Você acompanha tudo por aqui, usando o código gerado ao final do cadastro.</li>
          </ul>
        </Card>
      </div>
    </>
  )
}
