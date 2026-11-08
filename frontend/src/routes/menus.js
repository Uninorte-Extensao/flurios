import {
  ChartColumn,
  CircleHelp,
  House,
  LayoutDashboard,
  Navigation,
  Package,
  PackageCheck,
  PackagePlus,
  Route,
  Ship,
} from 'lucide-react'
import { PERFIS_RETIRADA } from '../utils/retirada.js'

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
      { para: '/empresa/retiradas', rotulo: 'Retiradas', icone: PackageCheck, perfis: PERFIS_RETIRADA },
      { para: '/empresa/dashboard', rotulo: 'Dashboard', icone: ChartColumn },
    ],
    // A ordem é a prioridade: os 4 primeiros (já filtrados por perfil) ficam fixos e o resto vai
    // para o "Mais". Sem "Dashboard": Início (/empresa) já abre o mesmo painel.
    barraInferior: [
      { para: '/empresa', rotulo: 'Início', icone: House, exato: true },
      { para: '/empresa/encomendas', rotulo: 'Encomendas', icone: Package },
      { para: '/empresa/retiradas', rotulo: 'Retiradas', icone: PackageCheck, perfis: PERFIS_RETIRADA },
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
    itens: [
      { para: '/cliente', rotulo: 'Início', icone: House, exato: true },
      { para: '/cliente/nova-encomenda', rotulo: 'Nova encomenda', icone: PackagePlus },
      { para: '/cliente/encomendas', rotulo: 'Minhas encomendas', icone: Package },
    ],
    barraInferior: [
      { para: '/cliente', rotulo: 'Início', icone: House, exato: true },
      { para: '/cliente/nova-encomenda', rotulo: 'Nova encomenda', icone: PackagePlus },
      { para: '/cliente/encomendas', rotulo: 'Minhas encomendas', icone: Package },
    ],
    suporte: { para: '/cliente/suporte', rotulo: 'Suporte', icone: CircleHelp },
  },
}

export const ROTULOS_PERFIL_EMPRESA = {
  administrador: 'Administrador',
  atendente: 'Atendente',
  operador_embarcacao: 'Operador',
  funcionario_retirada: 'Funcionário',
}
