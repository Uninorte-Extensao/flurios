import { ChevronLeft, ChevronRight, Package } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import CampoSelecao from '../../components/CampoSelecao'
import CampoTexto from '../../components/CampoTexto'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import StatusBadge from '../../components/StatusBadge'
import Tabela from '../../components/Tabela'
import { useCarga } from '../../hooks/useCarga'
import { listarDestinos, listarEncomendasDaEmpresa } from '../../services/encomendas'
import { mascararCpf } from '../../utils/cpf'
import { formatarData, formatarDataHora } from '../../utils/data'
import { agruparDestinosPorRota } from '../../utils/encomenda'
import {
  caminhoDetalheEmpresa,
  FILTRO_TODOS,
  FILTROS_STATUS,
  ITENS_POR_PAGINA,
  resumoPagina,
} from '../../utils/gestaoEncomenda'
import './Gestao.css'
import './Encomendas.css'

const ATRASO_BUSCA_MS = 400
const FILTROS_INICIAIS = { status: FILTRO_TODOS, destino: FILTRO_TODOS, semViagem: false, busca: '', pagina: 0 }

// Os filtros da tela viram os parâmetros de GET /empresa/encomendas.
function consultaDe(filtros) {
  return {
    status: filtros.status === FILTRO_TODOS ? [] : [filtros.status],
    paradaDestinoId: filtros.destino === FILTRO_TODOS ? undefined : Number(filtros.destino),
    semViagemAtiva: filtros.semViagem,
    busca: filtros.busca,
    limite: ITENS_POR_PAGINA,
    deslocamento: filtros.pagina * ITENS_POR_PAGINA,
  }
}

function Destinatario({ destinatario }) {
  return (
    <span className="encomendas__destinatario">
      <strong>{destinatario.nome}</strong>
      <small className="texto-suave">CPF {mascararCpf(destinatario.cpf)}</small>
    </span>
  )
}

function ViagemAtiva({ viagem }) {
  if (!viagem) return <span className="texto-suave">—</span>

  return (
    <span className="encomendas__viagem">
      <Link to={`/empresa/viagens/${viagem.id}`}>Viagem #{viagem.id}</Link>
      <StatusBadge status={viagem.status} />
    </span>
  )
}

function Paginacao({ pagina, quantidade, total, aoMudar }) {
  const ultima = (pagina + 1) * ITENS_POR_PAGINA >= total

  return (
    <nav className="encomendas__paginacao" aria-label="Paginação">
      <span className="texto-suave">{resumoPagina(pagina, ITENS_POR_PAGINA, quantidade, total)}</span>
      <div className="encomendas__paginas">
        <button type="button" className="btn btn--contorno" onClick={() => aoMudar(pagina - 1)} disabled={pagina === 0}>
          <ChevronLeft size={16} aria-hidden="true" />
          Anterior
        </button>
        <button type="button" className="btn btn--contorno" onClick={() => aoMudar(pagina + 1)} disabled={ultima}>
          Próxima
          <ChevronRight size={16} aria-hidden="true" />
        </button>
      </div>
    </nav>
  )
}

