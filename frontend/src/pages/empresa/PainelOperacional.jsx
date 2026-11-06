import Card from '../../components/Card'
import { useAuth } from '../../hooks/useAuth'

// Provisório: o painel completo (KPIs, mapa, envios ativos) vem nas tarefas F.6/F.8.
export default function PainelOperacional() {
  const { usuario } = useAuth()

  return (
    <>
      <h1 className="pagina__titulo">Painel Operacional</h1>
      <p className="pagina__subtitulo">Visão geral das operações e movimentações do sistema FLURIOS.</p>
      <Card titulo={`Olá, ${usuario.nome}`}>
        <p className="texto-suave">Você está na área da empresa. Os indicadores chegam nas próximas telas.</p>
      </Card>
    </>
  )
}
