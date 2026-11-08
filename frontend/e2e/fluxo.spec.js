/* global process */
// Bateria ponta a ponta pelas telas: administrador, cliente, atendente e funcionário da retirada.
// Sobe sozinha (rodar.mjs): API + frontend em portas livres, banco temporário. Só testa e reporta.
import { expect, test } from '@playwright/test'
import {
  API_DIRETA,
  capturar,
  chamarApi,
  gravarAchados,
  loginApi,
  observar,
} from './ajudantes.js'

const SENHA = 'senha123'
const ADMIN = { email: process.env.E2E_ADMIN_EMAIL, senha: process.env.E2E_ADMIN_SENHA }
const ATENDENTE = { email: 'ana.atendente@flurios.com', nome: 'Ana Atendente' }
const RETIRADA = { email: 'rita.retirada@flurios.com', nome: 'Rita Retirada' }
const CLIENTE = { nome: 'maria souza', email: 'maria@exemplo.com', cpf: '111.222.333-96', cpfDigitos: '11122233396', telefone: '(92) 99999-0000' }
const DESTINATARIO = { nome: 'João Pereira', cpf: '222.333.444-05', telefone: '(97) 98888-7777', endereco: 'Rua das Flores, 123', municipio: 'Tefé' }
const AUTORIZADA = { nome: 'Carlos Souza', cpf: '333.444.555-08', cpfDigitos: '33344455508' }
const CPF_ERRADO = '529.982.247-25'

const estado = { codigo: '', codigo2: '' }
const contextos = {}
const paginas = {}

test.describe.configure({ mode: 'serial' })

async function entrar(page, { email, senha }, destino) {
  await page.goto('/login')
  await page.getByLabel('E-mail').fill(email)
  await page.getByLabel('Senha').fill(senha)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await page.waitForURL(destino)
}

async function escolherOpcao(page, rotulo, trecho) {
  const campo = page.getByLabel(rotulo, { exact: false }).first()
  // As opções chegam da API depois do primeiro desenho da tela: espera a lista ter mais que o "Escolha...".
  await expect.poll(async () => (await campo.locator('option').count()) > 1, { timeout: 10_000 }).toBe(true)
  const textos = await campo.locator('option').allTextContents()
  const indice = textos.findIndex((t) => t.includes(trecho))
  expect(indice, `opção com "${trecho}" em "${rotulo}" (opções: ${textos.join(' | ')})`).toBeGreaterThanOrEqual(0)
  await campo.selectOption({ index: indice })
}

async function abrirEncomendaEmpresa(page, codigo) {
  await page.goto(`/empresa/encomendas/${codigo}`)
  await expect(page.getByRole('heading', { name: new RegExp(`Encomenda #${codigo}`) })).toBeVisible()
}

async function mudarStatus(page, rotuloStatus) {
  await escolherOpcao(page, 'Novo status', rotuloStatus)
  await page.getByRole('button', { name: 'Atualizar status' }).click()
  await expect(page.getByText(rotuloStatus, { exact: true }).first()).toBeVisible()
}

async function criarEmpresa(token, nome, email, perfil) {
  await chamarApi('POST', '/usuarios', { nome, email, senha: SENHA })
  const { status } = await chamarApi('POST', '/empresas', { email, perfil }, token)
  expect(status).toBe(201)
}

async function programarViagem(page, { embarcacao, rota, saida }) {
  await page.goto('/empresa/viagens')
  await page.getByRole('button', { name: 'Programar viagem' }).first().click()
  const modal = page.getByRole('dialog')
  await escolherOpcao(modal, 'Embarcação', embarcacao)
  await escolherOpcao(modal, 'Rota', rota)
  await modal.getByLabel('Saída de Manaus').fill(saida)
  await modal.getByRole('button', { name: 'Programar viagem' }).click()
  await page.waitForURL(/\/empresa\/viagens\/\d+/)
  return Number(page.url().split('/').pop())
}

