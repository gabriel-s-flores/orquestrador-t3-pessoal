# Playbook · uma iteração do orquestrador

`$E` é a pasta de estado (a que tem `orq.env`). Os parâmetros (`ORQ_ID`, `REPO`, `BASE`, `PREFIXO`,
`CHECKOUT`, `MAX_AGENTES`, alvos de modelo, prazos…) vêm de `$E/orq.env`. O que vale só para este projeto
(premissas, autorizações, checagens, padrão de commit, validação externa) está em `$E/PROJETO.md`: ele vence
este playbook onde os dois divergirem. As ferramentas V2 estão em [`T3-V2.md`](T3-V2.md).

Cada despertar é **uma iteração**, do passo 0 ao 9. Você planeja, despacha, confere, faz merge e relata. O código do
projeto chega só pelos PRs dos agentes.

## 0. Varredura (toda iteração, antes de tudo)

1. `$E/bin/varrer.sh`: pausa, heartbeat, PRs abertos para `$BASE`, sinais em disco por tarefa ativa, processos
   órfãos e carga. Todo sinal é processado **nesta** iteração.
2. `$E/bin/agentes.py ativos` e, para cada agente, `task_status`. Ler um resultado terminal confirma a entrega: a
   mesma conclusão não volta a te acordar.

**Só na primeira iteração da sessão:**

- `orchestrator_capabilities`: os provedores dos alvos do `orq.env` têm `canRunChildTask: true`? Se o do revisor
  sumiu, use `REVISOR_RESERVA` e registre `[decisão]`.
- Autenticação do GitHub: `$E/bin/pr-provas.py --checar` (`gh auth status`). Falhou → avise o usuário: sem o `gh`
  não há PR nem merge.
- `git -C "$CHECKOUT" fetch origin --quiet && git -C "$CHECKOUT" merge --ff-only "origin/$BASE"`.
- `t3_thread_organize` `pin` nesta thread (idempotente): thread fixada não é assentada sozinha quando um PR vigiado
  é mergeado.
- Heartbeat: `list_scheduled_tasks`. Sem o id de `$E/HEARTBEAT`, crie com `schedule_task`
  (`prompt: "/orquestrador-t3-pessoal $E"`, `schedule: {"type":"interval","everyMs": HEARTBEAT_MIN×60000}`, título
  `ORQ_NOME · heartbeat`) e grave o id.
- Vigílias: `watch_pull_request` para cada PR aberto de tarefa ativa.
- Limites ([`AMBIENTE.md`](AMBIENTE.md)): `$E/bin/guarda.py checar` e `guarda.py instalado "$CHECKOUT"` (ausente →
  `guarda.py instalar "$CHECKOUT"`). Problema no `checar` → não despache nada e avise o usuário.
- Ambiente de teste (projeto com login, ver `PROJETO.md`): `$E/bin/hml checar` e, com tarefa de tela no backlog,
  `$E/bin/slot browser -- $E/bin/hml vivo` ([`AMBIENTE.md`](AMBIENTE.md)). `FALTA CONFIGURAR` ou resultado diferente de `NO AR` → tarefas com tela esperam,
  as outras seguem, e o `hml vivo` roda de novo a cada iteração até dar `NO AR`. Só o que pede o usuário
  (`CREDENCIAL RECUSADA`, `SEM LOGIN AUTOMÁTICO`) vira pedido de decisão.

## 1. Controles

- `$E/PAUSAR` existe ou o usuário pediu pausa, retomada ou parada: [`PAUSA.md`](PAUSA.md).
- `$E/PAUSADO` existe: registre os eventos no DIARIO, não despache nada e vá ao passo 9. Pausa em andamento
  (tarefas `pausando`): continue os passos 5–7 de `PAUSA.md`.

## 2. Estado e fatos

Leia `PAINEL.md` (fonte da verdade dos status), `BACKLOG.md` e as últimas entradas do `DIARIO.md`. Depois:

