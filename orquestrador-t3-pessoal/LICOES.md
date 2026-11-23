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

- **PRs paralelos conflitam depois de cada merge.** Sem `FLUXO=2`, peça só o rebase e confira com `git range-diff`.
  Capturas e outros binários de referência conflitam sempre: quem entra por último refaz a referência com o código
  já mesclado.
- **Merge sem fila refaz atualização de base** (épico de 31 tarefas, 22/11/2026). Com o revisor sem cota, as
  implementações seguiram e 8 PRs ficaram abertos para 3 vagas. Em 85 min, 6 merges pediram 7 atualizações da base e
  3 avisos de "a base andou de novo". A tarefa do caminho crítico refez as checagens 3 vezes no degrau mais caro da
  escada, por um conflito de documentação, e entrou por último. PR `COMUM` trazia a base antes da revisão e de novo
  antes do merge. Daí a fila de integração, o merge direto de PR limpo com checagem na ponta, a base trazida só na
  vez e o teto de PRs abertos ([`INTEGRACAO.md`](INTEGRACAO.md)). O `tempos.py` conta os pedidos de base por tarefa.
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

## Medição de novembro de 2026

Em 16/11/2026 as sessões de 114 tarefas de 8 orquestrações foram medidas, em tempo e em tokens. Os scripts e os
números estão em `~/.local/share/orquestrador-t3/medicao-2026-11-16/`. O `bin/tempos.py` faz as mesmas contas com os
eventos de uma pasta de estado, para comparar um épico novo com esse retrato.

- **A revisão por tarefa acha defeito real.** A primeira revisão pediu mudanças em 1 de 16 tarefas P, 22 de 45 M e 34
  de 46 G. De 105 achados altos e médios, 93 eram defeito de comportamento, 89 achados executando algo, e só 4
  dependiam de outra tarefa do épico. Por isso a primeira revisão continua completa, por tarefa e antes do merge.
- **Onde o relógio vai.** Entre PRONTO e merge, a mediana foi de 25 min sem devolutiva e de 105 min com. Na mesma
  classe, a devolutiva custa cerca de 65 min em M e 30 em G. O revisor começa 1 min depois do PRONTO (mediana).
- **A prova do implementador passa em falso.** Numa amostra, 23 de 47 defeitos estavam dentro de um critério que o
  relatório dava como atendido, quase sempre com evidência só do caminho feliz. Daí os casos negativos no `Aceite`.
- **A segunda revisão acha quase tudo na correção** (20 de 25 achados). Daí a rodada curta
  ([`REVISAO.md`](REVISAO.md)).
- **Suíte inteira por head de PR custa caro.** Num épico, 47% do tempo entre PRONTO e merge foi espera pela suíte com
  a revisão já aprovada, e cada rebase ou devolutiva jogava fora uma rodada. Daí a suíte na ponta do épico e a base
  trazida uma vez só, depois da aprovação ([`INTEGRACAO.md`](INTEGRACAO.md)).
- **O que ficou de fora, e por quê.** Revisão por bloco de tarefas no lugar da revisão por tarefa: o efeito na
  qualidade não foi medido. Classe P sem revisor: economizaria menos de 4% dos tokens de revisão, e a única P
  reprovada tinha defeito sério. Verificador extra dentro da thread do implementador: custaria mais tokens do que os
  ciclos de devolutiva que evita, a menos que evitasse uns 70% deles. Dependente começar antes do merge da
  dependência: encurtaria o caminho crítico em até 43%, mas três em cada quatro dependências G ainda mudam na
  revisão. Fica para um piloto com medição.
- **Sem investigar ainda:** o laço do orquestrador gastou 22% dos tokens do Claude, e 13% dos tokens de revisão no
  Codex foram para execuções que terminaram sem veredito.

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