test.beforeAll(async ({ browser }) => {
  for (const papel of ['admin', 'atendente', 'retirada', 'cliente', 'anonimo']) {
    contextos[papel] = await browser.newContext({
      baseURL: process.env.E2E_FRONT_URL,
      locale: 'pt-BR',
      timezoneId: 'America/Manaus',
      viewport: { width: 1440, height: 900 },
    })
    paginas[papel] = await contextos[papel].newPage()
    observar(paginas[papel], papel)
  }

  // Massa mínima que não tem tela: contas de funcionários (hoje só a API cria; ver relatório).
  const token = await loginApi(ADMIN.email, ADMIN.senha)
  await criarEmpresa(token, ATENDENTE.nome, ATENDENTE.email, 'atendente')
  await criarEmpresa(token, RETIRADA.nome, RETIRADA.email, 'funcionario_retirada')
})

test.afterAll(async () => {
  gravarAchados({ apiDireta: API_DIRETA ? 'sim' : 'nao', codigos: estado })
  for (const contexto of Object.values(contextos)) await contexto.close()
})

test('01 login: validação, senha errada e telas públicas', async () => {
  const page = paginas.anonimo
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Entrar' })).toBeVisible()
  await capturar(page, 'login')

  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByText('Informe o e-mail.')).toBeVisible()
  await expect(page.getByText('Informe a senha.')).toBeVisible()
  await capturar(page, 'login-campos-obrigatorios')

  await page.getByLabel('E-mail').fill('ninguem@exemplo.com')
  await page.getByLabel('Senha').fill('senhaerrada')
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByText(/e-mail ou senha inv/i)).toBeVisible()
  await capturar(page, 'login-senha-errada')

  await page.goto('/empresa')
  await expect(page).toHaveURL(/\/login/)
})

test('02 administrador: painel vazio, embarcação, rota e paradas', async () => {
  const page = paginas.admin
  await entrar(page, ADMIN, /\/empresa$/)
  await expect(page.getByText('Painel Operacional').first()).toBeVisible()
  await capturar(page, 'admin-painel-vazio')

  await page.goto('/empresa/embarcacoes')
  await capturar(page, 'embarcacoes-vazio')
  await page.getByRole('button', { name: 'Nova embarcação' }).first().click()
  await page.getByLabel('Nome da embarcação').fill('Rio Negro I')
  await page.getByLabel('Capacidade (nº de encomendas)').fill('5')
  await capturar(page, 'embarcacao-modal-nova')
  await page.getByRole('button', { name: 'Cadastrar embarcação' }).click()
  await expect(page.getByText('Rio Negro I').first()).toBeVisible()
  await capturar(page, 'embarcacoes-lista')

  await page.goto('/empresa/rotas')
  await capturar(page, 'rotas-vazio')
  await page.getByRole('button', { name: 'Nova rota' }).first().click()
  await page.getByLabel('Nome da rota').fill('Manaus - Coari')
  await capturar(page, 'rota-modal-nova')
  await page.getByRole('button', { name: 'Cadastrar rota' }).click()
  await page.waitForURL(/\/empresa\/rotas\/\d+/)

  for (const [nome, ordem] of [['Manaus', '1'], ['Tefé', '2'], ['Coari', '3']]) {
    await page.getByLabel('Nome da parada').fill(nome)
    await page.getByLabel('Ordem na rota').fill(ordem)
    await page.getByRole('button', { name: 'Adicionar parada' }).click()
    await expect(page.locator('.detalhe-rota__sequencia')).toContainText(nome)
  }
  await capturar(page, 'rota-detalhe-com-paradas')

  await page.goto('/empresa/rotas')
  await capturar(page, 'rotas-lista')
})