```bash
$E/bin/capacidade.sh            # VAGAS=, ESTADO=ok|apertado|critico e o porquê
git -C "$CHECKOUT" fetch origin --prune --quiet
```

`ESTADO=critico`: pausa de proteção ([`PAUSA.md`](PAUSA.md)) antes de qualquer outro passo.

## 3. Implementações (`implementando`, `corrigindo`)

Para cada implementador, pelo `task_status` e pelo bloco `STATUS:` da conclusão:

- **`PRONTO`: conferência objetiva.**
  - o PR aponta para `$BASE` a partir da branch da tarefa (`$E/bin/guarda.py pr <n>` dá `OK`), está sem conflito e
    foi rebaseado (`git merge-base --is-ancestor origin/$BASE <head>`);
  - o hook dos limites está ativo na worktree do agente (`guarda.py instalado <worktree>`);
  - o `relatorio.md` tem todas as seções, inclusive o **Mapa de escopo**;
  - as evidências citadas existem e as checagens batem com o brief;
  - `$E/bin/escopo.py <ID> --head <sha do PR> > $E/tarefas/<ID>/escopo-c<N>.md` sem alerta (roda no `CHECKOUT`,
    que já tem o head depois do fetch; [`ESCOPO.md`](ESCOPO.md)).

  Faltou algo → `t3_thread_send` ao `childThreadId` dizendo exatamente o quê (não conta como ciclo). Tudo certo →
  `watch_pull_request` do PR e revisor (passo 5.6).
- **`BLOQUEADO`:**
  - `HML: …`: rode `hml vivo` você mesmo antes de qualquer coisa. `NO AR` → devolva ao agente "o login pelo
    formulário funciona: entre de novo com `HML_USUARIO` e `HML_SENHA` e siga". `FORA DO AR` → a tarefa espera e o
    `hml vivo` roda a cada iteração. `CREDENCIAL RECUSADA` ou `SEM LOGIN AUTOMÁTICO` → junte os bloqueios e mande
    **um** pedido de decisão com o comando exato. Quando o `hml vivo` der `NO AR`, retome todos;
  - pergunta: responda com base no plano, registre `[decisão]` e envie;
  - dificuldade técnica: veja primeiro se faltou meio de conferir (ambiente, fixture, comando do aceite) e
    conserte isso. Senão, suba um passo na escada ([`MODELOS.md`](MODELOS.md)): `--acima` se faltou cuidado,
    `--acima-modelo` se faltou capacidade. Retome com o trecho do modelo novo na mensagem;
  - sem saída: `bloqueada`, com o motivo no PAINEL.
- **Pergunta pendente** (`hasPendingQuestion`): `t3_pending_request_read` → resposta conservadora com
  `t3_pending_request_respond` e `[decisão]`.
- **Falha do provedor ou limite de uso:** com "Auto-resume limited threads" ligado, espere o reset. Senão, depois
  do reset: `t3_thread_send` "Continue de onde parou: leia git log, git status e o seu relatório." Até 3 retomadas;
  depois, escale ou `bloqueada`.
- **`working` ou `waiting_for_children`:** nada. Agente esperando subagente não é agente parado.
- **Conclusão sem o bloco `STATUS:`:** é um relato, não a prova de que a tarefa acabou. Leia com `t3_thread_read` e
  os arquivos da tarefa. Algo que o agente iniciou ainda roda (subagente, comando) → espere. Há trabalho devido e
  nenhum bloqueio declarado → mande uma continuação que nomeia os itens em aberto ([`PROMPTS.md`](PROMPTS.md)). No
  máximo duas por tarefa; na terceira, suba um degrau (`--acima`) e registre `[modelo]`.
- **Depois de toda conclusão:** `$E/bin/orfaos.sh <worktree>`; sobrou processo → `--matar`.

## 4. Revisões (`em revisão`)

Revisão escrita (`tarefas/<ID>/revisao-c<N>.md`):

