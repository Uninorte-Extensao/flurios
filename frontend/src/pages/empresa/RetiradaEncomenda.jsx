import { ArrowLeft, SearchX, UserRound } from 'lucide-react'
import { useCallback, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import CampoTexto from '../../components/CampoTexto'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import StatusBadge from '../../components/StatusBadge'
import { useCarga } from '../../hooks/useCarga'
import {
  buscarPessoaAutorizada,
  listarEncomendasDaEmpresa,
  registrarRetirada,
} from '../../services/encomendas'
import { formatarCpfDigitado, mascararCpf } from '../../utils/cpf'
import { formatarData } from '../../utils/data'
import { ROTULOS_STATUS } from '../../utils/gestaoEncomenda'
import {
  CAMINHO_FILA_RETIRADA,
  interpretarErroRetirada,
  motivoRetiradaIndisponivel,
  TEXTO_ACEITE,
  TEXTO_TERMO,
  TITULO_TERMO,
  validarRetirada,
} from '../../utils/retirada'
import './Gestao.css'
import './Encomendas.css'
import './Retirada.css'

const ORIGEM = 'Manaus'

// A busca por código é parcial; a encomenda é a de código igual. `encomenda: null` = não encontrada.
// A pessoa autorizada (CPF já mascarado pela API) vem de uma segunda chamada; `null` = não cadastrada.
async function carregarRetirada(codigo) {
  const lista = await listarEncomendasDaEmpresa({ busca: codigo, limite: 100 })
  const encomenda = lista.itens.find((i) => i.codigo_rastreio.toUpperCase() === codigo.toUpperCase())

  if (!encomenda) return { encomenda: null, pessoa: null }

  return { encomenda, pessoa: await buscarPessoaAutorizada(encomenda.id) }
}

function PessoaAutorizada({ pessoa }) {
  return (
    <Card titulo="Pessoa autorizada">
      {pessoa ? (
        <div className="retirada__pessoa">
          <UserRound size={22} aria-hidden="true" />
          <div>
            <strong>{pessoa.nome}</strong>
            <small className="texto-suave">CPF {mascararCpf(pessoa.cpf)}</small>
          </div>
        </div>
      ) : (
        <p className="texto-suave">Nenhuma pessoa autorizada cadastrada para esta encomenda.</p>
      )}
    </Card>
  )
}

// O CPF digitado fica só neste estado: não vai para URL, localStorage, log nem mensagem de erro.
function FormularioRetirada({ encomenda, aoRetirar }) {
  const [cpf, setCpf] = useState('')
  const [termoAceito, setTermoAceito] = useState(false)
  const [erros, setErros] = useState({})
  const [erroGeral, setErroGeral] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setErroGeral('')

    const encontrados = validarRetirada({ cpf, termoAceito })
    setErros(encontrados)
    if (Object.keys(encontrados).length > 0) return

    setEnviando(true)
    try {
      const retirada = await registrarRetirada(encomenda.id, { cpf, termoAceito })
      aoRetirar(retirada)
    } catch (falha) {
      const { cpf: erroCpf, geral } = interpretarErroRetirada(falha)
      setErros(erroCpf ? { cpf: erroCpf } : {})
      setErroGeral(geral)
      setEnviando(false)
    }
  }

  return (
    <Card titulo="Confirmar retirada">
      <form onSubmit={enviar} noValidate>
        {erroGeral && <Alerta tipo="erro">{erroGeral}</Alerta>}

        <CampoTexto
          rotulo="CPF de quem está retirando"
          inputMode="numeric"
          autoComplete="off"
          autoCorrect="off"
          spellCheck={false}
          maxLength={14}
          placeholder="000.000.000-00"
          ajuda="Digite o CPF do documento apresentado. Ele precisa ser o da pessoa autorizada."
          value={cpf}
          onChange={(e) => {
            setCpf(formatarCpfDigitado(e.target.value))
            setErros((atual) => ({ ...atual, cpf: undefined }))
            setErroGeral('')
          }}
          erro={erros.cpf}
        />

        <div className="retirada__termo" role="region" aria-label={TITULO_TERMO} tabIndex={0}>
          <h3>{TITULO_TERMO}</h3>
          {TEXTO_TERMO.map((paragrafo) => (
            <p key={paragrafo}>{paragrafo}</p>
          ))}
        </div>

        <div className={`campo campo--caixa${erros.termo ? ' campo--erro' : ''}`}>
          <input
            id="aceite-termo"
            type="checkbox"
            checked={termoAceito}
            aria-invalid={erros.termo ? 'true' : undefined}
            aria-describedby={erros.termo ? 'aceite-termo-erro' : undefined}
            onChange={(e) => {
              setTermoAceito(e.target.checked)
              setErros((atual) => ({ ...atual, termo: undefined }))
              setErroGeral('')
            }}
          />
          <label htmlFor="aceite-termo">{TEXTO_ACEITE}</label>
        </div>
        {erros.termo && (
          <span id="aceite-termo-erro" className="campo__erro retirada__erro-termo" role="alert">
            {erros.termo}
          </span>
        )}

        <button type="submit" className="btn btn--primario btn--bloco" disabled={enviando}>
          {enviando ? 'Registrando retirada...' : 'Confirmar retirada'}
        </button>
      </form>
    </Card>
  )
}