test('03 cliente: cadastro pela tela e área inicial', async () => {
  const page = paginas.cliente
  await page.goto('/cadastro')
  await expect(page.getByRole('heading', { name: 'Criar conta de cliente' })).toBeVisible()
  await capturar(page, 'cadastro-cliente')

  await page.getByRole('button', { name: /criar conta|cadastrar/i }).click()
  await capturar(page, 'cadastro-cliente-erros')

  await page.getByLabel('Nome', { exact: false }).first().fill(CLIENTE.nome)
  await page.getByLabel('E-mail').fill(CLIENTE.email)
  await page.getByLabel('Senha', { exact: true }).fill(SENHA)
  await page.getByLabel('Confirmar senha', { exact: false }).fill(SENHA)
  await page.getByLabel('CPF').fill(CLIENTE.cpf)
  await page.getByLabel('Telefone').fill(CLIENTE.telefone)
  await page.getByRole('button', { name: /criar conta|cadastrar/i }).click()
  await page.waitForURL(/\/cliente$/)
  await capturar(page, 'cliente-inicio-sem-encomendas')

  await page.goto('/cliente/encomendas')
  await capturar(page, 'cliente-minhas-encomendas-vazio')
})

test('04 cliente: nova encomenda para Tefé com novo destinatário', async () => {
  const page = paginas.cliente
  await page.goto('/cliente/nova-encomenda')
  await capturar(page, 'cliente-nova-encomenda')

  await page.getByRole('button', { name: 'Cadastrar encomenda' }).click()
  await capturar(page, 'cliente-nova-encomenda-erros')

  await escolherOpcao(page, 'Destino', 'Tefé')
  await escolherOpcao(page, 'Quem vai receber', 'Cadastrar novo destinatário')
  await page.getByLabel('Nome do destinatário').fill(DESTINATARIO.nome)
  await page.getByLabel('CPF do destinatário').fill(DESTINATARIO.cpf)
  await page.getByLabel('Telefone do destinatário').fill(DESTINATARIO.telefone)
  await page.getByLabel('Endereço').fill(DESTINATARIO.endereco)
  await page.getByLabel('Município').fill(DESTINATARIO.municipio)
  await page.getByLabel('Descrição').fill('Caixa de ferramentas')
  await capturar(page, 'cliente-nova-encomenda-preenchida')

  await page.getByRole('button', { name: 'Cadastrar encomenda' }).click()
  const codigo = page.locator('.codigo-rastreio')
  await expect(codigo).toBeVisible()
  estado.codigo = (await codigo.innerText()).trim()
  expect(estado.codigo).toMatch(/^FLX/)
  await capturar(page, 'cliente-encomenda-cadastrada')
})

test('05 cliente: detalhe da encomenda e pessoa autorizada (CPF mascarado)', async () => {
  const page = paginas.cliente
  await page.goto('/cliente/encomendas')
  await expect(page.getByText(estado.codigo).first()).toBeVisible()
  await capturar(page, 'cliente-minhas-encomendas')

  await page.goto(`/cliente/encomendas/${estado.codigo}`)
  await expect(page.getByText('Linha do tempo')).toBeVisible()
  await capturar(page, 'cliente-detalhe-pendente-sem-autorizada')

  await page.getByRole('button', { name: 'Cadastrar pessoa autorizada' }).click()
  await page.getByLabel('Nome da pessoa autorizada').fill(AUTORIZADA.nome)
  await page.getByLabel('CPF da pessoa autorizada').fill(AUTORIZADA.cpf)
  await capturar(page, 'cliente-pessoa-autorizada-formulario')
  await page.getByRole('button', { name: 'Salvar' }).click()
  await expect(page.getByText(AUTORIZADA.nome).first()).toBeVisible()
  await expect(page.getByText('333.***.***-08').first()).toBeVisible()

  const corpo = await page.content()
  expect(corpo).not.toContain(AUTORIZADA.cpfDigitos)
  expect(corpo).not.toContain(AUTORIZADA.cpf)
  await capturar(page, 'cliente-detalhe-com-autorizada')
})

