import { larguraBarra } from '../utils/dashboard'
import './BarraProgresso.css'

// Barra de progresso em CSS puro. `percentual` é o valor real (pode passar de 100: a barra enche
// e o texto mostra o número). `variante`: azul | verde | coral | ambar.
export default function BarraProgresso({ percentual, variante = 'azul', rotulo }) {
  return (
    <div
      className="barra"
      role="progressbar"
      aria-label={rotulo}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.min(100, percentual)}
      aria-valuetext={`${percentual}%`}
    >
      <span className={`barra__preenchimento barra__preenchimento--${variante}`} style={{ width: `${larguraBarra(percentual)}%` }} />
    </div>
  )
}
