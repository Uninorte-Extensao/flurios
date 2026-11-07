import { ArrowLeft, Repeat, SearchX, Ship } from 'lucide-react'
import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import CampoSelecao from '../../components/CampoSelecao'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import LinhaDoTempo from '../../components/LinhaDoTempo'
import StatusBadge from '../../components/StatusBadge'
import { useCarga } from '../../hooks/useCarga'
import {
  atualizarStatusEncomenda,
  buscarRastreio,
  listarEncomendasDaEmpresa,
} from '../../services/encomendas'
import { mascararCpf } from '../../utils/cpf'
import { formatarData } from '../../utils/data'
import {
  motivoNaoAssociar,
  podeAssociar,
  podeRealocar,
  ROTULOS_STATUS,
  statusSeguintes,
} from '../../utils/gestaoEncomenda'
import AssociarViagemModal from './AssociarViagemModal'
import './Gestao.css'
import './Encomendas.css'

const ORIGEM = 'Manaus'

// A busca por código é parcial; a encomenda é a de código igual. `encomenda: null` = não encontrada.
async function carregarDetalhe(codigo) {
  try {
    const [lista, rastreio] = await Promise.all([
      listarEncomendasDaEmpresa({ busca: codigo, limite: 100 }),
      buscarRastreio(codigo),
    ])
    const encomenda = lista.itens.find((i) => i.codigo_rastreio.toUpperCase() === codigo.toUpperCase())

    return { encomenda: encomenda ?? null, rastreio }
  } catch (erro) {
    if (erro.status === 404) return { encomenda: null, rastreio: null }
    throw erro
  }
}

