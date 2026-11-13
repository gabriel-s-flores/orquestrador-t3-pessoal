# Lições das orquestrações anteriores

Casos que já aconteceram e o que fazer. Consulte antes de improvisar. Cada lição vale para o caso que ela descreve:
se o motivo deixou de existir, a lição sai.

## Orchestrator V2

- **Tudo passa pelas ferramentas MCP `t3-code`** ([`T3-V2.md`](T3-V2.md)). A API HTTP do protocolo 1 não existe mais.
- **Thread fixada não é assentada automaticamente** (o servidor pula `pinnedAt` e `autoSettleDisabledAt`). Vincular
  ou vigiar um PR na thread do orquestrador sem fixá-la pode assentá-la no primeiro merge e encerrar todas as
  vigílias.
- **A worktree de uma tarefa delegada nasce do commit local do orquestrador.** Esqueceu o `merge --ff-only` antes
  do despacho → o agente trabalha numa base velha e o PR conflita.
- **O `childThreadId` não recebe uma rodada nova de revisão:** cada rodada é um `delegate_task` novo. Já a devolutiva
  e a retomada vão para o `childThreadId` do implementador (contexto preservado) e geram um `taskId` novo: grave-o.
- **Agente esperando subagente** aparece como `waiting_for_children` no `task_status`: não há o que cutucar.
- **Conclusões chegam sozinhas** (e, no meio de um turno, entram nele). Não monte monitor nem laço de espera.

## Modelos, effort e prompts

- **Revisor em effort alto bate no limite de uso.** O padrão do revisor é `low`, com `medium` nas classes G e GG. O
  que segura a qualidade com effort baixo são os portões mecânicos (`provas.py`, `escopo.py`) e as notas de revisão
  em ordem de risco. Se o provedor sair do ar ou bater no limite mesmo assim, entra o `REVISOR_RESERVA`.
- **Effort acima de `high` não é o primeiro recurso.** Opus em `xhigh` e `max` gasta o que o Fable 5.2 em `medium` ou
  `high` entrega por menos. A subida segue a `ESCADA` ([`MODELOS.md`](MODELOS.md)).
- **O `Explore` roda no modelo da sessão** quando o `model` é omitido. Para buscar fatos barato, passe
  `model: "haiku"`.
- **Um brief só não serve a todos os modelos.** O Sonnet acrescenta teste e documentação não pedidos, o Opus encerra
  o turno com nota de andamento, o Fable segura trabalho de rotina quando o contexto tem cautela demais. Cada brief
  fecha com o trecho do modelo dele ([`PROMPTS.md`](PROMPTS.md)).
- **Regra geral escrita por um revisor vira instrução permanente** para o implementador. A devolutiva leva a correção
  com alcance, não a regra.

## Provas e épico

- **Sincronização do épico com a `ORIGEM` é merge commit.** Com squash, o épico perde a ligação com os commits da
  `ORIGEM` e passa a conflitar com ela nas mesmas linhas.
- **`main`, `master` e `develop` ficam fora do fluxo**, até para PR. O fluxo termina na branch do épico; promover é
  do usuário.
- **Usuário de teste guardado errado pelo terminal** (orquestração de trabalho, 2026-11-13): o `hml guardar` no
  terminal aceitou um e-mail sem `@`, o login recusou na primeira tela e uma tarefa parou por horas. Digitar sem eco
  escondia o erro. Agora o valor vem pelo cartão do T3 (`request_secret`, `delivery: "file"`), `hml checar` marca o
  usuário sem `@`, e o `hml capturar` (SSO ou MFA) é rodado pelo orquestrador: o usuário não usa o terminal.
- **Login de teste pedido a cada tarefa cansa o usuário.** A conta de teste fica no chaveiro e a sessão é capturada
  uma vez (`hml`). Sessão expirada vira um único pedido, não um por agente.
- **Hook por worktree, não no repositório:** `core.hooksPath` na config da worktree do agente
  (`extensions.worktreeConfig`) bloqueia push só ali e encadeia os hooks do projeto (husky inclusive). O checkout do
  usuário não muda.
- **O git não aceita `<épico>` e `<épico>/<x>` juntos:** as tarefas usam outro prefixo (`feature/…`).
- **Comentário em PR de repositório público é público.** O `pr-provas.py` mascara segredos em texto, mas não revisa o
  conteúdo da revisão: com dúvida, `PROVAS_PR="desligado"`.

## Máquina

