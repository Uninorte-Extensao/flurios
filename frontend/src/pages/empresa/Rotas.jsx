import { Plus, Route as IconeRota } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Alerta from '../../components/Alerta'
import Card from '../../components/Card'
import Carregando from '../../components/Carregando'
import ErroCarga from '../../components/ErroCarga'
import Tabela from '../../components/Tabela'
import { useAuth } from '../../hooks/useAuth'
import { useCarga } from '../../hooks/useCarga'
import { listarRotas } from '../../services/rotas'
import { formatarData } from '../../utils/data'
import { ehAdministrador } from '../../utils/perfil'
import RotaModal from './RotaModal'
import './Gestao.css'

const caminhoDetalhe = (rota) => `/empresa/rotas/${rota.id}`

export default function Rotas() {
  const { usuario } = useAuth()
  const navegar = useNavigate()
  const administrador = ehAdministrador(usuario)
  const { carregando, erro, dados, recarregar } = useCarga(listarRotas)
  const [modalAberto, setModalAberto] = useState(false)

  // A rota nova ainda não tem paradas: leva direto ao detalhe para cadastrá-las.
  function aoSalvar(rota) {
    navegar(caminhoDetalhe(rota))
  }

  const rotas = dados ?? []
  const pronto = !carregando && !erro
  const botaoNova = administrador && (
    <button type="button" className="btn btn--primario" onClick={() => setModalAberto(true)}>
      <Plus size={16} aria-hidden="true" />
      Nova rota
    </button>
  )

  const colunas = [
    {
      chave: 'nome',
      titulo: 'Rota',
      render: (r) => (
        <Link to={caminhoDetalhe(r)} className="gestao__nome">
          {r.nome}
        </Link>
      ),
    },
    { chave: 'criado_em', titulo: 'Cadastrada em', render: (r) => formatarData(r.criado_em) },
    {
      chave: 'acoes',
      titulo: 'Ações',
      render: (r) => (
        <Link to={caminhoDetalhe(r)} className="btn btn--contorno">
          Ver paradas
        </Link>
      ),
    },
  ]

  return (
    <>
      <div className="gestao__topo">
        <div>
          <h1 className="pagina__titulo">Rotas</h1>
          <p className="pagina__subtitulo">Trajetos fluviais e suas paradas, partindo de Manaus.</p>
        </div>
        {pronto && rotas.length > 0 && botaoNova}
      </div>

      {!administrador && (
        <Alerta tipo="info">Modo leitura: apenas administradores podem cadastrar rotas e paradas.</Alerta>
      )}

      {carregando && <Carregando />}
      {erro && <ErroCarga mensagem={erro.message} aoTentarDeNovo={recarregar} />}

      {pronto && rotas.length === 0 && (
        <Card>
          <div className="gestao__vazio">
            <IconeRota size={36} aria-hidden="true" />
            <h2>Nenhuma rota cadastrada</h2>
            <p className="texto-suave">
              {administrador
                ? 'Cadastre a primeira rota e depois adicione as paradas dela, começando por Manaus.'
                : 'Quando um administrador cadastrar as rotas, elas aparecerão aqui.'}
            </p>
            {botaoNova}
          </div>
        </Card>
      )}

      {pronto && rotas.length > 0 && (
        <>
          <Card className="gestao__tabela">
            <Tabela colunas={colunas} linhas={rotas} />
          </Card>

          <ul className="gestao__cards" aria-label="Lista de rotas">
            {rotas.map((r) => (
              <li key={r.id} className="gestao__cartao">
                <Link to={caminhoDetalhe(r)} className="gestao__nome">
                  {r.nome}
                </Link>
                <span className="gestao__cartao-rodape texto-suave">
                  Cadastrada em {formatarData(r.criado_em)}
                </span>
                <Link to={caminhoDetalhe(r)} className="btn btn--contorno">
                  Ver paradas
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}

      {modalAberto && <RotaModal aoFechar={() => setModalAberto(false)} aoSalvar={aoSalvar} />}
    </>
  )
}
