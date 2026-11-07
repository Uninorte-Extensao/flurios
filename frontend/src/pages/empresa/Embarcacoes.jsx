import { Pencil, Plus, Ship } from 'lucide-react'
import { useState } from 'react'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import StatusBadge from '../../components/StatusBadge'
import Tabela from '../../components/Tabela'
import { useAuth } from '../../hooks/useAuth'
import { useCarga } from '../../hooks/useCarga'
import { listarEmbarcacoes } from '../../services/embarcacoes'
import { ehAdministrador } from '../../utils/perfil'
import EmbarcacaoModal from './EmbarcacaoModal'
import './Gestao.css'

const porNome = (a, b) => a.nome.localeCompare(b.nome, 'pt-BR')

export default function Embarcacoes() {
  const { usuario } = useAuth()
  const administrador = ehAdministrador(usuario)
  const { carregando, erro, dados, recarregar, definirDados } = useCarga(listarEmbarcacoes)
  // null = fechado; { embarcacao: null } = cadastro; { embarcacao } = edição.
  const [modal, setModal] = useState(null)
  const [aviso, setAviso] = useState('')

  function aoSalvar(salva, editando) {
    definirDados((lista) =>
      (editando ? lista.map((e) => (e.id === salva.id ? salva : e)) : [...lista, salva]).sort(porNome),
    )
    setAviso(editando ? 'Embarcação atualizada.' : 'Embarcação cadastrada.')
    setModal(null)
  }

  function abrir(embarcacao) {
    setAviso('')
    setModal({ embarcacao })
  }

  const embarcacoes = dados ?? []
  const pronto = !carregando && !erro
  const botaoNova = administrador && (
    <button type="button" className="btn btn--primario" onClick={() => abrir(null)}>
      <Plus size={16} aria-hidden="true" />
      Nova embarcação
    </button>
  )

  const colunas = [
    { chave: 'nome', titulo: 'Embarcação', render: (e) => <span className="gestao__nome">{e.nome}</span> },
    { chave: 'capacidade', titulo: 'Capacidade (encomendas)' },
    { chave: 'ativa', titulo: 'Situação', render: (e) => <StatusBadge status={e.ativa ? 'ativa' : 'inativa'} /> },
  ]

  if (administrador) {
    colunas.push({
      chave: 'acoes',
      titulo: 'Ações',
      render: (e) => (
        <button type="button" className="btn btn--contorno" onClick={() => abrir(e)}>
          <Pencil size={14} aria-hidden="true" />
          Editar
        </button>
      ),
    })
  }

  return (
    <>
      <div className="gestao__topo">
        <div>
          <h1 className="pagina__titulo">Embarcações</h1>
          <p className="pagina__subtitulo">Frota usada nas viagens entre Manaus e o interior.</p>
        </div>
        {pronto && embarcacoes.length > 0 && botaoNova}
      </div>

      {!administrador && (
        <Alerta tipo="info">Modo leitura: apenas administradores podem cadastrar e editar embarcações.</Alerta>
      )}
      {aviso && <Alerta tipo="sucesso">{aviso}</Alerta>}

      {carregando && <Carregando />}
      {erro && <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />}

      {pronto && embarcacoes.length === 0 && (
        <Card>
          <div className="gestao__vazio">
            <Ship size={36} aria-hidden="true" />
            <h2>Nenhuma embarcação cadastrada</h2>
            <p className="texto-suave">
              {administrador
                ? 'Cadastre a primeira embarcação para poder programar viagens.'
                : 'Quando um administrador cadastrar as embarcações, elas aparecerão aqui.'}
            </p>
            {botaoNova}
          </div>
        </Card>
      )}

      {pronto && embarcacoes.length > 0 && (
        <>
          <Card className="gestao__tabela">
            <Tabela colunas={colunas} linhas={embarcacoes} />
          </Card>

          <ul className="gestao__cards" aria-label="Lista de embarcações">
            {embarcacoes.map((e) => (
              <li key={e.id} className="gestao__cartao">
                <span className="gestao__cartao-topo">
                  <strong className="gestao__nome">{e.nome}</strong>
                  <StatusBadge status={e.ativa ? 'ativa' : 'inativa'} />
                </span>
                <span className="gestao__cartao-rodape texto-suave">
                  Capacidade: {e.capacidade} encomendas
                </span>
                {administrador && (
                  <button type="button" className="btn btn--contorno" onClick={() => abrir(e)}>
                    <Pencil size={14} aria-hidden="true" />
                    Editar
                  </button>
                )}
              </li>
            ))}
          </ul>
        </>
      )}

      {modal && (
        <EmbarcacaoModal
          embarcacao={modal.embarcacao}
          aoFechar={() => setModal(null)}
          aoSalvar={aoSalvar}
        />
      )}
    </>
  )
}
