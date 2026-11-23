# Montagem de uma orquestração nova

Etapas, em ordem. Cada uma termina no critério em **negrito**. As etapas 1, 2, 3, 5, 6 e 7 precisam do usuário.
`S=~/.claude/skills/orquestrador-t3-pessoal`. Toda mensagem ao usuário segue [`escrita/ESCRITA.md`](escrita/ESCRITA.md);
as perguntas ao usuário vão pelo painel do `AskUserQuestion`, uma por vez, conferidas com `texto.py --tipo pergunta`
([`sabatina/SABATINA.md`](sabatina/SABATINA.md)).

## 1. Planejamento: sabatina

Faça a sabatina ([`sabatina/SABATINA.md`](sabatina/SABATINA.md)) até a fronteira esvaziar. Com vocabulário de domínio
em jogo, use junto a modelagem ([`sabatina/MODELAGEM.md`](sabatina/MODELAGEM.md)): o glossário e as decisões vão para
a pasta de estado.

O resultado vai para `$E/PLANO.md`: objetivo, fim, requisitos numerados (`R1`, `R2`…), **não-objetivos**, decisões e
riscos. Se o projeto já tem uma especificação (issue, documento, README de design), ela é a entrada da sabatina, não
um substituto dela.

**Pronto quando o `PLANO.md` está aprovado pelo usuário e os não-objetivos estão escritos.**

## 2. Sabatina da orquestração

Mais uma rodada de sabatina, agora sobre como rodar. Os ramos obrigatórios da árvore:

- o "fim" da orquestração;
- o repositório no GitHub e a **branch do épico** (`BASE`, ex.: `epico-login`), criada a partir da `ORIGEM` (só
  leitura): ela recebe todas as tarefas, e o fluxo termina nela;
- as **branches protegidas** (`BRANCHES_PROTEGIDAS`, padrão `main master develop`), que nunca recebem push, merge
  nem PR do fluxo, e se elas têm proteção no GitHub;
- o **ambiente de teste**: a `HML_URL` local, o domínio de homologação, se houver (`HOSTS_PERMITIDOS`), os domínios de
  produção (`HOSTS_PROIBIDOS`), o `.env` que o app local usa, e o login: conta de teste, sessão capturada (SSO ou MFA)
  ou token. Projeto sem login: deixe `HML_CONTA` vazio;
- as **provas** por tipo de tarefa (tela: print e vídeo; API: requisição; desempenho: medição) e se o resumo delas vai
  como comentário no PR (`PROVAS_PR`, padrão `comentario`). Em repositório público o comentário é público: confirme com
  o usuário, e use `desligado` se ele preferir;
- a **revisão**: rodadas depois da primeira curtas (`REVISAO_RODADA`, padrão `curta`) e revisão final do épico
  (`REVISAO_FINAL`: `conselho`, `unico` ou `nao`), em [`REVISAO.md`](REVISAO.md);
- a **suíte longa** (`SUITE_LONGA`): se o projeto tem uma suíte de dezenas de minutos, ela roda na ponta do épico
  depois dos merges e nos gates, e não em cada head de PR ([`INTEGRACAO.md`](INTEGRACAO.md)). Se o usuário quiser a
  suíte por PR, escreva no `PROJETO.md` que cada devolutiva e cada atualização da base repetem a rodada;
- a **integração** ([`INTEGRACAO.md`](INTEGRACAO.md)):
  - os PRs aprovados entram um por vez (`FILA_INTEGRACAO`, padrão `sim`), e só quem tem a vez traz a base;
  - PR atrás da base com merge limpo entra sem trazê-la, e as checagens rodam na ponta do épico (`MERGE_LIMPO`,
    padrão `direto`). O custo: um conflito que o git não vê pode chegar ao épico e só aparecer minutos depois, na
    checagem de ponta. Com `atualizar`, cada PR é conferido em cima da base antes do merge, ao preço de uma
    atualização com agente por PR;
  - o comando das checagens na ponta (`CHECAGEM_PONTA`; vazio vale a tabela de checagens do `PROJETO.md`);
  - o teto de PRs abertos (`MAX_PRS_ABERTOS`; vazio vale `MAX_AGENTES` + 1): acima dele, nenhuma implementação nova;
  - se ele autoriza rebase com `--force-with-lease` só na branch da tarefa (`REBASE_FORCADO`, padrão `nao`: a base
    entra por `git merge`);