- **`APROVAR`, `Escopo: DENTRO` e `PROVAS: PROVADO`:**
  1. **Provas** ([`PROVAS.md`](PROVAS.md)): `$E/bin/provas.py <ID> <N> --head <sha do PR>`. `INCOMPLETO` não é
     aprovação: mande a lista do que falta ao mesmo revisor (`t3_thread_send` ao `childThreadId` dele) e espere;
     não conta como ciclo. Confira também que o revisor rodou as checagens e que o head revisado é o head atual do
     PR. Head mudou → novo ciclo de revisão, sem devolutiva.
  2. Se o `PROJETO.md` exige **validação externa** (dispositivo real, homologação), faça-a antes do merge e só com
     a autorização do usuário naquele momento. Sem autorização: status `aprovada — aguarda <validação>`, artefato
     pronto, e peça.
  3. **Provas no PR** (`PROVAS_PR=comentario`): `$E/bin/pr-provas.py <ID> <N>` comenta no PR a lista de provas por
     critério e a revisão. Falhou → registre no DIARIO e siga: o comentário não segura o merge.
  4. `$E/bin/guarda.py pr <n>` de novo (`OK` = base é o épico). Merge na branch do épico:
     `gh pr merge <n> --repo "$REPO" --squash --subject "<título do PR> (#<n>)" --match-head-commit <sha revisado>`.
     Depois `git -C "$CHECKOUT" merge --ff-only "origin/$BASE"` (após o fetch). Merge e pull são um passo só:
     nenhuma pausa entra entre eles.
  5. Status `concluída ✅`. No resumo da iteração, mostre a prova principal da tarefa (print ou vídeo) com o caminho
     absoluto, como no modelo do guia.
  6. `t3_thread_organize` `settle` no revisor. O implementador assenta sozinho com o merge do PR vinculado; se não
     assentar, faça o settle.
  7. Achados baixos e sugestões: [`ESCOPO.md`](ESCOPO.md), "O que o orquestrador faz com os extras".
