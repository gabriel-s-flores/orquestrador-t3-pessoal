# Ambiente de teste, autenticação e limites

Os agentes testam só em **localhost e homologação**, com uma conta de teste configurada uma vez pelo usuário.
Produção, `main`, `master` e `develop` ficam **sempre fora** deste fluxo: nenhum push, merge, PR ou requisição.
Todo o código se consolida na branch do épico, por PR revisado.

## O que é permitido

| | Permitido | Proibido |
|---|---|---|
| Branches | criar a branch do épico; push nas branches de tarefa (`PREFIXO/*`, `sync/*`); PR com base na branch do épico | push, merge ou PR para `BRANCHES_PROTEGIDAS` (padrão `main master develop`); push direto, force-push ou apagar a branch do épico |
| Leitura | `fetch` de qualquer branch; trazer a `ORIGEM` para o épico pela tarefa de sincronização | — |
| Ambiente | `HML_URL` e os hosts de `HOSTS_PERMITIDOS` (localhost, homologação) | qualquer host fora da lista; `HOSTS_PROIBIDOS` (produção) é recusado com motivo |
| Credencial | a conta de **teste** de homologação, entregue pelo `hml exec` | conta pessoal, conta de produção, token pedido no chat |

## Autenticação sem pedir ao usuário

O usuário configura uma vez, num terminal (o valor não passa pelo agente):

```bash
<estado>/bin/hml guardar usuario      # conta de teste de homologação
<estado>/bin/hml guardar senha
<estado>/bin/hml guardar token        # se a API de homologação usa token
<estado>/bin/hml capturar             # login com SSO ou MFA: abre o Chrome, ele entra e fecha a janela
<estado>/bin/hml checar               # o que está guardado, sem mostrar valores
<estado>/bin/hml vivo                 # login de verdade: a homologação está no ar e aceita a conta de teste?
```

- As credenciais ficam no chaveiro do sistema (serviço `orq-hml`), separadas por **conta de teste** (`HML_CONTA`,
  ex.: `meuapp-hml`): orquestrações do mesmo projeto usam a mesma conta e não pedem nada de novo. Sem chaveiro,
  ou com `HML_COFRE=arquivo`, ficam em `~/.local/share/orquestrador-t3-pessoal/hml/<conta>/hml.env`, com permissão 600.
- A sessão capturada é um perfil do Chrome em `~/.local/share/orquestrador-t3-pessoal/hml/<conta>/chrome-hml/`. Ela vale até
  o sistema expirar o login.
- Os agentes rodam tudo o que precisa de login com `<estado>/bin/hml exec -- <comando>`, que:
  - recusa o comando se `HML_URL` não estiver em `HOSTS_PERMITIDOS`;
  - põe no ambiente do comando `HML_URL`, `HML_USUARIO`, `HML_SENHA`, `HML_TOKEN` e `HML_PERFIL` (uma cópia da sessão
    só para esta execução, apagada no fim, para os agentes não disputarem o mesmo perfil);
  - mascara os valores na saída.

No Playwright, use a sessão assim (o vídeo e o print seguem [`PROVAS.md`](PROVAS.md)):

```js
const ctx = await chromium.launchPersistentContext(process.env.HML_PERFIL, {
  channel: 'chrome', args: process.env.HML_CHROME_ARGS.split(' '),
  recordVideo: { dir: PASTA_DE_PROVAS, size: { width: 1280, height: 720 } },
});
const page = await ctx.newPage();
await page.goto(process.env.HML_URL);
```

Sem sessão capturada, o script de teste faz login com `HML_USUARIO` e `HML_SENHA` (seletores no `PROJETO.md` e em
`HML_LOGIN_*`).

**Sessão ou token expirou** (o teste caiu na tela de login): com usuário e senha guardados, o agente faz login de novo
pelo formulário e segue. Isso não é bloqueio nem motivo para chamar o usuário. Ele só conclui com `STATUS: BLOQUEADO`
se `hml vivo` não der `NO AR`, e o motivo é a linha `Resultado` do `hml vivo`. O orquestrador junta os bloqueios do
mesmo tipo e manda **um** pedido de decisão com o comando exato. As tarefas sem tela seguem enquanto isso.

## A homologação está no ar?