- o **PR final** (`PR_FINAL`, padrão `nao`): se no fechamento você abre o PR da branch do épico para a `ORIGEM`,
  pronto para ele revisar e sem merge. É a única exceção à regra de nenhum PR para branch protegida
  ([`AMBIENTE.md`](AMBIENTE.md));
- o projeto no T3 (`t3_project_list`, ou o projeto desta thread);
- o que ele autoriza sem perguntar: criar e assentar agentes, criar a branch do épico, push em `<PREFIXO>/*`, PRs,
  merge na branch do épico depois de revisão aprovada e provada, trazer a base para a branch de um PR aprovado
  quando o merge é limpo (`gh pr update-branch`), a tarefa de sincronização com a `ORIGEM`, comentários nos PRs;
- o que ele não autoriza: branches dele, force-push (fora o `--force-with-lease` na branch da tarefa, se ele ligar
  `REBASE_FORCADO`), contas, dispositivos reais, serviços pagos…;
- as premissas técnicas e as checagens obrigatórias (lint, testes, builds) com os limites de paralelismo de cada
  ferramenta (`--maxWorkers`, `-p`, `-j`);
- a validação externa antes do merge (se houver) e se ela exige autorização a cada vez;
- pausa e retomada automáticas (ex.: pausar às 23:00 e retomar às 08:00).

Fatos (a branch padrão, se existe script de setup no T3, se o repositório é público) são seus: busque com um subagente
Haiku (agente `Explore` com `model: "haiku"`; sem o `model`, ele roda no modelo desta thread).

**Pronto quando cada ramo tem resposta ou um padrão que ele aceitou.**

## 3. Revisor e modelos

1. `orchestrator_capabilities`: descubra os modelos disponíveis e quais provedores têm `canRunChildTask: true`.
2. Pergunte com `AskUserQuestion`, numa chamada só, pulando o que o usuário já escolheu no pedido:
   - **Revisor de código:** de preferência uma família diferente da do implementador, porque os pontos cegos não
     coincidem. Com o Codex no catálogo: `GPT-6.1-Sol · low (Recomendado)`, `GPT-6.1-Sol · medium`. Sem ele, ou como
     alternativa: `Claude Opus 5.5 · high`, `Claude Fable 5.2 · medium`. Mostre só os que o catálogo tem.
   - **Revisor nas classes G e GG:** `O mesmo, um nível acima (Recomendado)` ou `Igual ao revisor padrão`.
   - **Implementadores:** `Padrão da skill (Recomendado)` (tabela de [`MODELOS.md`](MODELOS.md)), `Mais qualidade`
     (P → Sonnet 5.5 high; M → Opus 5.5 medium) ou `Mais economia` (M → Sonnet 5.5 medium; G → Opus 5.5 medium;
     GG → Fable 5.2 medium). Nenhuma opção passa de `high`: acima disso o guia da Anthropic manda testar o modelo
     seguinte num effort menor.
   - **Orquestrador do loop:** `Opus 5.5 · medium (Recomendado)` ou `Fable 5.2 · medium` (épico com mais de ~12
     tarefas, ou várias G e GG em paralelo).
   - **Revisão final do épico** (com 4 tarefas ou mais): `Conselho: um modelo forte por provedor (Recomendado)`,
     `Um revisor só` ou `Sem revisão final`. No conselho, monte `CONSELHO` com o modelo mais forte de cada provedor
     que o catálogo mostra com `canRunChildTask: true` (três, se houver), em effort `high`. Provedor cuja opção de
     effort tem outro nome entra em `EFFORT_OPCAO`.
