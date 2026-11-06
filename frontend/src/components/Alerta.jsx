// tipo: 'erro' | 'info' | 'sucesso'
export default function Alerta({ tipo = 'erro', children }) {
  return (
    <div className={`alerta alerta--${tipo}`} role={tipo === 'erro' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}
