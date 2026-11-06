import './Logo.css'

// Logo FLURIOS: barco sobre ondas + nome.
export default function Logo({ tamanho = 'normal' }) {
  return (
    <span className={`logo logo--${tamanho}`}>
      <svg className="logo__icone" viewBox="0 0 40 32" aria-hidden="true">
        <path d="M14 6h6v4h-6z" fill="#fff" />
        <path d="M10 10h18l3 6H7z" fill="#fff" />
        <path d="M13 12h3v2h-3zM18 12h3v2h-3zM23 12h3v2h-3z" fill="#135999" />
        <path
          d="M2 21q4-4 8 0t8 0 8 0 8 0 4 0"
          fill="none"
          stroke="#53bd92"
          strokeWidth="2.4"
          strokeLinecap="round"
        />
        <path
          d="M2 27q4-4 8 0t8 0 8 0 8 0 4 0"
          fill="none"
          stroke="#8fd6bb"
          strokeWidth="2.4"
          strokeLinecap="round"
        />
      </svg>
      <span className="logo__nome">FLURIOS</span>
    </span>
  )
}