3. Grave as escolhas no `orq.env` (`REVISOR`, `REVISOR_CRITICO`, `MODELO_*`, `ORQUESTRADOR`, `REVISAO_FINAL`,
   `CONSELHO`). O `REVISOR_RESERVA` é
   um Claude (padrão Opus 5.5 high), usado se o provedor do revisor sair do ar ou bater no limite. A `ESCADA` só muda
   se o usuário trocou os modelos dos implementadores.

**Pronto quando `$E/bin/alvo.py REVISOR`, `alvo.py M`, `alvo.py ORQUESTRADOR` e, com conselho,
`alvo.py --lista CONSELHO` imprimem alvos que existem no
catálogo, com o effort entre os valores que o catálogo aceita.**

## 4. Pasta de estado

Fora do repositório (ex.: `~/<projeto>-orq/`):

```bash
$S/bin/nova-orquestracao.sh <estado>    # pasta, links e modelos
E=<estado>
$E/bin/capacidade.sh --sugerir          # confira os valores de paralelismo para esta máquina
```

Preencha no `orq.env` o que o script listou como faltando e o que a sabatina mudou. Escreva `$E/PROJETO.md`:
autorizações, proibições, premissas, checagens obrigatórias com os limites de paralelismo, padrão de commit e
validação externa. Nos modelos de brief, troque cada comentário `<!-- PROJETO: … -->` pelo texto do projeto: leituras,
preparação da worktree, checagens, como validar e proibições. Comando pesado nos briefs passa por
`$E/bin/slot <build|test|browser|install> -- <comando>`.

Crie a branch do épico se ainda não existir no remoto:

```bash
git -C <repo> fetch origin
git -C <repo> ls-remote --exit-code --heads origin "$BASE" >/dev/null || git -C <repo> push origin "origin/$ORIGEM:refs/heads/$BASE"
$E/bin/guarda.py checar                       # épico, prefixo e protegidas coerentes
$E/bin/guarda.py texto <.env do app local>    # nenhuma URL de produção no ambiente de teste
$E/bin/pr-provas.py --checar                  # gh autenticado
```

**Projeto com login:** peça a autenticação de teste **uma vez, pelo cartão de segredo do T3**
([`AMBIENTE.md`](AMBIENTE.md)): um `request_secret` com `delivery: "file"` para o usuário, outro para a senha (e o
`token`, se houver), cada um gravado com `$E/bin/hml guardar <campo> --arquivo <arquivo>` no mesmo comando. O valor
não passa pelo agente nem pelo chat. Depois confira com `$E/bin/hml checar`: usuário marcado `sem @` num login por
e-mail volta a ser pedido pelo cartão, antes do `hml vivo`. Com SSO ou MFA, você mesmo roda o `hml capturar` em
segundo plano: o Chrome abre na tela do usuário, ele entra e fecha a janela. O usuário não usa o terminal em nenhum
passo.

Configure você mesmo o login para o `hml vivo`, sem perguntar ao usuário: abra a página de login, leia os campos e o
botão, e grave no `orq.env` os seletores `HML_LOGIN_USUARIO`, `HML_LOGIN_SENHA`, `HML_LOGIN_BOTAO` (e
`HML_LOGIN_AVANCAR`, se o login tem duas etapas), o `HML_LOGIN_OK` e, com app local, o `HML_SERVIDOR` e o
`HML_PLAYWRIGHT`. Rode `$E/bin/hml vivo --em <checkout do projeto>` até dar `NO AR` ([`AMBIENTE.md`](AMBIENTE.md)).
Depois da etapa 6 ele usa o `CHECKOUT`, que precisa das dependências instaladas (o setup do projeto, ou um link para
as do checkout principal, como nas worktrees dos agentes).

**Projeto sem login** (CLI, biblioteca, site estático): pule os dois parágrafos acima, anote no `PROJETO.md` que os
agentes não usam o `hml` e tire dos modelos de brief o item do `hml exec`: os agentes testam direto na `HML_URL` local.

