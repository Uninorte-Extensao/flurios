import { History, MapPin, Navigation, Package, RefreshCw, Ship } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import BarraProgresso from '../../components/BarraProgresso'
import BlocoCarga from '../../components/BlocoCarga'
import Card from '../../components/Card'
import StatusBadge from '../../components/StatusBadge'
import Tabela from '../../components/Tabela'
import { rotuloDoStatus } from '../../utils/status'
import {
  obterEncomendasPorMunicipio,
  obterEnviosAtivos,
  obterMovimentacoesRecentes,
  obterOcupacao,
  obterResumoEncomendas,
  obterResumoViagens,
} from '../../services/dashboard'
import {
  caminhoViagem,
  ENVIOS_POR_VEZ,
  envioSemViagem,
  formatarNumero,
  LIMITE_MOVIMENTACOES,
  limitarEnvios,
  listarPorStatus,
  maiorTotal,
  ORDEM_STATUS_ENCOMENDA,
  ORDEM_STATUS_VIAGEM,
  percentual,
  percentualDoMaior,
  percentualDoTotal,
  textoOcupacao,
  textoProximaParada,
  varianteOcupacao,
  varianteProgresso,
} from '../../utils/dashboard'
import { formatarDataHora } from '../../utils/data'
import { caminhoDetalheEmpresa } from '../../utils/gestaoEncomenda'
import './Gestao.css'
import './Dashboard.css'

// Cada bloco chama a própria rota. Funções do módulo: a identidade estável evita recargas em loop.
const carregarMovimentacoes = () => obterMovimentacoesRecentes(LIMITE_MOVIMENTACOES)

const VARIANTE_BARRA_VIAGEM = { em_andamento: 'verde', cancelada: 'coral' }

function LinhaBarra({ rotulo, valor, percentualBarra, variante, nomeBarra }) {
  return (
    <li className="dashboard__linha">
      <span className="dashboard__linha-topo">
        <span className="dashboard__linha-rotulo">{rotulo}</span>
        <strong>{valor}</strong>
      </span>
      <BarraProgresso percentual={percentualBarra} variante={variante} rotulo={nomeBarra} />
    </li>
  )
}

function CartaoStatus({ status, total }) {
  return (
    <Card className={`kpi${total === 0 ? ' kpi--zero' : ''}${status === 'imprevisto' && total > 0 ? ' kpi--alerta' : ''}`}>
      <StatusBadge status={status} />
      <strong className="kpi__numero">{formatarNumero(total)}</strong>
    </Card>
  )
}

function Resumo({ dados }) {
  return (
    <div className="dashboard__resumo">
      <Card className="kpi kpi--principal">
        <span className="kpi__rotulo">
          <Package size={18} aria-hidden="true" />
          Encomendas registradas
        </span>
        <strong className="card__kpi">{formatarNumero(dados.total)}</strong>
      </Card>

      <div className="dashboard__status">
        {listarPorStatus(dados.por_status, ORDEM_STATUS_ENCOMENDA).map(({ status, total }) => (
          <CartaoStatus key={status} status={status} total={total} />
        ))}
      </div>
    </div>
  )
}

function Viagens({ dados }) {
  return (
    <>
      <p className="dashboard__destaque">
        <strong className="card__kpi">{formatarNumero(dados.em_andamento)}</strong>
        <span className="texto-suave">{dados.em_andamento === 1 ? 'viagem em andamento' : 'viagens em andamento'}</span>
      </p>

      <ul className="dashboard__lista">
        {listarPorStatus(dados.por_status, ORDEM_STATUS_VIAGEM).map(({ status, total }) => (
          <LinhaBarra
            key={status}
            rotulo={<StatusBadge status={status} />}
            valor={formatarNumero(total)}
            percentualBarra={percentualDoTotal(total, dados.total)}
            variante={VARIANTE_BARRA_VIAGEM[status]}
            nomeBarra={`Viagens ${rotuloDoStatus(status).toLowerCase()}: ${total} de ${dados.total}`}
          />
        ))}
      </ul>
    </>
  )
}

