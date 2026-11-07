import { ArrowLeft, MapPin, Trash2 } from 'lucide-react'
import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import CampoTexto from '../../components/CampoTexto'
import Card from '../../components/Card'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import Modal from '../../components/Modal'
import Tabela from '../../components/Tabela'
import { useAuth } from '../../hooks/useAuth'
import { useCarga } from '../../hooks/useCarga'
import { cadastrarParada, obterRota, removerParada } from '../../services/rotas'
import {
  ehManaus,
  lerInteiroPositivo,
  NOME_MAXIMO,
  ordenarParadas,
  ORDEM_ORIGEM,
  ORIGEM_NOME,
  origemEhManaus,
  podeRemoverParada,
  sugestaoParada,
  validarParada,
} from '../../utils/frota'
import { ehAdministrador } from '../../utils/perfil'
import './DetalheRota.css'
import './Gestao.css'

function AdicionarParada({ rotaId, paradas, aoAdicionar }) {
  const sugestao = sugestaoParada(paradas)
  // null = usa a sugestão; assim ela se atualiza sozinha depois de cada parada adicionada.
  const [digitado, setDigitado] = useState({ nome: null, ordem: null })
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState('')
  const [enviando, setEnviando] = useState(false)

  const nome = digitado.nome ?? sugestao.nome
  const ordem = digitado.ordem ?? String(sugestao.ordem)

  function alterar(campo, valor) {
    setDigitado((atual) => ({ ...atual, [campo]: valor }))
    setErros((atual) => ({ ...atual, [campo]: undefined }))
  }

  async function enviar(evento) {
    evento.preventDefault()
    setErroGeral('')

    const errosValidacao = validarParada({ nome, ordem }, paradas)
    setErros(errosValidacao)
    if (Object.keys(errosValidacao).length > 0) return

    const numeroOrdem = lerInteiroPositivo(ordem)
    // Manaus sempre é gravado com a grafia certa, qualquer que seja a caixa digitada.
    const nomeFinal = ehManaus(nome) ? ORIGEM_NOME : nome.trim()

    setEnviando(true)
    try {
      aoAdicionar(await cadastrarParada(rotaId, { nome: nomeFinal, ordem: numeroOrdem }))
      setDigitado({ nome: null, ordem: null })
    } catch (erro) {
      const errosApi = {}
      for (const campo of ['nome', 'ordem']) {
        if (erro.erros?.[campo]) errosApi[campo] = erro.erros[campo]
      }

      setErros(errosApi)
      if (Object.keys(errosApi).length === 0) setErroGeral(erro.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Card titulo="Adicionar parada">
      <form onSubmit={enviar} noValidate>
        {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}

        <CampoTexto
          rotulo="Nome da parada"
          value={nome}
          onChange={(e) => alterar('nome', e.target.value)}
          erro={erros.nome}
          maxLength={NOME_MAXIMO}
          placeholder="Ex.: Coari"
          autoComplete="off"
        />

        <CampoTexto
          rotulo="Ordem na rota"
          type="number"
          inputMode="numeric"
          min="1"
          step="1"
          value={ordem}
          onChange={(e) => alterar('ordem', e.target.value)}
          erro={erros.ordem}
          ajuda="1 é a origem; as paradas seguintes recebem 2, 3, 4..."
        />

        <button type="submit" className="btn btn--primario btn--bloco" disabled={enviando}>
          {enviando ? 'Adicionando...' : 'Adicionar parada'}
        </button>
      </form>
    </Card>
  )
}

function RemoverParadaModal({ rotaId, parada, aoFechar, aoRemovida }) {
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function confirmar() {
    setErro('')
    setEnviando(true)
    try {
      await removerParada(rotaId, parada.id)
      aoRemovida(parada)
    } catch (falha) {
      setErro(falha.message)
      setEnviando(false)
    }
  }

  return (
    <Modal titulo="Remover parada" aoFechar={aoFechar} bloqueado={enviando}>
      {erro && <Alerta tipo="erro">{erro}</Alerta>}

      <p>
        Remover a parada <strong>{parada.nome}</strong> (ordem {parada.ordem}) desta rota?
      </p>
      <p className="texto-suave">As demais paradas mantêm a ordem que já têm.</p>

      <div className="modal__acoes">
        <button type="button" className="btn btn--contorno" onClick={aoFechar} disabled={enviando}>
          Cancelar
        </button>
        <button type="button" className="btn btn--perigo" onClick={confirmar} disabled={enviando}>
          {enviando ? 'Removendo...' : 'Remover parada'}
        </button>
      </div>
    </Modal>
  )
}

export default function DetalheRota() {
  const { rotaId } = useParams()
  const { usuario } = useAuth()
  const administrador = ehAdministrador(usuario)
  const carregar = useCallback(() => obterRota(rotaId), [rotaId])
  const { carregando, erro, dados: rota, recarregar, definirDados } = useCarga(carregar)
  const [paradaARemover, setParadaARemover] = useState(null)
  const [aviso, setAviso] = useState('')

  const voltar = (
    <Link to="/empresa/rotas" className="detalhe-rota__voltar">
      <ArrowLeft size={16} aria-hidden="true" />
      Voltar para rotas
    </Link>
  )

  if (carregando) return <Carregando />

  if (erro) {
    return (
      <>
        {voltar}
        {erro.status === 404 ? (
          <Alerta tipo="erro">Rota não encontrada. Ela pode ter sido removida.</Alerta>
        ) : (
          <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />
        )}
      </>
    )
  }

  const paradas = ordenarParadas(rota.paradas)

  function aoAdicionar(nova) {
    definirDados((atual) => ({ ...atual, paradas: [...atual.paradas, nova] }))
    setAviso(`Parada ${nova.nome} adicionada.`)
  }

  function aoRemovida(removida) {
    definirDados((atual) => ({ ...atual, paradas: atual.paradas.filter((p) => p.id !== removida.id) }))
    setAviso(`Parada ${removida.nome} removida.`)
    setParadaARemover(null)
  }

  const colunas = [
    { chave: 'ordem', titulo: 'Ordem', render: (p) => <span className="detalhe-rota__ordem">{p.ordem}</span> },
    {
      chave: 'nome',
      titulo: 'Parada',
      render: (p) => (
        <span className="gestao__nome">
          {p.nome}
          {p.ordem === ORDEM_ORIGEM && <small className="texto-suave"> · origem</small>}
        </span>
      ),
    },
  ]

  if (administrador) {
    colunas.push({
      chave: 'acoes',
      titulo: 'Ações',
      render: (p) => <BotaoRemover parada={p} paradas={paradas} aoClicar={setParadaARemover} />,
    })
  }

  return (
    <>
      {voltar}

      <h1 className="pagina__titulo">{rota.nome}</h1>
      <p className="pagina__subtitulo">Paradas na ordem em que a embarcação passa por elas.</p>

      {paradas.length > 0 && !origemEhManaus(paradas) ? (
        <Alerta tipo="erro">
          Esta rota não tem {ORIGEM_NOME} na ordem {ORDEM_ORIGEM}. A parada de ordem {ORDEM_ORIGEM}{' '}
          deve ser {ORIGEM_NOME}.
          {administrador && ` Remova a parada de ordem ${ORDEM_ORIGEM} e cadastre ${ORIGEM_NOME} no lugar.`}
        </Alerta>
      ) : (
        <Alerta tipo="info">
          Atenção: a parada de ordem {ORDEM_ORIGEM} deve ser <strong>{ORIGEM_NOME}</strong>, a origem de
          todas as rotas.
        </Alerta>
      )}

      {!administrador && (
        <Alerta tipo="info">Modo leitura: apenas administradores podem adicionar e remover paradas.</Alerta>
      )}
      {aviso && <Alerta tipo="sucesso">{aviso}</Alerta>}

      <div className={administrador ? 'detalhe-rota__corpo' : undefined}>
        <Card titulo="Sequência de paradas">
          {paradas.length === 0 ? (
            <div className="gestao__vazio">
              <MapPin size={36} aria-hidden="true" />
              <h2>Esta rota ainda não tem paradas</h2>
              <p className="texto-suave">
                {administrador
                  ? `Comece adicionando ${ORIGEM_NOME} na ordem ${ORDEM_ORIGEM}.`
                  : 'Um administrador ainda precisa cadastrar as paradas.'}
              </p>
            </div>
          ) : (
            <>
              <p className="detalhe-rota__sequencia">{paradas.map((p) => p.nome).join(' → ')}</p>

              <div className="detalhe-rota__tabela">
                <Tabela colunas={colunas} linhas={paradas} />
              </div>

              <ul className="gestao__cards detalhe-rota__cards" aria-label="Paradas da rota">
                {paradas.map((p) => (
                  <li key={p.id} className="gestao__cartao">
                    <span className="gestao__cartao-topo">
                      <span className="detalhe-rota__ordem">{p.ordem}</span>
                      <strong className="gestao__nome">{p.nome}</strong>
                      {p.ordem === ORDEM_ORIGEM && <span className="texto-suave">origem</span>}
                    </span>
                    {administrador && <BotaoRemover parada={p} paradas={paradas} aoClicar={setParadaARemover} />}
                  </li>
                ))}
              </ul>

              {administrador && paradas.length > 1 && (
                <p className="campo__ajuda detalhe-rota__dica">
                  {ORIGEM_NOME} (ordem {ORDEM_ORIGEM}) só pode ser removida depois das outras paradas.
                </p>
              )}
            </>
          )}
        </Card>

        {administrador && <AdicionarParada rotaId={rota.id} paradas={paradas} aoAdicionar={aoAdicionar} />}
      </div>

      {paradaARemover && (
        <RemoverParadaModal
          rotaId={rota.id}
          parada={paradaARemover}
          aoFechar={() => setParadaARemover(null)}
          aoRemovida={aoRemovida}
        />
      )}
    </>
  )
}

function BotaoRemover({ parada, paradas, aoClicar }) {
  const permitido = podeRemoverParada(parada, paradas)

  return (
    <button
      type="button"
      className="btn btn--contorno"
      onClick={() => aoClicar(parada)}
      disabled={!permitido}
      title={permitido ? undefined : `Remova antes as outras paradas: ${ORIGEM_NOME} é a origem da rota.`}
    >
      <Trash2 size={14} aria-hidden="true" />
      Remover
    </button>
  )
}