test('06 atendente: recebe a encomenda, programa viagem e associa', async () => {
  const page = paginas.atendente
  await entrar(page, { email: ATENDENTE.email, senha: SENHA }, /\/empresa$/)
  await capturar(page, 'atendente-painel')

  await page.goto('/empresa/encomendas')
  await expect(page.getByText(estado.codigo).first()).toBeVisible()
  await capturar(page, 'empresa-encomendas-lista')

  await abrirEncomendaEmpresa(page, estado.codigo)
  await capturar(page, 'empresa-encomenda-pendente')
  await mudarStatus(page, 'Recebida')
  await capturar(page, 'empresa-encomenda-recebida')

  await page.goto('/empresa/viagens')
  await capturar(page, 'viagens-vazio')
  await page.getByRole('button', { name: 'Programar viagem' }).first().click()
  const modal = page.getByRole('dialog')
  await escolherOpcao(modal, 'Embarcação', 'Rio Negro I')
  await escolherOpcao(modal, 'Rota', 'Manaus - Coari')
  await modal.getByLabel('Saída de Manaus').fill('2026-12-05T08:00')
  await capturar(page, 'viagem-modal-programar')
  await modal.getByRole('button', { name: 'Programar viagem' }).click()
  await page.waitForURL(/\/empresa\/viagens\/\d+/)
  estado.viagem1 = page.url()
  await capturar(page, 'viagem-programada-sem-encomendas')

  await page.getByRole('button', { name: 'Associar encomenda' }).first().click()
  await capturar(page, 'viagem-modal-associar-encomenda')
  await page.getByRole('dialog').getByRole('button', { name: 'Associar', exact: true }).first().click()
  await expect(page.getByText(/associada à viagem/i)).toBeVisible()
  await page.getByRole('dialog').getByRole('button', { name: 'Fechar' }).click()
  await capturar(page, 'viagem-programada-com-encomenda')

  await abrirEncomendaEmpresa(page, estado.codigo)
  await expect(page.getByText('Aguardando embarque').first()).toBeVisible()
  await capturar(page, 'empresa-encomenda-aguardando-embarque')
})

test('07 operação da viagem: iniciar, embarcar, localização em cada parada, chegada', async () => {
  const page = paginas.atendente
  await page.goto(estado.viagem1)
  await page.getByRole('button', { name: 'Iniciar viagem' }).click()
  await expect(page.getByText('Viagem iniciada.')).toBeVisible()
  await capturar(page, 'viagem-em-andamento')

  await abrirEncomendaEmpresa(page, estado.codigo)
  await mudarStatus(page, 'Embarcada')
  await capturar(page, 'empresa-encomenda-embarcada')

  await page.goto(estado.viagem1)
  for (const parada of ['Manaus', 'Tefé']) {
    await escolherOpcao(page, 'Parada em que a embarcação chegou', parada)
    await page.getByRole('button', { name: 'Registrar localização' }).click()
    await expect(page.getByText(new RegExp(`Localização registrada em ${parada}`))).toBeVisible()
    await capturar(page, `viagem-localizacao-${parada === 'Manaus' ? 'manaus' : 'tefe'}`)
  }

  await abrirEncomendaEmpresa(page, estado.codigo)
  await expect(page.getByText('Em trânsito').first()).toBeVisible()
  await capturar(page, 'empresa-encomenda-em-transito')
  await mudarStatus(page, 'Chegou ao destino')
  await mudarStatus(page, 'A retirar')
  await capturar(page, 'empresa-encomenda-a-retirar')
})

test('08 cliente acompanha: linha do tempo até "a retirar"', async () => {
  const page = paginas.cliente
  await page.goto(`/cliente/encomendas/${estado.codigo}`)
  await expect(page.getByText('Linha do tempo')).toBeVisible()
  await capturar(page, 'cliente-detalhe-a-retirar')
})

