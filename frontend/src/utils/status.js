// Status da encomenda e da viagem (valores iguais aos da API) -> texto e cor.
export const STATUS = {
  // Encomenda
  pendente: { rotulo: 'Pendente', variante: 'amarelo' },
  recebida: { rotulo: 'Recebida', variante: 'azul' },
  aguardando_embarque: { rotulo: 'Aguardando embarque', variante: 'azul' },
  embarcada: { rotulo: 'Embarcada', variante: 'azul' },
  em_transito: { rotulo: 'Em trânsito', variante: 'azul' },
  chegou_ao_destino: { rotulo: 'Chegou ao destino', variante: 'verde-claro' },
  a_retirar: { rotulo: 'A retirar', variante: 'amarelo' },
  entregue: { rotulo: 'Entregue', variante: 'verde' },
  imprevisto: { rotulo: 'Imprevisto', variante: 'vermelho' },
  // Viagem
  programada: { rotulo: 'Programada', variante: 'azul' },
  em_andamento: { rotulo: 'Em andamento', variante: 'verde-claro' },
  concluida: { rotulo: 'Concluída', variante: 'verde' },
  cancelada: { rotulo: 'Cancelada', variante: 'vermelho' },
  // Embarcação
  ativa: { rotulo: 'Ativa', variante: 'verde-claro' },
  inativa: { rotulo: 'Inativa', variante: 'cinza' },
}


// Texto em português de um status (para telas e leitores de tela). Desconhecido volta como veio.
export function rotuloDoStatus(status) {
  return STATUS[status]?.rotulo ?? status
}
