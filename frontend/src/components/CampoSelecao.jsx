import { useId } from 'react'

// Lista de opções com rótulo e mensagem de erro (mesmo visual do CampoTexto).
// Passe <option> / <optgroup> como filhos.
export default function CampoSelecao({ rotulo, erro, ajuda, children, ...props }) {
  const id = useId()
  const idMensagem = `${id}-msg`

  return (
    <div className={`campo${erro ? ' campo--erro' : ''}`}>
      <label className="campo__rotulo" htmlFor={id}>
        {rotulo}
      </label>
      <select
        id={id}
        className="campo__entrada"
        aria-invalid={erro ? 'true' : undefined}
        aria-describedby={erro || ajuda ? idMensagem : undefined}
        {...props}
      >
        {children}
      </select>
      {erro ? (
        <span id={idMensagem} className="campo__erro" role="alert">
          {erro}
        </span>
      ) : (
        ajuda && (
          <span id={idMensagem} className="campo__ajuda">
            {ajuda}
          </span>
        )
      )}
    </div>
  )
}
