import { useEffect, useId, useRef } from 'react'
import './Modal.css'

// Janela de diálogo (elemento <dialog> nativo: foco preso, Esc fecha, fundo bloqueado).
// Renderize só quando estiver aberta. `bloqueado` impede fechar (ex.: enquanto salva).
export default function Modal({ titulo, aoFechar, bloqueado = false, className = '', children }) {
  const ref = useRef(null)
  const idTitulo = useId()

  useEffect(() => {
    const dialogo = ref.current
    if (dialogo && !dialogo.open) dialogo.showModal()

    return () => {
      if (dialogo?.open) dialogo.close()
    }
  }, [])

  function aoCancelar(evento) {
    // Esc: o fechamento passa sempre pelo estado da tela.
    evento.preventDefault()
    if (!bloqueado) aoFechar()
  }

  return (
    <dialog ref={ref} className={`modal ${className}`.trim()} aria-labelledby={idTitulo} onCancel={aoCancelar}>
      <div className="modal__conteudo">
        <h2 id={idTitulo} className="modal__titulo">
          {titulo}
        </h2>
        {children}
      </div>
    </dialog>
  )
}
