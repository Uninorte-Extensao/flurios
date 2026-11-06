import {
  ChartColumn,
  CircleHelp,
  House,
  LayoutDashboard,
  Navigation,
  Package,
  Route,
  Ship,
} from 'lucide-react'

// Menu lateral (web) e barra inferior (mobile) de cada área.
export const MENUS = {
  empresa: {
    base: '/empresa',
    rotuloUsuario: 'Operador',
    placeholderBusca: 'Buscar carga, viagem...',
    itens: [
      { para: '/empresa', rotulo: 'Painel Operacional', icone: LayoutDashboard, exato: true },
      { para: '/empresa/embarcacoes', rotulo: 'Embarcações', icone: Ship },
      { para: '/empresa/rotas', rotulo: 'Rotas', icone: Route },
      { para: '/empresa/viagens', rotulo: 'Viagens', icone: Navigation },
      { para: '/empresa/encomendas', rotulo: 'Encomendas', icone: Package },
      { para: '/empresa/dashboard', rotulo: 'Dashboard', icone: ChartColumn },
    ],
    barraInferior: [
      { para: '/empresa', rotulo: 'Início', icone: House, exato: true },
      { para: '/empresa/encomendas', rotulo: 'Encomendas', icone: Package },
      { para: '/empresa/viagens', rotulo: 'Viagens', icone: Navigation },
      { para: '/empresa/embarcacoes', rotulo: 'Embarcações', icone: Ship },
      { para: '/empresa/rotas', rotulo: 'Rotas', icone: Route },
    ],
    suporte: { para: '/empresa/suporte', rotulo: 'Suporte', icone: CircleHelp },
  },
  cliente: {
    base: '/cliente',
    rotuloUsuario: 'Cliente',
    placeholderBusca: 'Digite seu código de rastreio...',
    itens: [{ para: '/cliente', rotulo: 'Minhas Encomendas', icone: Package, exato: true }],
    barraInferior: [{ para: '/cliente', rotulo: 'Início', icone: House, exato: true }],
    suporte: { para: '/cliente/suporte', rotulo: 'Suporte', icone: CircleHelp },
  },
}

export const ROTULOS_PERFIL_EMPRESA = {
  administrador: 'Administrador',
  atendente: 'Atendente',
  operador_embarcacao: 'Operador',
  funcionario_retirada: 'Funcionário',
}
