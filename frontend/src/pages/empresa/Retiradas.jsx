import { PackageCheck } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import CampoTexto from '../../components/CampoTexto'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import StatusBadge from '../../components/StatusBadge'
import Tabela from '../../components/Tabela'
import { useCarga } from '../../hooks/useCarga'
import { listarEncomendasDaEmpresa } from '../../services/encomendas'
import { mascararCpf } from '../../utils/cpf'
import { formatarData, formatarDataHora } from '../../utils/data'
import { caminhoRetirada } from '../../utils/retirada'
import './Gestao.css'
import './Encomendas.css'
import './Retirada.css'

const ATRASO_BUSCA_MS = 400
// A fila é curta (só o que está a retirar); a busca por código refina quando passar disso.
const LIMITE_FILA = 50

function Destinatario({ destinatario }) {
  return (
    <span className="encomendas__destinatario">
      <strong>{destinatario.nome}</strong>
      <small className="texto-suave">CPF {mascararCpf(destinatario.cpf)}</small>
    </span>
  )
}

// Carrega e mostra a fila. O pai troca a `key` a cada busca, então cada consulta começa em "Carregando...".
function Fila({ busca }) {
  const carregar = useCallback(
    () => listarEncomendasDaEmpresa({ status: ['a_retirar'], busca, limite: LIMITE_FILA }),
    [busca],
  )
  const { carregando, erro, dados, recarregar } = useCarga(carregar)

  if (carregando) return <Carregando />
  if (erro) return <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />

  const { itens, total } = dados

  if (total === 0) {
    return (
      <Card>
        <div className="gestao__vazio">
          <PackageCheck size={36} aria-hidden="true" />
          {busca ? (
            <>
              <h2>Nenhuma encomenda encontrada</h2>
              <p className="texto-suave">Nenhuma encomenda a retirar tem um código parecido com esse.</p>
            </>
          ) : (
            <>
              <h2>Nenhuma encomenda a retirar</h2>
              <p className="texto-suave">
                Quando uma encomenda chegar ao destino e ficar com o status “A retirar”, ela aparece aqui.
              </p>
            </>
          )}
        </div>
      </Card>
    )
  }

  const colunas = [
    {
      chave: 'codigo_rastreio',
      titulo: 'Código',
      render: (e) => (
        <Link to={caminhoRetirada(e.codigo_rastreio)} className="encomendas__codigo">
          {e.codigo_rastreio}
        </Link>
      ),
    },
    { chave: 'destinatario', titulo: 'Destinatário', render: (e) => <Destinatario destinatario={e.destinatario} /> },
    { chave: 'destino_nome', titulo: 'Destino', render: (e) => e.destino_nome ?? '—' },
    { chave: 'descricao', titulo: 'Descrição', render: (e) => e.descricao },
    { chave: 'status', titulo: 'Status', render: (e) => <StatusBadge status={e.status} /> },
    { chave: 'criado_em', titulo: 'Data', render: (e) => formatarData(e.criado_em) },
    {
      chave: 'acoes',
      titulo: 'Ações',
      render: (e) => (
        <Link to={caminhoRetirada(e.codigo_rastreio)} className="btn btn--primario">
          Retirar
        </Link>
      ),
    },
  ]

  return (
    <>
      <Card className="gestao__tabela">
        <Tabela colunas={colunas} linhas={itens} />
      </Card>

      <ul className="gestao__cards" aria-label="Fila de retirada">
        {itens.map((e) => (
          <li key={e.id} className="gestao__cartao">
            <span className="gestao__cartao-topo">
              <Link to={caminhoRetirada(e.codigo_rastreio)} className="gestao__nome encomendas__codigo">
                {e.codigo_rastreio}
              </Link>
              <StatusBadge status={e.status} />
            </span>
            <span>{e.descricao}</span>
            <Destinatario destinatario={e.destinatario} />
            <span className="texto-suave">Destino: {e.destino_nome ?? '—'}</span>
            <small className="texto-suave" title={formatarDataHora(e.criado_em)}>
              {formatarData(e.criado_em)}
            </small>
            <Link to={caminhoRetirada(e.codigo_rastreio)} className="btn btn--primario">
              Retirar
            </Link>
          </li>
        ))}
      </ul>

      <p className="texto-suave retirada__resumo">
        {total > itens.length
          ? `Mostrando ${itens.length} de ${total} encomendas a retirar. Use a busca por código para encontrar as demais.`
          : `${total} ${total === 1 ? 'encomenda a retirar' : 'encomendas a retirar'}.`}
      </p>
    </>
  )
}

export default function Retiradas() {
  const [textoBusca, setTextoBusca] = useState('')
  const [busca, setBusca] = useState('')
  const localizacao = useLocation()
  const navegar = useNavigate()

  // Confirmação vinda da tela de retirada ({ codigo, entregueEm }); não leva CPF. Lida uma vez e
  // retirada do histórico, para não reaparecer ao recarregar a página.
  const [confirmacao] = useState(() => localizacao.state?.confirmacao ?? null)

  useEffect(() => {
    if (confirmacao) navegar(localizacao.pathname, { replace: true, state: null })
  }, [confirmacao, localizacao.pathname, navegar])

  // A busca por código só vira filtro depois de uma pausa na digitação.
  useEffect(() => {
    const temporizador = setTimeout(() => setBusca(textoBusca.trim()), ATRASO_BUSCA_MS)

    return () => clearTimeout(temporizador)
  }, [textoBusca])

  return (
    <>
      <div className="gestao__topo">
        <div>
          <h1 className="pagina__titulo">Retiradas</h1>
          <p className="pagina__subtitulo">Encomendas que chegaram ao destino e aguardam a retirada.</p>
        </div>
      </div>

      {confirmacao && (
        <Alerta tipo="sucesso">
          Retirada registrada: a encomenda <strong>{confirmacao.codigo}</strong> foi entregue em{' '}
          {formatarDataHora(confirmacao.entregueEm)}.
        </Alerta>
      )}

      <Card className="retirada__busca">
        <CampoTexto
          rotulo="Buscar por código"
          type="search"
          placeholder="Ex.: FLX-ABC123"
          value={textoBusca}
          onChange={(e) => setTextoBusca(e.target.value)}
        />
      </Card>

      <Fila key={busca} busca={busca} />
    </>
  )
}