- **`MUDANÇAS` ou `Escopo: EXTRAPOLA`:** escreva `tarefas/<ID>/devolutiva-c<N>.md` só com os obrigatórios (altos e
  médios ligados a aceite, correção, regressão, segurança ou escopo), no formato de
  [`escrita/ESCRITA.md`](escrita/ESCRITA.md) e com `texto.py --tipo devolutiva` limpo. Sugestões vão para as
  Propostas do BACKLOG.
  - Achado alto de correção → suba o implementador um passo antes de enviar ([`MODELOS.md`](MODELOS.md), "Escada e
    escalonamento"): `novo=$($E/bin/alvo.py <alvo atual> --acima --spec)` (ou `--acima-modelo`),
    `t3_thread_configure` com `alvo.py $novo --selecao`, e o trecho de `alvo.py $novo --bloco impl` no fim da
    devolutiva. Grave `agentes.py set <ID> impl alvo=$novo`.
  - A devolutiva leva correções com alcance (onde, o quê, como conferir), nunca a regra geral que o revisor
    escreveu ([`PROMPTS.md`](PROMPTS.md)).
  - Envie a devolutiva com `t3_thread_send` ao `childThreadId` do implementador, que devolve um `taskId` novo: grave
    com `agentes.py`. Status `corrigindo`; settle do revisor deste ciclo.
  - No `PRONTO` seguinte: conferência objetiva e **revisor novo** (`delegate_task` novo, ciclo N+1). As notas levam
    a devolutiva, a resposta do implementador e as objeções em aberto.
  - **Máximo de 2 devolutivas.** A revisão do ciclo 2 é a última: `MUDANÇAS` de novo → `bloqueada`, com os achados
    no PAINEL.
- **Revisor terminou sem arquivo:** `waiting_for_children` → espere. Senão, uma mensagem pedindo a revisão. Sem
  resposta, abra uma rodada nova com a parcial nas notas.

**Depois de cada merge:** os PRs paralelos podem conflitar. A vigília te acorda; peça ao implementador **só o
rebase** (e refazer artefatos binários que conflitaram). Antes do merge, confira com
`git range-diff <base-antiga>..<head-antigo> origin/$BASE..<head-novo>` que nada além do rebase mudou. Avise as
tarefas em andamento que tocam nos mesmos arquivos.

## 5. Despachar

1. **Prontas** = `pendente` com todas as dependências `concluída ✅` (ou o gate aprovado), na ordem do BACKLOG.
   Propostas nunca entram.
2. **Vagas:** o `VAGAS=` do `capacidade.sh`. Ele já aplica `MAX_AGENTES`, a carga, a memória livre, o PSI e
   `DESPACHO_POR_ITERACAO`, porque o setup de cada worktree nova é pesado. `VAGAS=0` → não despache.
3. **Base em dia:** `git -C "$CHECKOUT" merge --ff-only "origin/$BASE"` (as worktrees nascem deste commit).
4. **Brief:** escreva as notas da tarefa num arquivo e rode `$E/bin/mkbrief.py <ID> <notas.md>`. As notas cobrem o
   estado da base (o que já entrou), as tarefas em paralelo, quem é dono de quais arquivos e as decisões anteriores
   que afetam a tarefa, com o motivo. **Notas dão contexto; não ampliam o escopo nem criam regra** ([`PROMPTS.md`](PROMPTS.md)).
   O `mkbrief.py` fecha o brief com o trecho do modelo que vai rodar a tarefa.
5. **Implementador:** `delegate_task` com
   - `task`: o conteúdo de `tarefas/<ID>/brief.md`;
   - `title`: `🔨 <ID> · <título curto>`, `role: "implementation"`;
   - `isolation: "worktree"`, `mode: "async"`;
   - `target`: `$E/bin/alvo.py --tarefa <ID>` (o modelo da classe, com o effort da tarefa);
   - `clientRequestId`: `<ORQ_ID>-<ID>-impl`.

   Tarefa redespachada num passo acima: `mkbrief.py <ID> <notas.md> --alvo <novo alvo>` e o mesmo alvo no `target`.

   Grave com `$E/bin/agentes.py set <ID> impl taskId=… threadId=… alvo=$($E/bin/alvo.py --tarefa <ID> --spec) estado=rodando`. Status
   `implementando`. Assim que o agente começar, grave também a worktree (`worktreePath` em `t3_thread_read` do
   `childThreadId`) com `agentes.py set <ID> impl worktree=…`: a pausa e o `orfaos.sh` dependem dela.
6. **Revisor:** `$E/bin/mkrev.py <ID> <PR> <HEAD> <ciclo> <notas.md>` (notas com os riscos que você viu, do mais
   grave ao menos, e, do ciclo 2 em diante, o histórico). O revisor começa por eles: com effort baixo, a ordem das
   notas decide onde ele gasta a atenção. Depois `delegate_task` com
   - `task`: o conteúdo de `tarefas/<ID>/brief-revisor-c<N>.md`;
   - `title`: `🔍 <ID> · revisão c<N>`, `role: "review"`;
   - `isolation: "worktree"`, `mode: "async"`;
   - `target`: `$E/bin/alvo.py --tarefa <ID> REVISOR` (já escolhe `REVISOR_CRITICO` nas classes G e GG);
   - `clientRequestId`: `<ORQ_ID>-<ID>-rev-c<N>`.

   Revisor de reserva (provedor fora do ar ou no limite): `mkrev.py … --alvo REVISOR_RESERVA` e
   `alvo.py REVISOR_RESERVA` no `target`, para o brief sair com o trecho do modelo certo.

   Grave com `agentes.py set <ID> rev-c<N> …`, inclusive a worktree. Status `em revisão`, ciclo `c<N>`.

## 6. Gates e consolidação no épico

Tudo se consolida na branch do épico (`$BASE`): cada PR de tarefa entra nela com squash. O fluxo
termina aí. Levar o épico para a `main` é decisão do usuário, fora deste fluxo: você não abre PR, não faz
push e não faz merge em nenhuma branch de `BRANCHES_PROTEGIDAS` ([`AMBIENTE.md`](AMBIENTE.md)).

**Gates:** quando todas as tarefas de um gate estiverem concluídas, avalie os critérios do BACKLOG lendo relatórios,
medições e provas. Mostre o resultado como página (`html_preview` e `html_render`): uma linha por critério com o
número medido, e as provas visuais das tarefas do gate em miniatura. Escreva o resultado no DIARIO e no PAINEL. Gate
reprovado → as dependentes ficam `em espera` e o usuário decide.

**Sincronização com a `$ORIGEM`** (`SYNC_ORIGEM=gate`): em cada gate e no fim, se
`git -C "$CHECKOUT" rev-list --count "origin/$BASE..origin/$ORIGEM"` for maior que zero, acrescente ao BACKLOG a
tarefa abaixo e despache-a antes das próximas. A `$ORIGEM` só é lida: o merge acontece numa branch `sync/…` que entra
no épico por PR. É a única tarefa que você cria sem perguntar, porque o usuário autorizou na montagem. O merge dela é
**merge commit, nunca squash**: o squash corta a ligação com os commits da `$ORIGEM` e o épico passaria a conflitar
com ela.

```markdown
### SYNC-<AAAAMMDD> · Sincronizar <BASE> com <ORIGEM>
- **Issue:** — · **Origem:** sincronização autorizada na montagem
- **Depende de:** — · **Classe:** P
- **Escopo:** merge de origin/<ORIGEM> numa branch nova a partir de origin/<BASE>, resolvendo conflitos sem mudar o comportamento de nenhum dos lados
- **Fora do escopo:** qualquer mudança além da resolução de conflitos
- **Arquivos:** **
- **Aceite:**
  1 git merge origin/<ORIGEM> concluído, sem marcadores de conflito
  2 a suíte completa passa no resultado
- **Provas:** log, sem mutação
- **Branch:** sync/<base-em-minúsculas>-<AAAAMMDD>
```

**Fechamento do épico:** com todas as tarefas e gates concluídos e a sincronização feita, escreva
`$E/fechamento.md`: a branch, as tarefas com seus PRs e provas, e os riscos, no formato de
[`escrita/ESCRITA.md`](escrita/ESCRITA.md). Ele serve de corpo para o PR do épico, que quem abre é o usuário.

## 7. Registrar

Tudo o que o usuário lê segue [`escrita/ESCRITA.md`](escrita/ESCRITA.md): curto, em português simples, começando
pelo que importa.

- **`PAINEL.md`:** "Precisa de você" no topo; depois a tabela de tarefas, agentes ativos (`N / MAX_AGENTES`),
  carga, último commit visto e próximos passos.
- **`DIARIO.md`:** uma entrada no modelo do guia (horário, o que mudou, por quê). Decisões sem o usuário levam
  `[decisão]`; escalonamentos de modelo, `[modelo]`.
- **Thread:** o resumo da iteração no modelo do guia (até 6 linhas), com os agentes como links `t3-thread://` e a
  prova visual do que entrou. Iteração sem mudança termina numa linha só.
- **Título da thread** (`t3_thread_update` `rename`), só quando o estado mudar: `<ORQ_NOME> · 🔨 <n> rodando`,
  `· ⛔ <n> decisão`, `· ⏸️ pausado`, `· ✅ concluído` ([`T3-V2.md`](T3-V2.md), "Interface do T3").

## 8. Avisar o usuário

Só quando ele agiria agora (gate, bloqueio, proposta de escopo, pedido de autorização, pausa concluída, fim):

- na thread, o **pedido de decisão** do guia, em texto e com `texto.py --tipo decisao` limpo. Nunca pelo painel
  do `AskUserQuestion`: ele segura o turno e trava os despertares ([`T3-V2.md`](T3-V2.md));
- o título da thread com `⛔` e `t3_thread_organize` `mark_unread` nesta thread: ela está fixada no topo da barra
  lateral, e é isso que ele vê primeiro;
- `PushNotification` com até 120 caracteres (`--tipo push`): o ícone, a tarefa e o que ele precisa fazer.

A notificação só chega ao celular com o Remote Control ativo, então a thread é o canal garantido. Respondida a
decisão, o título volta ao estado normal.

## 9. Próximo despertar

Não há `ScheduleWakeup`: as conclusões e as vigílias te acordam, e o heartbeat cobre o resto. Ajuste o heartbeat
com `update_scheduled_task` só quando o regime mudar:

- agentes rodando: `HEARTBEAT_MIN` (padrão 30 min);
- nada rodando e tudo esperando o usuário ou algo externo: 120 min;
- pausa em andamento: 5 min; pausado: desligado.

Sem `schedule_task` disponível, volte ao modo antigo: `ScheduleWakeup` com o prompt `/loop /orquestrador-t3-pessoal $E`.

**Fim:** com o épico fechado (passo 6), escreva o relatório final no modelo do guia (o que foi entregue,
as decisões sem o usuário, as propostas que ficaram, os riscos, o que não foi testado), com `texto.py --tipo final`
limpo. Na thread, mostre antes a página do fechamento (`html_render`: tarefas com PR e provas em miniatura) e
depois o texto curto. Grave no DIARIO e avise. Para devolver a thread: `list_thread_pull_requests` (todo PR do
épico vinculado), `unwatch_pull_request` dos que ainda estiverem vigiados, apague o heartbeat, título `· ✅ concluído`
e desafixe a thread.

## Regras

- O seu checkout é `$CHECKOUT`, só com fast-forward. Você não commita no repositório: o estado vive em `$E`.
  Cópias de trabalho do usuário ficam na branch em que ele as deixou.
- Coordenação visível: seus turnos, as tarefas delegadas, as vigílias, o heartbeat e os arquivos de estado. Nenhum
  processo de fundo seu.
- Limites: [`AMBIENTE.md`](AMBIENTE.md). `main`, `master`, `develop` e produção ficam fora: nenhum push, merge, PR ou
  requisição. Testes só em localhost e homologação, com a conta de teste do `hml`. Credencial nunca é pedida no chat.
- Escopo: [`ESCOPO.md`](ESCOPO.md). Você não cria tarefa, não muda aceite e não amplia globs sem o usuário.
- Escrita: [`escrita/ESCRITA.md`](escrita/ESCRITA.md). Texto que o usuário não lê não serve.
- Interface: [`T3-V2.md`](T3-V2.md), "Interface do T3". Painel para perguntar com ele presente, links para agentes,
  provas visuais na mensagem, páginas nos marcos, título com o estado.
- AFK: diante de dúvida, escolha a opção mais conservadora que respeite o plano, registre `[decisão]` e siga.
- Sem pedir aprovação: o que o `PROJETO.md` lista como autorizado, e a rotina do loop. Repetir chamada que só lê
  (`task_status`, `t3_thread_read`, `gh pr view`, `git fetch`) ou script de `bin/` que falhou por motivo passageiro;
  mandar continuação, pedido de rebase e retomada aos seus agentes; assentar os agentes que terminaram; ajustar o
  heartbeat. Cautela de uma nota ou de uma lição vale para o caso que ela cita, não para o resto do loop.
- Contexto enxuto: leitura longa (diff grande, log, relatório de vários agentes) vai para um subagente Haiku, que
  volta com a conclusão e as linhas citadas. Decisão, devolutiva e merge ficam com você ([`MODELOS.md`](MODELOS.md)).
- Modelo e effort: quem escolhe é o `alvo.py`, pela classe e pelo `**Effort:**` da tarefa. Você não troca alvo por
  conta própria fora da escada, e não passa de `high` sem o "pode" do usuário.
- Escrita para agentes: [`PROMPTS.md`](PROMPTS.md). Regra com alcance e motivo, sem maiúsculas de ênfase, ação nomeada.
- Tokens, chaves e URLs com credenciais nunca aparecem em saídas: mascare hosts e caminhos.
- Antes de agir em casos que já aconteceram (reinício, sessão nova, conflito, revisor mudo), consulte
  [`LICOES.md`](LICOES.md).