**Pronto quando `rg -n 'PROJETO:' $E/modelos` e `rg -n '<' $E/orq.env` não acham nada, a branch do épico existe no
remoto, `guarda.py checar` e `pr-provas.py --checar` respondem ok e, em projeto com login, `hml checar` dá `PRONTO` e
`hml vivo` dá `NO AR`.**

## 5. Backlog

`BACKLOG.md` no formato de `modelos/BACKLOG.md`:

- fases em `## `;
- tarefas em `### <ID> · <título>`, com issue (opcional), origem (o requisito `R<n>` do `PLANO.md`), classe,
  dependências, escopo, **fora do escopo**, **arquivos**, **orçamento**, aceite, evidências e **provas** (tela →
  `print, vídeo`);
- o **effort** de cada tarefa, pelos critérios de [`MODELOS.md`](MODELOS.md) ("Classes e effort por tarefa"): a
  classe escolhe o modelo, e o campo `**Effort:**` sobe para `high` a tarefa em que a conferência pesa (casos de
  borda, código antigo, dados, segurança) ou desce para `medium` a que tem especificação fechada e teste automático.
  `—` vale o padrão da classe;
- **casos negativos dentro do `Aceite`**: para cada regra que a tarefa cria, o caso que ela nega (entrada inválida,
  sem permissão, repetição, vazio, duas requisições ao mesmo tempo) entra como item numerado, quando o risco existe
  naquela tarefa. Nas revisões medidas, metade dos defeitos estava dentro de um critério que o implementador provou
  só no caminho feliz ([`LICOES.md`](LICOES.md)). É item do `Aceite`, não campo novo: os scripts só leem o `Aceite`;
- **cadeia de dependências**: uma tarefa G de que várias dependem segura todas enquanto é revisada. Veja se o
  contrato dela (tipos, schema, interfaces) cabe numa tarefa pequena que entra antes, para as outras dependerem só
  dessa;
- gates onde uma decisão do usuário ou uma medição separa as fases;
- a seção `## Propostas` vazia.

Antes de mostrar ao usuário, rode a **revisão do plano**: `delegate_task` com `target` de `alvo.py PLANO_REVISOR`,
`role: "review"`, sem worktree e só leitura (diga isso no prompt). Ela recebe o `PLANO.md` e o BACKLOG e procura
tarefas que extrapolam o plano, requisitos sem tarefa, dependências erradas, classes e effort subestimados, aceite que
não dá para verificar e tarefas paralelas que disputam os mesmos arquivos. O formato do prompt está em
[`PROMPTS.md`](PROMPTS.md), "Revisão do plano". Pule com 3 tarefas ou menos.

Mostre o BACKLOG como página (`html_preview` e `html_render`): as tarefas com classe, modelo e effort
(`alvo.py --tarefa <ID> --spec`), pastas e provas, as dependências e os gates num diagrama simples, e as correções do
revisor do plano destacadas. Depois peça a aprovação pelo painel (`Aprovar (Recomendado)`, `Aprovar com ajustes`,
`Refazer`; o ajuste vem como resposta livre). A aprovação vale para todas as tarefas: registre `[aprovação]` no
DIARIO. Copie as tarefas para a tabela do PAINEL como `pendente`.

**Pronto quando toda tarefa tem classe, contrato de escopo, provas e aceite verificável por comando ou medição,
`rg -n '<' $E/BACKLOG.md` não acha nada, e o usuário aprovou o backlog.**

## 6. Thread do orquestrador

A thread do orquestrador precisa morar numa worktree própria que acompanha `origin/$BASE`: as worktrees das tarefas
nascem do commit local dela.

- **Esta thread está no projeto certo e fora de worktree** (`t3_worktree_status`): `t3_worktree_handoff` com
  `branch: "orq/<ORQ_ID>"`, `baseRef: "$BASE"`, `startFromOrigin: true` e
  `continuationPrompt: "/orquestrador-t3-pessoal $E"`. É a última ação do turno.