function Ocupacao({ dados }) {
  return (
    <ul className="dashboard__lista">
      {dados.viagens.map((v) => {
        const pct = percentual(v.ocupacao)

        return (
          <li key={v.viagem_id} className="dashboard__linha">
            <span className="dashboard__linha-topo">
              <span className="dashboard__linha-rotulo">
                <Link to={caminhoViagem(v.viagem_id)}>{v.embarcacao_nome}</Link>
                <small className="texto-suave">{v.rota_nome}</small>
              </span>
              <strong>{pct}%</strong>
            </span>
            <BarraProgresso
              percentual={pct}
              variante={varianteOcupacao(v.ocupacao)}
              rotulo={`Ocupação de ${v.embarcacao_nome}: ${pct}%`}
            />
            <small className="texto-suave">
              {textoOcupacao(v)}
              {v.ocupacao > 1 && <span className="dashboard__aviso"> · acima da capacidade</span>}
            </small>
          </li>
        )
      })}
    </ul>
  )
}

function Municipios({ dados }) {
  const maior = maiorTotal(dados.municipios)

  return (
    <ul className="dashboard__lista">
      {dados.municipios.map((m) => (
        <LinhaBarra
          key={m.municipio}
          rotulo={m.municipio}
          valor={`${formatarNumero(m.total)} · ${percentualDoTotal(m.total, dados.total)}%`}
          percentualBarra={percentualDoMaior(m.total, maior)}
          nomeBarra={`Encomendas para ${m.municipio}: ${m.total}`}
        />
      ))}
    </ul>
  )
}

// Envio sem viagem não tem progresso a mostrar: em vez da barra em 0%, avisa que ainda não saiu.
function ProgressoDoEnvio({ envio }) {
  if (envioSemViagem(envio)) return <span className="texto-suave">Ainda não saiu</span>

  return <Progresso proporcao={envio.progresso} />
}

function Progresso({ proporcao }) {
  const pct = percentual(proporcao)

  return (
    <span className="dashboard__progresso">
      <BarraProgresso percentual={pct} variante={varianteProgresso(proporcao)} rotulo={`Progresso: ${pct}%`} />
      <small>{pct}%</small>
    </span>
  )
}

function Envios({ dados }) {
  const [quantidade, setQuantidade] = useState(ENVIOS_POR_VEZ)
  const { visiveis, restantes } = limitarEnvios(dados.envios, quantidade)

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
    { chave: 'destinatario', titulo: 'Destinatário' },
    { chave: 'municipio_destino', titulo: 'Destino' },
    { chave: 'proxima_parada', titulo: 'Próxima parada', render: textoProximaParada },
    { chave: 'status', titulo: 'Status', render: (e) => <StatusBadge status={e.status} /> },
    { chave: 'progresso', titulo: 'Progresso', render: (e) => <ProgressoDoEnvio envio={e} /> },
  ]

  return (
    <>
      <div className="gestao__tabela">
        <Tabela colunas={colunas} linhas={visiveis} chaveLinha="codigo_rastreio" />
      </div>

      <ul className="gestao__cards dashboard__cards" aria-label="Envios ativos">
        {visiveis.map((e) => (
          <li key={e.codigo_rastreio} className="gestao__cartao">
            <span className="gestao__cartao-topo">
              <Link to={caminhoDetalheEmpresa(e.codigo_rastreio)} className="gestao__nome encomendas__codigo">
                {e.codigo_rastreio}
              </Link>
              <StatusBadge status={e.status} />
            </span>
            <span>
              {e.destinatario} · {e.municipio_destino}
            </span>
            <span className="texto-suave">Próxima parada: {textoProximaParada(e)}</span>
            <ProgressoDoEnvio envio={e} />
          </li>
        ))}
      </ul>

      <div className="dashboard__rodape">
        <small className="texto-suave">
          Mostrando {visiveis.length} de {dados.total} {dados.total === 1 ? 'envio' : 'envios'}.
        </small>
        {restantes > 0 && (
          <button type="button" className="btn btn--contorno" onClick={() => setQuantidade((n) => n + ENVIOS_POR_VEZ)}>
            Mostrar mais
          </button>
        )}
      </div>
    </>
  )
}