Responda sempre com `$E/bin/slot browser -- $E/bin/hml vivo`, nunca com `curl` na raiz de um servidor: 404 e 502 ali
não dizem se o login funciona, e o backend pode ter vários hosts, nem todos em uso. O `hml vivo`:

- abre um navegador limpo e faz o login pelo formulário com a conta de teste. Sessão ou token vencido não enganam a
  checagem;
- com `HML_URL` em localhost e a porta fechada, sobe o app com `HML_SERVIDOR` em `HML_SERVIDOR_DIR` (padrão:
  `CHECKOUT`, que precisa das dependências), segurando a trava `<estado>/locks/porta-<porta>.lock`, e derruba o app
  no fim. Com a porta já aberta (o servidor de um agente), usa o que está de pé;
- tenta de novo uma vez, depois de 20 s, se não teve resposta.

| Resultado | O que quer dizer | O que fazer |
|---|---|---|
| `NO AR` (saída 0) | o login passou | seguir |
| `CREDENCIAL RECUSADA` (10) | a homologação respondeu e recusou a conta | pedir ao usuário `hml guardar senha` (a senha mudou) |
| `FORA DO AR` (11) | o login não teve resposta, ou teve 5xx | tarefas com tela esperam; conferir de novo a cada heartbeat |
| `ROTEIRO FALHOU` (12) | a tela de login não é a esperada | ajustar `HML_LOGIN_*` no `orq.env`, sem chamar o usuário |
| `SERVIDOR LOCAL NÃO SUBIU` (13) | o app local não abriu a porta | ler o log mostrado; conferir `HML_SERVIDOR` e as dependências |
| `SEM LOGIN AUTOMÁTICO` (14) | não há senha guardada, e a sessão capturada falta ou venceu | pedir `hml guardar` (ou `hml capturar`, com SSO ou MFA) |

O roteiro padrão (`bin/hml-login.js`) usa os seletores `HML_LOGIN_USUARIO`, `HML_LOGIN_SENHA`, `HML_LOGIN_BOTAO` e
`HML_LOGIN_OK`, e aceita login em duas etapas (e-mail, Avançar, senha). Um login diferente vai num roteiro próprio
(`HML_LOGIN_ROTEIRO`), com os mesmos códigos de saída.

## As camadas de proteção

1. **Briefs:** os limites estão escritos para o implementador e o revisor.
2. **Hook de `pre-push` nas worktrees dos agentes** (`guarda.py instalar <worktree>`, primeiro passo de cada agente):
   bloqueia push para branches protegidas, push direto e remoção do épico. Vale só para aquela worktree
   (`core.hooksPath` por worktree). O checkout do usuário não muda, e os hooks do repositório (husky inclusive)
   continuam rodando, encadeados.
3. **Antes de todo merge:** `guarda.py pr <n>` exige base = branch do épico e head fora das protegidas.
4. **URLs:** `hml exec` e `prova --tipo requisicao` recusam hosts fora de `HOSTS_PERMITIDOS`. `guarda.py texto <arquivos>`
   acha referências a produção nos `.env` e nas configurações usadas para subir o ambiente local.
5. **No servidor:** confirme na montagem se a `main` tem proteção de branch no GitHub. É a única camada que vale
   também fora desta máquina.

## Configuração (`orq.env`)

```bash
BRANCHES_PROTEGIDAS="main master develop"
ORIGEM="main"                                   # de onde o épico nasce e que ele acompanha (só leitura)
HML_URL="http://localhost:3000"                 # onde os agentes testam
HML_LOGIN_URL=""                                # página de login, se for outra
HOSTS_PERMITIDOS="localhost 127.0.0.1 ::1 *.hml.<dominio>"
HOSTS_PROIBIDOS="<dominio> *.<dominio>"         # produção: recusada e apontada nas varreduras
HML_CONTA="meuapp-hml"                          # conta de teste compartilhada pelas orquestrações do projeto
HML_COFRE="chaveiro"                            # chaveiro | arquivo
HML_LOGIN_USUARIO='[placeholder="Insira seu e-mail"]'   # seletores do login, para o hml vivo
HML_LOGIN_SENHA='[placeholder="Insira sua senha"]'
HML_LOGIN_BOTAO='text=Entrar no sistema'
HML_LOGIN_OK="/home"                            # trecho da URL depois do login
HML_SERVIDOR="PORT=3000 BROWSER=none yarn start"   # sobe o app local quando a porta está fechada
```