- **Senão** (thread de rascunho, outro projeto): confirme pelo painel (`Criar a thread (Recomendado)`, `Agora não`) e
  crie a thread com `t3_thread_launch`,
  `title` = `ORQ_NOME`, `workspaceStrategy: {"type":"worktree","baseRef":"$BASE","branch":"orq/<ORQ_ID>","startFromOrigin":true}`,
  `modelSelection` do alvo `ORQUESTRADOR` e `message: "/orquestrador-t3-pessoal $E"`. Passe o link
  `[ORQ_NOME](t3-thread://v1/<threadId>)`.

Na thread do orquestrador:

- grave o caminho da worktree em `CHECKOUT` e o id da thread no PAINEL;
- `$E/bin/guarda.py instalar "$CHECKOUT"`: o hook dos limites vale também para o orquestrador;
- `t3_thread_organize` `pin`;
- `t3_thread_configure` para o alvo `ORQUESTRADOR` (`alvo.py ORQUESTRADOR --selecao`), se ainda estiver no modelo da
  montagem. A troca reescreve o cache da conversa uma vez, e o raciocínio do modelo anterior não passa para um modelo
  menor: nada se perde, porque o estado está inteiro em `$E`. A primeira iteração do loop relê tudo de lá;
- título da thread no formato de estado (`<ORQ_NOME> · 🔨 0 rodando`), com `t3_thread_update` `rename`.

Peça ao usuário dois ajustes que só a interface faz: no menu da thread, **Auto-settle behavior → Disabled**; em
Settings, **Auto-resume limited threads** ligado. Confirme pelo painel (`Já ajustei (Recomendado)`, `Ajusto depois`).

**Pronto quando `t3_worktree_status` mostra a worktree em `orq/<ORQ_ID>` no commit de `origin/$BASE` e a thread
está fixada.**

## 7. Ensaio

Rode uma tarefa pequena de ponta a ponta com o usuário olhando: brief, `delegate_task`, `PRONTO`, conferência,
`escopo.py`, revisor, merge e settle. Durante a implementação, faça uma pausa suave e uma retomada
([`PAUSA.md`](PAUSA.md)) para ele ver o ponto seguro.

O ensaio cobre o caminho sem devolutiva. A primeira devolutiva do épico é o ensaio do registro de achados e da rodada
curta ([`REVISAO.md`](REVISAO.md)): acompanhe essa tarefa de perto e diga ao usuário como ela fechou.

**Pronto quando o PR entrou em `BASE`, as duas threads estão assentadas e a pausa voltou sem perda.**

## 8. O loop

A primeira iteração do playbook cria o heartbeat (`schedule_task`, ligado a esta thread) e as vigílias. Se o
usuário quis pausa e retomada automáticas, crie também dois `schedule_task` `fixed_time` com os prompts
`/orquestrador-t3-pessoal $E pausar` e `/orquestrador-t3-pessoal $E retomar`, e grave os ids em `$E/AGENDA`.

**Pronto quando a primeira iteração terminou com despacho e o heartbeat aparece em `list_scheduled_tasks`.**

## Controles para o usuário

- **Pausar:** "pausar" na thread do orquestrador, `/orquestrador-t3-pessoal $E pausar`, ou criar `$E/PAUSAR` (vale no
  próximo heartbeat). **Pausar agora** corta em ~2 min.
- **Retomar:** "continue", "retomar" ou qualquer pedido parecido na thread do orquestrador. O comando
  `/orquestrador-t3-pessoal $E retomar` também vale, mas ninguém precisa dele.
- **Parar tudo:** "parar" ou `/orquestrador-t3-pessoal $E parar`. Em emergência, Stop na thread do orquestrador e em
  cada agente do painel de Agentes.
- **Ver o estado:** `PAINEL.md`, ou `/orquestrador-t3-pessoal $E status`.
