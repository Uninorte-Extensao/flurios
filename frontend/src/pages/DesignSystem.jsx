import Card from '../components/Card'
import CampoTexto from '../components/CampoTexto'
import Alerta from '../components/Alerta'
import StatusBadge from '../components/StatusBadge'
import Tabela from '../components/Tabela'

const STATUS = [
  'pendente',
  'recebida',
  'aguardando_embarque',
  'embarcada',
  'em_transito',
  'chegou_ao_destino',
  'a_retirar',
  'entregue',
  'imprevisto',
  'programada',
  'em_andamento',
  'concluida',
  'cancelada',
]

const LINHAS = [
  { id: 1, codigo: 'FLU-0001', destinatario: 'Contarto Manacapuru', destino: 'Manaus', status: 'em_transito' },
  { id: 2, codigo: 'FLU-0002', destinatario: 'Cominanto Coari', destino: 'Coari', status: 'pendente' },
  { id: 3, codigo: 'FLU-0003', destinatario: 'Conto do Manaus', destino: 'Tefé', status: 'entregue' },
  { id: 4, codigo: 'FLU-0004', destinatario: 'Cominanto Manaus', destino: 'Coari', status: 'imprevisto' },
]

const COLUNAS = [
  { chave: 'codigo', titulo: 'Código Rastreio' },
  { chave: 'destinatario', titulo: 'Destinatário' },
  { chave: 'destino', titulo: 'Destino' },
  { chave: 'status', titulo: 'Status', render: (linha) => <StatusBadge status={linha.status} /> },
]

// Vitrine do design system — disponível só em desenvolvimento (rota /design-system).
export default function DesignSystem() {
  return (
    <div style={{ padding: 'var(--espaco-5)', display: 'grid', gap: 'var(--espaco-4)', maxWidth: 900, margin: '0 auto' }}>
      <h1>Design system Flurios</h1>

      <Card titulo="Badges de status">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--espaco-2)' }}>
          {STATUS.map((status) => (
            <StatusBadge key={status} status={status} />
          ))}
        </div>
      </Card>

      <Card titulo="KPI" acoes={<span className="texto-suave">vs. semana passada</span>}>
        <p className="card__kpi">3.150</p>
      </Card>

      <Card titulo="Tabela">
        <Tabela colunas={COLUNAS} linhas={LINHAS} />
      </Card>

      <Card titulo="Formulário e botões">
        <CampoTexto rotulo="E-mail" placeholder="voce@exemplo.com" ajuda="Texto de ajuda." />
        <CampoTexto rotulo="CPF" defaultValue="123" erro="CPF inválido." />
        <Alerta tipo="erro">Mensagem de erro.</Alerta>
        <Alerta tipo="info">Mensagem informativa.</Alerta>
        <Alerta tipo="sucesso">Mensagem de sucesso.</Alerta>
        <div style={{ display: 'flex', gap: 'var(--espaco-2)', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn--primario">Primário</button>
          <button type="button" className="btn btn--sucesso">Sucesso</button>
          <button type="button" className="btn btn--contorno">Contorno</button>
          <button type="button" className="btn btn--primario" disabled>Desabilitado</button>
        </div>
      </Card>
    </div>
  )
}