- **Travamento do host** (agentes demais, ou loops de estresse): as threads voltam com erro. Depois do reinício,
  rode a varredura, retome os agentes ativos com `t3_thread_send` (nomeando o que falta) e confira o heartbeat.
- **Carga alta:** testes de estresse em paralelo já levaram o load a 49 num notebook de 8 núcleos. Por isso o despacho
  passa pelo `capacidade.sh`, comando pesado passa pelo `slot` e os briefs limitam os workers com `ORQ_JOBS`.
- **Processos esquecidos** (servidores de desenvolvimento, Chrome headless, watchers) seguem vivos depois do agente.
  `orfaos.sh` depois de cada conclusão; os briefs pedem para fechar tudo o que foi aberto.
- **Não reinicie o app do T3 de dentro de uma thread:** derruba o orquestrador junto.
- **Build interrompido pode deixar arquivos trocados.** Na retomada, o agente confere `git status` antes de
  aproveitar o que ficou.

## Fluxo de tarefas

- **PRs paralelos conflitam depois de cada merge.** Peça só o rebase e confira com `git range-diff`. Capturas e outros
  binários de referência conflitam sempre: quem entra por último refaz a referência com o código já mesclado.
- **Achados baixos não abrem ciclo.** Junte os de várias revisões numa tarefa de limpeza, com o "pode" do usuário.
  Os ciclos (no máximo 2) ficam para os altos e médios.
- **O revisor de cada ciclo é um agente novo**, com notas do que conferir e o histórico. O do ciclo anterior recebe
  settle.
- **O revisor também pede extras.** Sugestão de melhoria não entra na devolutiva obrigatória: vai para as Propostas
  ([`ESCOPO.md`](ESCOPO.md)).
- **Vários PRs aprovados esperando a mesma validação externa:** monte um build combinado só local (merge das branches
  num checkout destacado, testes) e valide uma vez. Guarde os artefatos de cada PR para isolar o culpado se falhar.
- **Validação externa encontra o que o ambiente simulado não mostra** (dispositivo mais lento, estado real do usuário,
  rede). Meça antes e depois na mesma sessão (A/B com o build da base) para separar regressão de problema antigo, e
  transforme o achado em tarefa nova com os números anexados.
- **O ambiente simulado pode ter capacidades que o real não tem.** Deixe no `PROJETO.md` e no brief quais diferenças
  importam e em que configuração o aceite é medido.
- **O usuário pode retirar uma autorização no meio do caminho.** Registre no `PROJETO.md` e no PAINEL, e deixe os
  artefatos prontos para a sessão autorizada ser curta.
- **Parar no fim do dia é rotina.** Ofereça a pausa e a retomada agendadas na montagem.

## Escrita e segredos

- Heredoc com `<<'EOF'` (aspas) para textos com crase, `$` ou aspas, como briefs e devolutivas.
- URLs de serviços com chave e tokens não vão para a saída. Guarde em arquivo `umask 077` e mascare. Se vazar, avise o
  usuário e ofereça a rotação.
- O usuário lê a thread do orquestrador: escreva o resumo de cada iteração em linguagem simples, com os números
  que importam.
- **Pergunta ao usuário vai pelo painel, não em lista:** uma lista de 7 perguntas em texto é difícil de responder. O
  `AskUserQuestion` vira no T3 um painel com uma pergunta por vez e alternativas clicáveis ([`T3-V2.md`](T3-V2.md)).
  No loop continua em texto, porque o painel segura o turno.
- **"continue" com a pausa ativa é a retomada.** Não devolva o comando para o usuário digitar ([`PAUSA.md`](PAUSA.md)).
  No `PROJETO.md`, escreva "sem agenda" quando ele não quiser pausa agendada, sem falar em comando.
- **"Ambiente fora do ar" se prova com login de verdade.** Uma resposta 502 na raiz de um host não diz se o login
  funciona. A pergunta "está no ar?" se responde com `hml vivo`, e sessão ou token vencido se renova pelo formulário,
  sem bloquear nem chamar o usuário ([`AMBIENTE.md`](AMBIENTE.md)).
- **A interface do T3 primeiro:** agentes como links `t3-thread://`, provas visuais na mensagem, backlog, gate, fim e
  `status` como página (`html_render`), o estado no título da thread e a thread marcada como não lida num pedido de
  decisão. Agentes não abrem painel; segredos vão pelo cartão do T3 (`request_secret` com `delivery: "file"`, ver a
  lição de 2026-11-13).