// Carrega e mostra uma página. O pai troca a `key` a cada filtro/página, então cada consulta começa
// em "Carregando..." sem perder o foco dos campos de filtro.
function Resultado({ consulta: consultaDaChave, filtrando, aoMudarPagina, aoLimpar }) {
  // Fixa a consulta desta montagem: o pai só a muda trocando a `key`, e `useCarga` pede função estável.
  const [consulta] = useState(consultaDaChave)
  const carregar = useCallback(() => listarEncomendasDaEmpresa(consulta), [consulta])
  const { carregando, erro, dados, recarregar } = useCarga(carregar)

  if (carregando) return <Carregando />
  if (erro) return <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />

  const { itens, total } = dados
  const pagina = Math.floor(consulta.deslocamento / ITENS_POR_PAGINA)

  if (total === 0) {
    if (filtrando) {
      return (
        <Alerta tipo="info">
          Nenhuma encomenda encontrada com esses filtros.{' '}
          <button type="button" className="btn btn--contorno" onClick={aoLimpar}>
            Limpar filtros
          </button>
        </Alerta>
      )
    }

    return (
      <Card>
        <div className="gestao__vazio">
          <Package size={36} aria-hidden="true" />
          <h2>Nenhuma encomenda registrada</h2>
          <p className="texto-suave">As encomendas cadastradas pelos clientes aparecem aqui.</p>
        </div>
      </Card>
    )
  }

  const colunas = [
    {
      chave: 'codigo_rastreio',
      titulo: 'Código',
      render: (e) => (
        <Link to={caminhoDetalheEmpresa(e.codigo_rastreio)} className="encomendas__codigo">
          {e.codigo_rastreio}
        </Link>
      ),
    },
    { chave: 'destinatario', titulo: 'Destinatário', render: (e) => <Destinatario destinatario={e.destinatario} /> },
    { chave: 'destino_nome', titulo: 'Destino', render: (e) => e.destino_nome ?? '—' },
    { chave: 'status', titulo: 'Status', render: (e) => <StatusBadge status={e.status} /> },
    { chave: 'viagem_ativa', titulo: 'Viagem', render: (e) => <ViagemAtiva viagem={e.viagem_ativa} /> },
    { chave: 'criado_em', titulo: 'Data', render: (e) => formatarData(e.criado_em) },
    {
      chave: 'acoes',
      titulo: 'Ações',
      render: (e) => (
        <Link to={caminhoDetalheEmpresa(e.codigo_rastreio)} className="btn btn--contorno">
          Ver detalhes
        </Link>
      ),
    },
  ]

  return (
    <>
      <Card className="gestao__tabela">
        <Tabela colunas={colunas} linhas={itens} />
      </Card>

      <ul className="gestao__cards" aria-label="Lista de encomendas">
        {itens.map((e) => (
          <li key={e.id} className="gestao__cartao">
            <span className="gestao__cartao-topo">
              <Link to={caminhoDetalheEmpresa(e.codigo_rastreio)} className="gestao__nome encomendas__codigo">
                {e.codigo_rastreio}
              </Link>
              <StatusBadge status={e.status} />
            </span>
            <span>{e.descricao}</span>
            <Destinatario destinatario={e.destinatario} />
            <span className="texto-suave">Destino: {e.destino_nome ?? '—'}</span>
            <span className="gestao__cartao-rodape">
              <ViagemAtiva viagem={e.viagem_ativa} />
              <small className="texto-suave" title={formatarDataHora(e.criado_em)}>
                {formatarData(e.criado_em)}
              </small>
            </span>
            <Link to={caminhoDetalheEmpresa(e.codigo_rastreio)} className="btn btn--contorno">
              Ver detalhes
            </Link>
          </li>
        ))}
      </ul>

      <Paginacao pagina={pagina} quantidade={itens.length} total={total} aoMudar={aoMudarPagina} />
    </>
  )
}

export default function Encomendas() {
  const [filtros, setFiltros] = useState(FILTROS_INICIAIS)
  const [textoBusca, setTextoBusca] = useState('')
  const destinosCarga = useCarga(listarDestinos)

  // A busca por código só vira filtro depois de uma pausa na digitação.
  useEffect(() => {
    const temporizador = setTimeout(() => {
      const busca = textoBusca.trim()
      setFiltros((atual) => (atual.busca === busca ? atual : { ...atual, busca, pagina: 0 }))
    }, ATRASO_BUSCA_MS)

    return () => clearTimeout(temporizador)
  }, [textoBusca])

  function alterar(campo, valor) {
    setFiltros((atual) => ({ ...atual, [campo]: valor, pagina: 0 }))
  }

  function limpar() {
    setTextoBusca('')
    setFiltros(FILTROS_INICIAIS)
  }

  const consulta = consultaDe(filtros)
  const filtrando = JSON.stringify({ ...filtros, pagina: 0 }) !== JSON.stringify(FILTROS_INICIAIS)
  const grupos = agruparDestinosPorRota(destinosCarga.dados ?? [])

  return (
    <>
      <div className="gestao__topo">
        <div>
          <h1 className="pagina__titulo">Encomendas</h1>
          <p className="pagina__subtitulo">Acompanhe as encomendas de todos os clientes e associe-as às viagens.</p>
        </div>
      </div>

      <Card className="encomendas__filtros">
        <CampoTexto
          rotulo="Buscar por código"
          type="search"
          placeholder="Ex.: FLX5MBAFUSZ3L"
          value={textoBusca}
          onChange={(e) => setTextoBusca(e.target.value)}
        />

        <CampoSelecao rotulo="Status" value={filtros.status} onChange={(e) => alterar('status', e.target.value)}>
          {FILTROS_STATUS.map(([valor, rotulo]) => (
            <option key={valor} value={valor}>
              {rotulo}
            </option>
          ))}
        </CampoSelecao>

        <CampoSelecao
          rotulo="Destino"
          value={filtros.destino}
          onChange={(e) => alterar('destino', e.target.value)}
          disabled={destinosCarga.carregando || Boolean(destinosCarga.erro)}
          ajuda={destinosCarga.erro ? 'Não foi possível carregar os destinos.' : undefined}
        >
          <option value={FILTRO_TODOS}>Todos os destinos</option>
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

        <div className="campo campo--caixa encomendas__caixa">
          <input
            id="filtro-sem-viagem"
            type="checkbox"
            checked={filtros.semViagem}
            onChange={(e) => alterar('semViagem', e.target.checked)}
          />
          <label htmlFor="filtro-sem-viagem">Somente sem viagem ativa</label>
        </div>
      </Card>

      <Resultado
        key={JSON.stringify(consulta)}
        consulta={consulta}
        filtrando={filtrando}
        aoMudarPagina={(pagina) => setFiltros((atual) => ({ ...atual, pagina }))}
        aoLimpar={limpar}
      />
    </>
  )
}
