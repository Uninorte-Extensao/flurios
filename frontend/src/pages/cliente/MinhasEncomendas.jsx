import { PackagePlus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import Carregando from '../../components/Carregando'
import StatusBadge from '../../components/StatusBadge'
import Tabela from '../../components/Tabela'
import { listarDestinatarios, listarEncomendas } from '../../services/encomendas'
import { mascararCpf } from '../../utils/cpf'
import { formatarData } from '../../utils/data'
import './MinhasEncomendas.css'

const caminhoDetalhe = (encomenda) => `/cliente/encomendas/${encodeURIComponent(encomenda.codigo_rastreio)}`

// A API de encomendas só traz o id do destinatário; nome e CPF (já mascarado) vêm de GET /destinatarios.
function Destinatario({ destinatario }) {
  if (!destinatario) return <span className="texto-suave">—</span>

  return (
    <span className="minhas-encomendas__destinatario">
      <strong>{destinatario.nome}</strong>
      <small className="texto-suave">CPF {mascararCpf(destinatario.cpf)}</small>
    </span>
  )
}

function EstadoVazio() {
  return (
    <Card>
      <div className="minhas-encomendas__vazio">
        <PackagePlus size={36} aria-hidden="true" />
        <h2>Você ainda não tem encomendas</h2>
        <p className="texto-suave">
          Cadastre sua primeira encomenda para receber um código de rastreio e acompanhá-la por aqui.
        </p>
        <Link to="/cliente/nova-encomenda" className="btn btn--primario">
          Nova encomenda
        </Link>
      </div>
    </Card>
  )
}

export default function MinhasEncomendas() {
  const [estado, setEstado] = useState({ carregando: true, erro: '', encomendas: [], destinatarios: [] })
  const [tentativa, setTentativa] = useState(0)

  useEffect(() => {
    let ativo = true

    Promise.all([listarEncomendas(), listarDestinatarios()])
      .then(([encomendas, destinatarios]) => {
        if (ativo) setEstado({ carregando: false, erro: '', encomendas, destinatarios })
      })
      .catch((erro) => {
        if (ativo) setEstado({ carregando: false, erro: erro.message, encomendas: [], destinatarios: [] })
      })

    return () => {
      ativo = false
    }
  }, [tentativa])

  function tentarDeNovo() {
    setEstado((atual) => ({ ...atual, carregando: true, erro: '' }))
    setTentativa((n) => n + 1)
  }

  const { carregando, erro, encomendas, destinatarios } = estado
  const destinatarioDe = (encomenda) => destinatarios.find((d) => d.id === encomenda.destinatario_id)

  const colunas = [
    {
      chave: 'codigo_rastreio',
      titulo: 'Código de rastreio',
      render: (e) => (
        <Link to={caminhoDetalhe(e)} className="minhas-encomendas__codigo">
          {e.codigo_rastreio}
        </Link>
      ),
    },
    {
      chave: 'destinatario',
      titulo: 'Destinatário',
      render: (e) => <Destinatario destinatario={destinatarioDe(e)} />,
    },
    { chave: 'destino_nome', titulo: 'Destino', render: (e) => e.destino_nome ?? '—' },
    { chave: 'status', titulo: 'Status', render: (e) => <StatusBadge status={e.status} /> },
    { chave: 'criado_em', titulo: 'Data', render: (e) => formatarData(e.criado_em) },
  ]

  return (
    <>
      <div className="minhas-encomendas__topo">
        <div>
          <h1 className="pagina__titulo">Minhas encomendas</h1>
          <p className="pagina__subtitulo">Acompanhe os envios que você cadastrou.</p>
        </div>
        {encomendas.length > 0 && (
          <Link to="/cliente/nova-encomenda" className="btn btn--primario">
            <PackagePlus size={16} aria-hidden="true" />
            Nova encomenda
          </Link>
        )}
      </div>

      {carregando && <Carregando />}

      {erro && (
        <Alerta tipo="erro">
          {erro}{' '}
          <button type="button" className="btn btn--contorno" onClick={tentarDeNovo}>
            Tentar novamente
          </button>
        </Alerta>
      )}

      {!carregando && !erro && encomendas.length === 0 && <EstadoVazio />}

      {!carregando && !erro && encomendas.length > 0 && (
        <>
          <Card className="minhas-encomendas__tabela">
            <Tabela colunas={colunas} linhas={encomendas} />
          </Card>

          <ul className="minhas-encomendas__cards" aria-label="Lista de encomendas">
            {encomendas.map((e) => (
              <li key={e.id}>
                <Link to={caminhoDetalhe(e)} className="minhas-encomendas__cartao">
                  <span className="minhas-encomendas__cartao-topo">
                    <strong className="minhas-encomendas__codigo">{e.codigo_rastreio}</strong>
                    <StatusBadge status={e.status} />
                  </span>
                  <Destinatario destinatario={destinatarioDe(e)} />
                  <span className="minhas-encomendas__cartao-rodape texto-suave">
                    <span>Destino: {e.destino_nome ?? '—'}</span>
                    <span>{formatarData(e.criado_em)}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  )
}