function Retirada({ codigo }) {
  const carregar = useCallback(() => carregarRetirada(codigo), [codigo])
  const { carregando, erro, dados, recarregar } = useCarga(carregar)
  const navegar = useNavigate()

  const voltar = (
    <Link to={CAMINHO_FILA_RETIRADA} className="encomenda__voltar">
      <ArrowLeft size={16} aria-hidden="true" />
      Voltar para a fila de retirada
    </Link>
  )

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
            <p className="texto-suave">
              Não encontramos nenhuma encomenda com o código <strong>{codigo}</strong>.
            </p>
          </div>
        </Card>
      </>
    )
  }

  const { encomenda, pessoa } = dados
  const motivo = motivoRetiradaIndisponivel(encomenda, pessoa, ROTULOS_STATUS[encomenda.status])

  // Sucesso: volta à fila com a confirmação (código e data/hora; nunca o CPF).
  function aoRetirar(retirada) {
    navegar(CAMINHO_FILA_RETIRADA, {
      state: { confirmacao: { codigo: encomenda.codigo_rastreio, entregueEm: retirada.criado_em } },
    })
  }

  return (
    <>
      {voltar}

      <div className="gestao__topo">
        <div>
          <h1 className="pagina__titulo">Retirada #{encomenda.codigo_rastreio}</h1>
          <p className="pagina__subtitulo">Confira os dados e o documento de quem está retirando.</p>
        </div>
        <StatusBadge status={encomenda.status} />
      </div>

      <div className="retirada__corpo">
        <div className="retirada__dados">
          <Card titulo="Dados da encomenda">
            <dl className="encomenda__dados">
              <div>
                <dt>Origem</dt>
                <dd>{ORIGEM}</dd>
              </div>
              <div>
                <dt>Destino</dt>
                <dd>{encomenda.destino_nome ?? '—'}</dd>
              </div>
              <div>
                <dt>Descrição</dt>
                <dd>{encomenda.descricao}</dd>
              </div>
              <div>
                <dt>Destinatário</dt>
                <dd>
                  {encomenda.destinatario.nome} · CPF {mascararCpf(encomenda.destinatario.cpf)}
                </dd>
              </div>
              <div>
                <dt>Cadastrada em</dt>
                <dd>{formatarData(encomenda.criado_em)}</dd>
              </div>
            </dl>
          </Card>

          <PessoaAutorizada pessoa={pessoa} />
        </div>

        <div className="retirada__acao">
          {motivo ? (
            <Card titulo="Confirmar retirada">
              <Alerta tipo="info">{motivo}</Alerta>
            </Card>
          ) : (
            <FormularioRetirada encomenda={encomenda} aoRetirar={aoRetirar} />
          )}
        </div>
      </div>
    </>
  )
}

export default function RetiradaEncomenda() {
  const { codigo } = useParams()

  // `key` zera o estado (inclusive o CPF digitado) ao trocar de código.
  return <Retirada key={codigo} codigo={codigo} />
}