test('09 retirada: perfil sem acesso, CPF errado, termo e CPF certo', async () => {
  // O atendente não vê nem abre a retirada.
  const atendente = paginas.atendente
  await atendente.goto('/empresa/retiradas')
  await expect(atendente).not.toHaveURL(/\/empresa\/retiradas/)
  await capturar(atendente, 'atendente-sem-acesso-retirada')

  const page = paginas.retirada
  await entrar(page, { email: RETIRADA.email, senha: SENHA }, /\/empresa$/)
  await capturar(page, 'retirada-painel-funcionario')

  await page.goto('/empresa/retiradas')
  await expect(page.getByText(estado.codigo).first()).toBeVisible()
  await capturar(page, 'retirada-fila')

  await page.goto(`/empresa/retiradas/${estado.codigo}`)
  await expect(page.getByRole('heading', { name: new RegExp(`Retirada #${estado.codigo}`) })).toBeVisible()
  await expect(page.getByText('333.***.***-08').first()).toBeVisible()
  await capturar(page, 'retirada-encomenda')

  await page.getByRole('button', { name: 'Confirmar retirada' }).click()
  await capturar(page, 'retirada-validacao')

  await page.getByLabel('CPF de quem está retirando').fill(CPF_ERRADO)
  await page.getByRole('checkbox').check()
  await page.getByRole('button', { name: 'Confirmar retirada' }).click()
  await expect(page.getByRole('alert').first()).toBeVisible()
  await capturar(page, 'retirada-cpf-errado')

  await page.getByLabel('CPF de quem está retirando').fill(AUTORIZADA.cpf)
  await page.getByRole('button', { name: 'Confirmar retirada' }).click()
  // Sucesso: volta à fila de retirada com a confirmação (sem CPF).
  await page.waitForURL(/\/empresa\/retiradas$/)
  await expect(page.getByText(/entregue/i).first()).toBeVisible()
  const texto = await page.locator('main').innerText()
  expect(texto).not.toContain(AUTORIZADA.cpfDigitos)
  expect(texto).not.toContain(AUTORIZADA.cpf)
  await capturar(page, 'retirada-sucesso')
})

test('10 cliente: encomenda entregue com linha do tempo completa', async () => {
  const page = paginas.cliente
  await page.goto(`/cliente/encomendas/${estado.codigo}`)
  await expect(page.getByText('Entregue').first()).toBeVisible()
  await capturar(page, 'cliente-detalhe-entregue')
  await page.goto('/cliente/encomendas')
  await capturar(page, 'cliente-minhas-encomendas-entregue')
  await page.goto('/cliente')
  await capturar(page, 'cliente-inicio')
})

test('11 exceção: cancelar viagem, encomenda em imprevisto e realocar', async () => {
  const cliente = paginas.cliente
  await cliente.goto('/cliente/nova-encomenda')
  await escolherOpcao(cliente, 'Destino', 'Tefé')
  await escolherOpcao(cliente, 'Quem vai receber', DESTINATARIO.nome)
  await cliente.getByLabel('Descrição').fill('Sacos de farinha')
  await cliente.getByRole('button', { name: 'Cadastrar encomenda' }).click()
  const codigo = cliente.locator('.codigo-rastreio')
  await expect(codigo).toBeVisible()
  estado.codigo2 = (await codigo.innerText()).trim()
  await capturar(cliente, 'cliente-segunda-encomenda')

  const page = paginas.atendente
  await abrirEncomendaEmpresa(page, estado.codigo2)
  await mudarStatus(page, 'Recebida')

  const viagem2 = await programarViagem(page, { embarcacao: 'Rio Negro I', rota: 'Manaus - Coari', saida: '2026-12-10T08:00' })
  const viagem3 = await programarViagem(page, { embarcacao: 'Rio Negro I', rota: 'Manaus - Coari', saida: '2026-12-20T08:00' })
  expect(viagem3).toBeGreaterThan(viagem2)

  await page.goto(`/empresa/viagens/${viagem2}`)
  await page.getByRole('button', { name: 'Associar encomenda' }).first().click()
  await page.getByRole('dialog').getByRole('button', { name: 'Associar', exact: true }).first().click()
  await expect(page.getByText(/associada à viagem/i)).toBeVisible()
  await page.getByRole('dialog').getByRole('button', { name: 'Fechar' }).click()

  await page.getByRole('button', { name: 'Cancelar viagem' }).first().click()
  await capturar(page, 'viagem-modal-cancelar')
  await page.getByRole('dialog').getByRole('button', { name: 'Cancelar viagem' }).click()
  await expect(page.getByText('Viagem cancelada.')).toBeVisible()
  await capturar(page, 'viagem-cancelada')

  await abrirEncomendaEmpresa(page, estado.codigo2)
  await expect(page.getByText('Imprevisto').first()).toBeVisible()
  await capturar(page, 'empresa-encomenda-imprevisto')

  await cliente.goto(`/cliente/encomendas/${estado.codigo2}`)
  await expect(cliente.getByText('Imprevisto').first()).toBeVisible()
  await capturar(cliente, 'cliente-detalhe-imprevisto')

  await page.getByRole('button', { name: 'Realocar' }).click()
  const modal = page.getByRole('dialog')
  await expect(modal).toBeVisible()
  await capturar(page, 'empresa-realocar-escolha-viagem')
  await modal.getByRole('radio').first().check()
  await modal.getByRole('button', { name: 'Associar', exact: true }).click()
  await expect(page.getByText('Aguardando embarque').first()).toBeVisible()
  await capturar(page, 'empresa-encomenda-realocada')

  await cliente.goto(`/cliente/encomendas/${estado.codigo2}`)
  await capturar(cliente, 'cliente-detalhe-realocada')
})