function MudarStatus({ encomenda, aoMudar }) {
  const opcoes = statusSeguintes(encomenda.status)
  const [novoStatus, setNovoStatus] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (opcoes.length === 0) {
    return (
      <Card titulo="Mudar status">
        <p className="texto-suave">Esta encomenda já foi entregue e não aceita mais mudanças de status.</p>
      </Card>
    )
  }

  async function enviar(evento) {
    evento.preventDefault()
    setErro('')

    if (!novoStatus) {
      setErro('Escolha o novo status.')
      return
    }

    setEnviando(true)
    try {
      await aoMudar(novoStatus)
      setNovoStatus('')
    } catch (falha) {
      setErro(falha.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Card titulo="Mudar status">
      <form onSubmit={enviar} noValidate>
        {erro && <Alerta tipo="erro">{erro}</Alerta>}

        <Alerta tipo="info">
          Cada mudança de status gera uma <strong>movimentação</strong> no histórico da encomenda, visível
          para o cliente.
        </Alerta>

        <CampoSelecao
          rotulo="Novo status"
          value={novoStatus}
          onChange={(e) => {
            setNovoStatus(e.target.value)
            setErro('')
          }}
          ajuda="“Entregue” é registrado pela retirada, não por aqui."
        >
          <option value="">Escolha o novo status</option>
          {opcoes.map((status) => (
            <option key={status} value={status}>
              {ROTULOS_STATUS[status]}
            </option>
          ))}
        </CampoSelecao>

        <button type="submit" className="btn btn--primario btn--bloco" disabled={enviando}>
          {enviando ? 'Atualizando...' : 'Atualizar status'}
        </button>
      </form>
    </Card>
  )
}

function CardViagem({ encomenda, realocando, aoAssociar, aoRealocar }) {
  const viagem = encomenda.viagem_ativa

  return (
    <Card titulo="Viagem">
      {viagem ? (
        <>
          <p>
            Associada à <Link to={`/empresa/viagens/${viagem.id}`}>viagem #{viagem.id}</Link>{' '}
            <StatusBadge status={viagem.status} />
          </p>
          <p className="campo__ajuda encomenda__nota">
            Para trocar de viagem, remova a encomenda na tela da viagem (só viagem programada permite).
          </p>
        </>
      ) : podeAssociar(encomenda) ? (
        <>
          <p className="texto-suave encomenda__texto">Esta encomenda ainda não está em nenhuma viagem.</p>
          <button type="button" className="btn btn--primario btn--bloco" onClick={aoAssociar}>
            <Ship size={16} aria-hidden="true" />
            Associar à viagem
          </button>
        </>
      ) : podeRealocar(encomenda) ? (
        <>
          <p className="texto-suave encomenda__texto">
            A viagem desta encomenda não está mais ativa. Realocar devolve a encomenda para{' '}
            <strong>Recebida</strong> e abre a escolha da nova viagem.
          </p>
          <button
            type="button"
            className="btn btn--primario btn--bloco"
            onClick={aoRealocar}
            disabled={realocando}
          >
            <Repeat size={16} aria-hidden="true" />
            {realocando ? 'Realocando...' : 'Realocar'}
          </button>
        </>
      ) : (
        <p className="texto-suave">{motivoNaoAssociar(encomenda)}</p>
      )}
    </Card>
  )
}

function Detalhe({ codigo }) {
  const carregar = useCallback(() => carregarDetalhe(codigo), [codigo])
  const { carregando, erro, dados, recarregar, definirDados } = useCarga(carregar)

  const [aviso, setAviso] = useState('')
  const [erroAcao, setErroAcao] = useState('')
  const [associando, setAssociando] = useState(false)
  const [realocando, setRealocando] = useState(false)

  const voltar = (
    <Link to="/empresa/encomendas" className="encomenda__voltar">
      <ArrowLeft size={16} aria-hidden="true" />
      Voltar para encomendas
    </Link>
  )

  // Confere a encomenda e o histórico sem voltar ao "Carregando...".
  const atualizarEmSilencio = useCallback(async () => {
    try {
      const atual = await carregarDetalhe(codigo)
      definirDados(() => atual)
    } catch {
      // Mantém o que já está na tela; um erro novo aparece na próxima ação.
    }
  }, [codigo, definirDados])

  if (carregando) return <Carregando />

  if (erro) {
    return (
      <>
        {voltar}
        <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />
      </>
    )
  }

  if (!dados.encomenda) {
    return (
      <>
        {voltar}
        <Card>
          <div className="gestao__vazio">
            <SearchX size={36} aria-hidden="true" />
            <h1>Encomenda não encontrada</h1>
            <p className="texto-suave encomenda__texto">
              Não encontramos nenhuma encomenda com o código <strong>{codigo}</strong>.
            </p>
          </div>
        </Card>
      </>
    )
  }

  const { encomenda, rastreio } = dados

  async function mudarStatus(novoStatus) {
    setErroAcao('')
    setAviso('')
    await atualizarStatusEncomenda(encomenda.id, novoStatus)
    await atualizarEmSilencio()
    setAviso(`Status atualizado para ${ROTULOS_STATUS[novoStatus]}. Movimentação registrada no histórico.`)
  }

  async function realocar() {
    setErroAcao('')
    setAviso('')
    setRealocando(true)
    try {
      await atualizarStatusEncomenda(encomenda.id, 'recebida')
      await atualizarEmSilencio()
      setAviso('Encomenda devolvida para Recebida. Escolha a nova viagem.')
      setAssociando(true)
    } catch (falha) {
      setErroAcao(falha.message)
    } finally {
      setRealocando(false)
    }
  }

  function aoAssociada(viagemId) {
    setAssociando(false)
    setErroAcao('')
    setAviso(`Encomenda associada à viagem #${viagemId}.`)
    atualizarEmSilencio()
  }

  return (
    <>
      {voltar}

      <div className="gestao__topo">
        <div>
          <h1 className="pagina__titulo">Encomenda #{encomenda.codigo_rastreio}</h1>
          <p className="pagina__subtitulo">Dados, histórico e ações desta encomenda.</p>
        </div>
        <StatusBadge status={encomenda.status} />
      </div>

      {erroAcao && <Alerta tipo="erro">{erroAcao}</Alerta>}
      {aviso && <Alerta tipo="sucesso">{aviso}</Alerta>}

      <div className="encomenda__corpo">
        <div className="encomenda__principal">
          <Card titulo="Dados da encomenda">
            <dl className="encomenda__dados">
              <div>
                <dt>Status</dt>
                <dd>
                  <StatusBadge status={encomenda.status} />
                </dd>
              </div>
              <div>
                <dt>Origem</dt>
                <dd>{ORIGEM}</dd>
              </div>
              <div>
                <dt>Destino</dt>
                <dd>{encomenda.destino_nome ?? '—'}</dd>
              </div>
              <div>
                <dt>Destinatário</dt>
                <dd>
                  {encomenda.destinatario.nome} · CPF {mascararCpf(encomenda.destinatario.cpf)}
                </dd>
              </div>
              <div>
                <dt>Descrição</dt>
                <dd>{encomenda.descricao}</dd>
              </div>
              <div>
                <dt>Cadastrada em</dt>
                <dd>{formatarData(encomenda.criado_em)}</dd>
              </div>
              <div>
                <dt>Viagem ativa</dt>
                <dd>
                  {encomenda.viagem_ativa ? (
                    <Link to={`/empresa/viagens/${encomenda.viagem_ativa.id}`}>
                      Viagem #{encomenda.viagem_ativa.id}
                    </Link>
                  ) : (
                    'Nenhuma'
                  )}
                </dd>
              </div>
            </dl>
          </Card>

          <Card titulo="Linha do tempo">
            <LinhaDoTempo historico={rastreio.historico} />
          </Card>
        </div>

        <div className="encomenda__lateral">
          <MudarStatus key={encomenda.status} encomenda={encomenda} aoMudar={mudarStatus} />
          <CardViagem
            encomenda={encomenda}
            realocando={realocando}
            aoAssociar={() => {
              setAviso('')
              setAssociando(true)
            }}
            aoRealocar={realocar}
          />
        </div>
      </div>

      {associando && (
        <AssociarViagemModal
          encomenda={encomenda}
          aoFechar={() => setAssociando(false)}
          aoAssociada={aoAssociada}
        />
      )}
    </>
  )
}

export default function DetalheEncomendaEmpresa() {
  const { codigo } = useParams()

  // `key` zera o estado ao trocar de código.
  return <Detalhe key={codigo} codigo={codigo} />
}
