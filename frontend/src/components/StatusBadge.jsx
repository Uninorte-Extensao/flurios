import { STATUS, rotuloDoStatus } from '../utils/status'
import './StatusBadge.css'

export default function StatusBadge({ status }) {
  const variante = STATUS[status]?.variante ?? 'azul'

  return <span className={`badge badge--${variante}`}>{rotuloDoStatus(status)}</span>
}
