import { Navigation, Plus } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import Carregando from '../../components/Carregando'
import CampoSelecao from '../../components/CampoSelecao'
import ErroCarga from '../../components/ErroCarga'
import StatusBadge from '../../components/StatusBadge'
import Tabela from '../../components/Tabela'
import { useCarga } from '../../hooks/useCarga'
import { listarEmbarcacoes } from '../../services/embarcacoes'
import { listarRotas } from '../../services/rotas'
import { listarViagens } from '../../services/viagens'
import { formatarDataHora } from '../../utils/data'
import { FILTRO_TODOS, FILTROS_STATUS } from '../../utils/viagem'
import ViagemModal from './ViagemModal'
import './Gestao.css'
import './Viagens.css'

// A lista de viagens só traz ids de embarcação e rota; os nomes vêm das listas de embarcações e rotas.
function carregarTudo() {
  return Promise.all([listarViagens(), listarEmbarcacoes(), listarRotas()]).then(
    ([viagens, embarcacoes, rotas]) => ({ viagens, embarcacoes, rotas }),
  )
}

export default function Viagens() {
  const navigate = useNavigate()
  const { carregando, erro, dados, recarregar } = useCarga(carregarTudo)
  const [filtro, setFiltro] = useState(FILTRO_TODOS)
  const [modalAberto, setModalAberto] = useState(false)

  const viagens = dados?.viagens ?? []
  const embarcacoes = dados?.embarcacoes ?? []
  const rotas = dados?.rotas ?? []
  const pronto = !carregando && !erro

  const nomeEmbarcacao = (id) => embarcacoes.find((e) => e.id === id)?.nome ?? '—'
  const nomeRota = (id) => rotas.find((r) => r.id === id)?.nome ?? '—'

  // O filtro roda na tela, sobre a lista completa (a API também aceita ?status=).
  const visiveis = filtro === FILTRO_TODOS ? viagens : viagens.filter((v) => v.status === filtro)

  function aoProgramada(nova) {
    // Segue para o detalhe, de onde a viagem pode ser iniciada.
    navigate(`/empresa/viagens/${nova.id}`, { state: { aviso: 'Viagem programada.' } })
  }

  const botaoProgramar = (
    <button type="button" className="btn btn--primario" onClick={() => setModalAberto(true)}>
      <Plus size={16} aria-hidden="true" />
      Programar viagem
    </button>
  )

  const detalhe = (v) => `/empresa/viagens/${v.id}`

  const colunas = [
    {
      chave: 'id',
      titulo: 'Viagem',
      render: (v) => (
        <Link to={detalhe(v)} className="gestao__nome">
          Viagem #{v.id}
        </Link>
      ),
    },
    { chave: 'embarcacao', titulo: 'Embarcação', render: (v) => nomeEmbarcacao(v.embarcacao_id) },
    { chave: 'rota', titulo: 'Rota', render: (v) => nomeRota(v.rota_id) },
    { chave: 'data_saida', titulo: 'Saída', render: (v) => formatarDataHora(v.data_saida) },
    { chave: 'status', titulo: 'Status', render: (v) => <StatusBadge status={v.status} /> },
    {
      chave: 'acoes',
      titulo: 'Ações',
      render: (v) => (
        <Link to={detalhe(v)} className="btn btn--contorno">
          Ver detalhes
        </Link>
      ),
    },
  ]

  return (
    <>
      <div className="gestao__topo">
        <div>
          <h1 className="pagina__titulo">Viagens</h1>
          <p className="pagina__subtitulo">Programe, acompanhe e encerre as viagens da frota.</p>
        </div>
        {pronto && viagens.length > 0 && botaoProgramar}
      </div>

      {carregando && <Carregando />}
      {erro && <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />}

      {pronto && viagens.length === 0 && (
        <Card>
          <div className="gestao__vazio">
            <Navigation size={36} aria-hidden="true" />
            <h2>Nenhuma viagem programada</h2>
            <p className="texto-suave">
              Programe a primeira viagem escolhendo uma embarcação ativa e uma rota.
            </p>
            {botaoProgramar}
          </div>
        </Card>
      )}

      {pronto && viagens.length > 0 && (
        <>
          <div className="viagens__filtro">
            <CampoSelecao
              rotulo="Filtrar por status"
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
            >
              {FILTROS_STATUS.map(([valor, rotulo]) => (
                <option key={valor} value={valor}>
                  {rotulo}
                </option>
              ))}
            </CampoSelecao>
          </div>

          {visiveis.length === 0 ? (
            <Alerta tipo="info">Nenhuma viagem com esse status.</Alerta>
          ) : (
            <>
              <Card className="gestao__tabela">
                <Tabela colunas={colunas} linhas={visiveis} />
              </Card>

              <ul className="gestao__cards" aria-label="Lista de viagens">
                {visiveis.map((v) => (
                  <li key={v.id} className="gestao__cartao">
                    <span className="gestao__cartao-topo">
                      <Link to={detalhe(v)} className="gestao__nome">
                        Viagem #{v.id}
                      </Link>
                      <StatusBadge status={v.status} />
                    </span>
                    <span>
                      {nomeEmbarcacao(v.embarcacao_id)} · {nomeRota(v.rota_id)}
                    </span>
                    <span className="gestao__cartao-rodape texto-suave">
                      Saída: {formatarDataHora(v.data_saida)}
                    </span>
                    <Link to={detalhe(v)} className="btn btn--contorno">
                      Ver detalhes
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      {modalAberto && (
        <ViagemModal
          embarcacoes={embarcacoes}
          rotas={rotas}
          aoFechar={() => setModalAberto(false)}
          aoProgramada={aoProgramada}
        />
      )}
    </>
  )
}
