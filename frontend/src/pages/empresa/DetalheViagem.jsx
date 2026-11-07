import { ArrowLeft, MapPin, Package, Play, CircleCheck, Ban } from 'lucide-react'
import { useCallback, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import CampoSelecao from '../../components/CampoSelecao'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import Modal from '../../components/Modal'
import StatusBadge from '../../components/StatusBadge'
import Tabela from '../../components/Tabela'
import { useCarga } from '../../hooks/useCarga'
import {
  atualizarStatusViagem,
  listarEncomendasDaViagem,
  obterViagem,
  registrarLocalizacao,
} from '../../services/viagens'
import { formatarDataHora } from '../../utils/data'
import {
  encomendasAfetadasPeloCancelamento,
  encomendasEmbarcadas,
  ordenarParadas,
  podeMudarPara,
  podeRegistrarLocalizacao,
  viagemFinalizada,
} from '../../utils/viagem'
import './Gestao.css'
import './Viagens.css'

const ORDEM_ORIGEM = 1

const AVISO_STATUS = {
  em_andamento: 'Viagem iniciada.',
  concluida: 'Viagem concluída.',
  cancelada: 'Viagem cancelada.',
}

const plural = (n, singular, pluralTexto) => `${n} ${n === 1 ? singular : pluralTexto}`

function CancelarViagemModal({ afetadas, carregandoEncomendas, aoFechar, aoConfirmar }) {
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function confirmar() {
    setErro('')
    setEnviando(true)
    try {
      await aoConfirmar()
    } catch (falha) {
      setErro(falha.message)
      setEnviando(false)
    }
  }

  return (
    <Modal titulo="Cancelar viagem" aoFechar={aoFechar} bloqueado={enviando}>
      {erro && <Alerta tipo="erro">{erro}</Alerta>}

      <p>Cancelar esta viagem?</p>
      <Alerta tipo="info">
        As encomendas associadas à viagem passam para <strong>Imprevisto</strong>, exceto as já
        entregues. A viagem cancelada não pode ser reaberta.
        {!carregandoEncomendas && ` ${plural(afetadas, 'encomenda será afetada', 'encomendas serão afetadas')}.`}
      </Alerta>

      <div className="modal__acoes">
        <button type="button" className="btn btn--contorno" onClick={aoFechar} disabled={enviando}>
          Voltar
        </button>
        <button type="button" className="btn btn--perigo" onClick={confirmar} disabled={enviando}>
          {enviando ? 'Cancelando...' : 'Cancelar viagem'}
        </button>
      </div>
    </Modal>
  )
}

function RegistrarLocalizacao({ viagem, paradas, embarcadas, aoRegistrar, aoConflito }) {
  const [paradaId, setParadaId] = useState('')
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (!podeRegistrarLocalizacao(viagem.status)) {
    return (
      <Card titulo="Registrar localização">
        <p className="texto-suave">
          {viagemFinalizada(viagem.status)
            ? 'Esta viagem já foi encerrada.'
            : 'Inicie a viagem para registrar a localização da embarcação.'}
        </p>
      </Card>
    )
  }

  async function enviar(evento) {
    evento.preventDefault()
    setErro('')
    setSucesso('')

    if (!paradaId) {
      setErro('Escolha a parada em que a embarcação está.')
      return
    }

    const parada = paradas.find((p) => String(p.id) === paradaId)

    setEnviando(true)
    try {
      const { encomendas_registradas: registradas } = await registrarLocalizacao(viagem.id, Number(paradaId))

      setSucesso(
        registradas === 0
          ? `Localização registrada em ${parada.nome}. Nenhuma encomenda a bordo para atualizar.`
          : `Localização registrada em ${parada.nome}: ${plural(registradas, 'encomenda a bordo atualizada', 'encomendas a bordo atualizadas')}.`,
      )
      setParadaId('')
      aoRegistrar()
    } catch (falha) {
      // 409: a situação da viagem pode ter mudado; a mensagem vai para o topo da página, que confere de novo.
      if (falha.status === 409) aoConflito(falha.message)
      else setErro(falha.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Card titulo="Registrar localização">
      <form onSubmit={enviar} noValidate>
        {erro && <Alerta tipo="erro">{erro}</Alerta>}
        {sucesso && <Alerta tipo="sucesso">{sucesso}</Alerta>}

        <Alerta tipo="info">
          A primeira localização registrada muda as encomendas <strong>Embarcada</strong> para{' '}
          <strong>Em trânsito</strong>.
          {embarcadas > 0 && ` Há ${plural(embarcadas, 'encomenda embarcada', 'encomendas embarcadas')} nesta viagem.`}
        </Alerta>

        <CampoSelecao
          rotulo="Parada em que a embarcação chegou"
          value={paradaId}
          onChange={(e) => {
            setParadaId(e.target.value)
            setErro('')
          }}
          disabled={paradas.length === 0}
          ajuda={paradas.length === 0 ? 'A rota desta viagem não tem paradas cadastradas.' : undefined}
        >
          <option value="">Escolha a parada</option>
          {paradas.map((p) => (
            <option key={p.id} value={p.id}>
              {p.ordem} · {p.nome}
            </option>
          ))}
        </CampoSelecao>

        <button type="submit" className="btn btn--primario btn--bloco" disabled={enviando || paradas.length === 0}>
          <MapPin size={16} aria-hidden="true" />
          {enviando ? 'Registrando...' : 'Registrar localização'}
        </button>
      </form>
    </Card>
  )
}

function Ocupacao({ total, capacidade }) {
  const percentual = capacidade > 0 ? Math.min(100, Math.round((total / capacidade) * 100)) : 0
  const acima = total > capacidade

  return (
    <div className="viagem__ocupacao">
      <span>
        {total} de {capacidade} {capacidade === 1 ? 'encomenda' : 'encomendas'}
        {acima && ' (acima da capacidade)'}
      </span>
      <div className="viagem__barra" role="presentation">
        <span className={acima ? 'viagem__barra-cheia' : undefined} style={{ width: `${percentual}%` }} />
      </div>
    </div>
  )
}

export default function DetalheViagem() {
  const { viagemId } = useParams()
  const location = useLocation()

  const carregarViagem = useCallback(() => obterViagem(viagemId), [viagemId])
  const carregarEncomendas = useCallback(() => listarEncomendasDaViagem(viagemId), [viagemId])
  const viagemCarga = useCarga(carregarViagem)
  const encomendasCarga = useCarga(carregarEncomendas)
  const { definirDados: definirViagem } = viagemCarga
  const { definirDados: definirEncomendas, recarregar: recarregarEncomendas } = encomendasCarga

  // `aviso` vem da tela anterior (ex.: "Viagem programada.").
  const [aviso, setAviso] = useState(location.state?.aviso ?? '')
  const [erroAcao, setErroAcao] = useState('')
  const [emCurso, setEmCurso] = useState('')
  const [cancelando, setCancelando] = useState(false)

  const voltar = (
    <Link to="/empresa/viagens" className="viagem__voltar">
      <ArrowLeft size={16} aria-hidden="true" />
      Voltar para viagens
    </Link>
  )

  // Confere a viagem e as encomendas sem voltar ao "Carregando..." (usado depois de um 409).
  const atualizarEmSilencio = useCallback(() => {
    obterViagem(viagemId)
      .then((atual) => definirViagem(() => atual))
      .catch(() => {})
    listarEncomendasDaViagem(viagemId)
      .then((lista) => definirEncomendas(() => lista))
      .catch(() => {})
  }, [viagemId, definirViagem, definirEncomendas])

  if (viagemCarga.carregando) return <Carregando />

  if (viagemCarga.erro) {
    return (
      <>
        {voltar}
        {viagemCarga.erro.status === 404 ? (
          <Alerta tipo="erro">Viagem não encontrada.</Alerta>
        ) : (
          <ErroCarga mensagem={viagemCarga.erro.message} aoTentarDeNovo={viagemCarga.recarregar} />
        )}
      </>
    )
  }

  const viagem = viagemCarga.dados
  const { embarcacao, rota } = viagem
  const paradas = ordenarParadas(rota.paradas)
  const encomendas = encomendasCarga.dados ?? []
  const encomendasProntas = !encomendasCarga.carregando && !encomendasCarga.erro

  // Aplica a mudança de status; quem chama trata a falha (a tela atual ou o modal de cancelamento).
  async function mudarStatus(novoStatus) {
    try {
      const atualizada = await atualizarStatusViagem(viagem.id, novoStatus)

      // A resposta não traz embarcação nem rota: mantém as que já estão na tela.
      definirViagem((atual) => ({ ...atual, ...atualizada }))
      if (novoStatus === 'cancelada') recarregarEncomendas()
      setAviso(AVISO_STATUS[novoStatus])
    } catch (falha) {
      // 409: outra pessoa pode ter mudado o status; a tela confere de novo.
      if (falha.status === 409) atualizarEmSilencio()
      throw falha
    }
  }

  async function executar(novoStatus) {
    setErroAcao('')
    setAviso('')
    setEmCurso(novoStatus)
    try {
      await mudarStatus(novoStatus)
    } catch (falha) {
      setErroAcao(falha.message)
    } finally {
      setEmCurso('')
    }
  }

  async function confirmarCancelamento() {
    setErroAcao('')
    setAviso('')
    await mudarStatus('cancelada')
    setCancelando(false)
  }

  function aoRegistrarLocalizacao() {
    setAviso('')
    recarregarEncomendas()
  }

  function aoConflitoLocalizacao(mensagem) {
    setAviso('')
    setErroAcao(mensagem)
    atualizarEmSilencio()
  }

  const colunasEncomendas = [
    {
      chave: 'codigo_rastreio',
      titulo: 'Código de rastreio',
      render: (e) => <span className="gestao__nome">{e.codigo_rastreio}</span>,
    },
    { chave: 'destino_nome', titulo: 'Destino', render: (e) => e.destino_nome ?? '—' },
    { chave: 'descricao', titulo: 'Descrição' },
    { chave: 'status', titulo: 'Status', render: (e) => <StatusBadge status={e.status} /> },
  ]

  const ocupada = Boolean(emCurso)

  return (
    <>
      {voltar}

      <div className="gestao__topo">
        <div>
          <h1 className="pagina__titulo">Viagem #{viagem.id}</h1>
          <p className="pagina__subtitulo">
            {embarcacao.nome} · {rota.nome}
          </p>
        </div>
        <StatusBadge status={viagem.status} />
      </div>

      {erroAcao && <Alerta tipo="erro">{erroAcao}</Alerta>}
      {aviso && <Alerta tipo="sucesso">{aviso}</Alerta>}

      <div className="viagem__corpo">
        <div className="viagem__principal">
          <Card titulo="Dados da viagem">
            <dl className="viagem__dados">
              <div>
                <dt>Status</dt>
                <dd>
                  <StatusBadge status={viagem.status} />
                </dd>
              </div>
              <div>
                <dt>Embarcação</dt>
                <dd>
                  {embarcacao.nome}
                  <small className="texto-suave"> · capacidade {embarcacao.capacidade}</small>
                </dd>
              </div>
              <div>
                <dt>Rota</dt>
                <dd>
                  <Link to={`/empresa/rotas/${rota.id}`}>{rota.nome}</Link>
                </dd>
              </div>
              <div>
                <dt>Saída de Manaus</dt>
                <dd>{formatarDataHora(viagem.data_saida)}</dd>
              </div>
              <div>
                <dt>Programada em</dt>
                <dd>{formatarDataHora(viagem.criado_em)}</dd>
              </div>
            </dl>
          </Card>

          <Card titulo="Paradas da rota">
            {paradas.length === 0 ? (
              <p className="texto-suave">Esta rota ainda não tem paradas cadastradas.</p>
            ) : (
              <ol className="viagem__paradas">
                {paradas.map((p) => (
                  <li key={p.id}>
                    <span className="viagem__ordem">{p.ordem}</span>
                    <strong>{p.nome}</strong>
                    {p.ordem === ORDEM_ORIGEM && <small className="texto-suave">origem</small>}
                  </li>
                ))}
              </ol>
            )}
          </Card>

          <Card
            titulo="Encomendas da viagem"
            acoes={encomendasProntas && <Ocupacao total={encomendas.length} capacidade={embarcacao.capacidade} />}
          >
            {encomendasCarga.carregando && <Carregando />}
            {encomendasCarga.erro && (
              <ErroCarga mensagem={encomendasCarga.erro.message} aoTentarDeNovo={recarregarEncomendas} />
            )}

            {encomendasProntas && encomendas.length === 0 && (
              <div className="gestao__vazio">
                <Package size={36} aria-hidden="true" />
                <h2>Nenhuma encomenda associada</h2>
                <p className="texto-suave">
                  A associação de encomendas a viagens será liberada junto com a tela de gestão de
                  encomendas.
                </p>
              </div>
            )}

            {encomendasProntas && encomendas.length > 0 && (
              <>
                <div className="viagem__tabela">
                  <Tabela colunas={colunasEncomendas} linhas={encomendas} />
                </div>

                <ul className="gestao__cards viagem__cards" aria-label="Encomendas da viagem">
                  {encomendas.map((e) => (
                    <li key={e.id} className="gestao__cartao">
                      <span className="gestao__cartao-topo">
                        <strong className="gestao__nome">{e.codigo_rastreio}</strong>
                        <StatusBadge status={e.status} />
                      </span>
                      <span>{e.descricao}</span>
                      <span className="texto-suave">Destino: {e.destino_nome ?? '—'}</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </Card>
        </div>

        <div className="viagem__lateral">
          <Card titulo="Ações">
            {viagemFinalizada(viagem.status) ? (
              <p className="texto-suave">
                Esta viagem foi {viagem.status === 'cancelada' ? 'cancelada' : 'concluída'} e não aceita mais
                mudanças de status.
              </p>
            ) : (
              <div className="viagem__acoes">
                {podeMudarPara(viagem.status, 'em_andamento') && (
                  <>
                    <button
                      type="button"
                      className="btn btn--sucesso btn--bloco"
                      onClick={() => executar('em_andamento')}
                      disabled={ocupada}
                    >
                      <Play size={16} aria-hidden="true" />
                      {emCurso === 'em_andamento' ? 'Iniciando...' : 'Iniciar viagem'}
                    </button>
                    <p className="campo__ajuda">Libera o registro de localização.</p>
                  </>
                )}

                {podeMudarPara(viagem.status, 'concluida') && (
                  <>
                    <button
                      type="button"
                      className="btn btn--sucesso btn--bloco"
                      onClick={() => executar('concluida')}
                      disabled={ocupada}
                    >
                      <CircleCheck size={16} aria-hidden="true" />
                      {emCurso === 'concluida' ? 'Concluindo...' : 'Concluir viagem'}
                    </button>
                    <p className="campo__ajuda">Encerra a viagem; ela não pode ser reaberta.</p>
                  </>
                )}

                {podeMudarPara(viagem.status, 'cancelada') && (
                  <button
                    type="button"
                    className="btn btn--perigo btn--bloco"
                    onClick={() => setCancelando(true)}
                    disabled={ocupada}
                  >
                    <Ban size={16} aria-hidden="true" />
                    Cancelar viagem
                  </button>
                )}
              </div>
            )}
          </Card>

          <RegistrarLocalizacao
            viagem={viagem}
            paradas={paradas}
            embarcadas={encomendasEmbarcadas(encomendas).length}
            aoRegistrar={aoRegistrarLocalizacao}
            aoConflito={aoConflitoLocalizacao}
          />
        </div>
      </div>

      {cancelando && (
        <CancelarViagemModal
          afetadas={encomendasAfetadasPeloCancelamento(encomendas).length}
          carregandoEncomendas={!encomendasProntas}
          aoFechar={() => setCancelando(false)}
          aoConfirmar={confirmarCancelamento}
        />
      )}
    </>
  )
}