function Movimentacoes({ dados }) {
  return (
    <ul className="dashboard__movimentacoes">
      {dados.movimentacoes.map((m, indice) => (
        // Sem id na resposta: o índice é estável porque a lista é recarregada por inteiro.
        <li key={`${m.codigo_rastreio}-${m.data}-${indice}`} className="dashboard__movimentacao">
          <span className="dashboard__movimentacao-topo">
            <Link to={caminhoDetalheEmpresa(m.codigo_rastreio)} className="encomendas__codigo">
              {m.codigo_rastreio}
            </Link>
            <StatusBadge status={m.status} />
          </span>
          <small className="texto-suave">
            {m.parada ? `${m.parada} · ` : ''}
            {formatarDataHora(m.data)}
          </small>
        </li>
      ))}
    </ul>
  )
}

// Página inicial da empresa (/empresa) e item "Dashboard" do menu: indicadores só de leitura.
// Cada bloco carrega e falha sozinho; "Atualizar" remonta todos (a `key` reinicia as cargas).
export default function Dashboard() {
  const [versao, setVersao] = useState(0)

  return (
    <>
      <div className="gestao__topo dashboard__topo">
        <div>
          <h1 className="pagina__titulo">Painel Operacional</h1>
          <p className="pagina__subtitulo">Visão geral das operações e movimentações do sistema FLURIOS.</p>
        </div>
        <button type="button" className="btn btn--contorno" onClick={() => setVersao((n) => n + 1)}>
          <RefreshCw size={16} aria-hidden="true" />
          Atualizar
        </button>
      </div>

      <div className="dashboard" key={versao}>
        <BlocoCarga
          carregar={obterResumoEncomendas}
          estaVazio={(d) => d.total === 0}
          iconeVazio={Package}
          mensagemVazio="Nenhuma encomenda registrada ainda."
          semCartao
        >
          {(dados) => <Resumo dados={dados} />}
        </BlocoCarga>

        <div className="dashboard__duplo">
          <BlocoCarga
            titulo="Viagens"
            carregar={obterResumoViagens}
            estaVazio={(d) => d.total === 0}
            iconeVazio={Navigation}
            mensagemVazio="Nenhuma viagem cadastrada ainda."
          >
            {(dados) => <Viagens dados={dados} />}
          </BlocoCarga>

          <BlocoCarga
            titulo="Ocupação das embarcações"
            carregar={obterOcupacao}
            estaVazio={(d) => d.total === 0}
            iconeVazio={Ship}
            mensagemVazio="Nenhuma viagem em andamento no momento."
          >
            {(dados) => <Ocupacao dados={dados} />}
          </BlocoCarga>
        </div>

        <div className="dashboard__duplo">
          <BlocoCarga
            titulo="Encomendas por município"
            carregar={obterEncomendasPorMunicipio}
            estaVazio={(d) => d.total === 0}
            iconeVazio={MapPin}
            mensagemVazio="Nenhuma encomenda registrada ainda."
          >
            {(dados) => <Municipios dados={dados} />}
          </BlocoCarga>

          <BlocoCarga
            titulo="Movimentações recentes"
            carregar={carregarMovimentacoes}
            estaVazio={(d) => d.total === 0}
            iconeVazio={History}
            mensagemVazio="Nenhuma movimentação registrada ainda."
          >
            {(dados) => <Movimentacoes dados={dados} />}
          </BlocoCarga>
        </div>

        <BlocoCarga
          titulo="Envios ativos"
          carregar={obterEnviosAtivos}
          estaVazio={(d) => d.total === 0}
          iconeVazio={Package}
          mensagemVazio="Nenhum envio ativo no momento."
        >
          {(dados) => <Envios dados={dados} />}
        </BlocoCarga>
      </div>
    </>
  )
}