test('12 painel e dashboard da empresa com dados', async () => {
  const page = paginas.admin
  await page.goto(estado.viagem1)
  await page.getByRole('button', { name: 'Concluir viagem' }).click()
  await expect(page.getByText('Viagem concluída.')).toBeVisible()
  await capturar(page, 'viagem-concluida')

  await page.goto('/empresa/viagens')
  await capturar(page, 'viagens-lista')

  await page.goto('/empresa/encomendas')
  await capturar(page, 'empresa-encomendas-lista-final')

  await page.goto('/empresa')
  await expect(page.getByText('Painel Operacional').first()).toBeVisible()
  await capturar(page, 'admin-painel-final')

  // Endereço antigo (F-5): redireciona para o painel, que tem um único item de menu.
  await page.goto('/empresa/dashboard')
  await expect(page).toHaveURL(/\/empresa$/)
  await expect(page.getByRole('heading', { name: 'Painel Operacional' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Dashboard' })).toHaveCount(0)
  await capturar(page, 'admin-dashboard-final')

  await page.goto('/empresa/embarcacoes')
  await capturar(page, 'embarcacoes-lista-final')
  await page.goto('/empresa/suporte')
  await capturar(page, 'empresa-suporte')
})

test('13 busca do cabeçalho, proteção de rotas e saída', async () => {
  const cliente = paginas.cliente
  await cliente.goto('/cliente')
  await cliente.getByRole('searchbox').fill(estado.codigo)
  await cliente.getByRole('searchbox').press('Enter')
  await expect(cliente).toHaveURL(new RegExp(`/cliente/encomendas/${estado.codigo}`))
  await capturar(cliente, 'cliente-busca-do-cabecalho')

  await cliente.goto('/cliente/encomendas/FLX0000000000')
  await capturar(cliente, 'cliente-codigo-inexistente')

  // Cliente não entra na área da empresa.
  await cliente.goto('/empresa')
  await expect(cliente).not.toHaveURL(/\/empresa/)

  const admin = paginas.admin
  await admin.goto('/empresa')
  await admin.getByRole('searchbox').fill(estado.codigo2)
  await admin.getByRole('searchbox').press('Enter')
  await expect(admin).toHaveURL(new RegExp(estado.codigo2))
  await capturar(admin, 'admin-busca-do-cabecalho')

  // Empresa não entra na área do cliente; rota inexistente volta ao início.
  await admin.goto('/cliente')
  await expect(admin).not.toHaveURL(/\/cliente/)
  await admin.goto('/pagina-que-nao-existe')
  await expect(admin).toHaveURL(/\/empresa$/)

  // Sair encerra a sessão.
  await admin.getByRole('button', { name: 'Sair' }).first().click()
  await expect(admin).toHaveURL(/\/login/)
  await admin.goto('/empresa')
  await expect(admin).toHaveURL(/\/login/)
})
