import { ArrowLeft, MapPin, SearchX } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import Carregando from '../../components/Carregando'
import StatusBadge from '../../components/StatusBadge'
import { buscarEncomenda, buscarRastreio, listarDestinatarios } from '../../services/encomendas'
import { mascararCpf } from '../../utils/cpf'
import { formatarData, formatarDataHora } from '../../utils/data'
import { ordenarHistorico } from '../../utils/encomenda'
import PessoaAutorizadaCard from './PessoaAutorizadaCard'
import './DetalheEncomenda.css'

const ORIGEM = 'Manaus'

function NaoEncontrada({ codigo }) {
  return (
    <Card>
      <div className="detalhe__vazio">
        <SearchX size={36} aria-hidden="true" />
        <h1>Encomenda não encontrada</h1>
        <p className="texto-suave">
          Não encontramos nenhuma encomenda sua com o código <strong>{codigo}</strong>. Confira o
          código ou consulte a lista das suas encomendas.
        </p>
        <Link to="/cliente/encomendas" className="btn btn--primario">
          Ver minhas encomendas
        </Link>
      </div>
    </Card>
  )
}

function LinhaDoTempo({ historico }) {
  const movimentacoes = ordenarHistorico(historico)

  if (movimentacoes.length === 0) {
    return <p className="texto-suave">Ainda não há movimentações registradas.</p>
  }

  return (
    <ol className="linha-do-tempo">
      {movimentacoes.map((m, indice) => (
        <li
          key={m.id}
          className={`linha-do-tempo__item${indice === 0 ? ' linha-do-tempo__item--atual' : ''}`}
        >
          <span className="linha-do-tempo__ponto" aria-hidden="true" />
          <div className="linha-do-tempo__conteudo">
            <StatusBadge status={m.status} />
            {m.parada_nome && (
              <span className="linha-do-tempo__local">
                <MapPin size={14} aria-hidden="true" />
                {m.parada_nome}
              </span>
            )}
            <time className="texto-suave" dateTime={m.criado_em}>
              {formatarDataHora(m.criado_em)}
            </time>
          </div>
        </li>
      ))}
    </ol>
  )
}

function Detalhe({ codigo }) {
  const [estado, setEstado] = useState({
    carregando: true,
    naoEncontrada: false,
    erro: '',
    encomenda: null,
    rastreio: null,
    destinatario: null,
  })
  const [tentativa, setTentativa] = useState(0)

  useEffect(() => {
    let ativo = true

    Promise.all([
      buscarEncomenda(codigo),
      buscarRastreio(codigo),
      // O nome do destinatário é complementar: se falhar, a tela abre mesmo assim.
      listarDestinatarios().catch(() => []),
    ])
      .then(([encomenda, rastreio, destinatarios]) => {
        if (!ativo) return
        const destinatario = destinatarios.find((d) => d.id === encomenda.destinatario_id) ?? null
        setEstado({ carregando: false, naoEncontrada: false, erro: '', encomenda, rastreio, destinatario })
      })
      .catch((erro) => {
        if (!ativo) return
        const naoEncontrada = erro.status === 404
        setEstado({
          carregando: false,
          naoEncontrada,
          erro: naoEncontrada ? '' : erro.message,
          encomenda: null,
          rastreio: null,
          destinatario: null,
        })
      })

    return () => {
      ativo = false
    }
  }, [codigo, tentativa])

  function tentarDeNovo() {
    setEstado((atual) => ({ ...atual, carregando: true, erro: '' }))
    setTentativa((n) => n + 1)
  }

  const { carregando, naoEncontrada, erro, encomenda, rastreio, destinatario } = estado

  if (carregando) return <Carregando />
  if (naoEncontrada) return <NaoEncontrada codigo={codigo} />

  if (erro) {
    return (
      <>
        <Alerta tipo="erro">{erro}</Alerta>
        <button type="button" className="btn btn--contorno" onClick={tentarDeNovo}>
          Tentar novamente
        </button>
      </>
    )
  }

  const ultimaMovimentacao = rastreio.historico[rastreio.historico.length - 1]
  const ultimaParada = [...rastreio.historico].reverse().find((m) => m.parada_nome)

  return (
    <>
      <Link to="/cliente/encomendas" className="detalhe__voltar">
        <ArrowLeft size={16} aria-hidden="true" />
        Minhas encomendas
      </Link>
      <h1 className="pagina__titulo">Sua encomenda #{encomenda.codigo_rastreio}</h1>
      <p className="pagina__subtitulo">Acompanhe o caminho da sua encomenda.</p>

      <div className="detalhe">
        <div className="detalhe__principal">
          <Card titulo="Dados da encomenda">
            <dl className="detalhe__dados">
              <div>
                <dt>Status</dt>
                <dd>
                  <StatusBadge status={rastreio.status_atual} />
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
                  {destinatario ? `${destinatario.nome} · CPF ${mascararCpf(destinatario.cpf)}` : '—'}
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
            </dl>
          </Card>

          <Card titulo="Linha do tempo">
            <LinhaDoTempo historico={rastreio.historico} />
          </Card>
        </div>

        <aside className="detalhe__lateral">
          <Card titulo="Rastreamento atual">
            <div className="detalhe__pessoa">
              <MapPin size={20} aria-hidden="true" />
              <div>
                <small className="texto-suave">Última parada registrada:</small>
                <strong>{ultimaParada ? ultimaParada.parada_nome : 'Ainda não saiu de Manaus'}</strong>
                {ultimaMovimentacao && (
                  <small className="texto-suave">
                    Atualizado em {formatarDataHora(ultimaMovimentacao.criado_em)}
                  </small>
                )}
              </div>
            </div>
          </Card>

          <PessoaAutorizadaCard encomenda={encomenda} destinatario={destinatario} />
        </aside>
      </div>
    </>
  )
}

export default function DetalheEncomenda() {
  const { codigo } = useParams()

  // `key` zera o estado ao trocar de código (ex.: pela busca do header com a tela já aberta).
  return <Detalhe key={codigo} codigo={codigo} />
}
