# Pausa, retomada e parada

Pausar é levar **todos** os agentes a um ponto seguro e parar o despacho, sem perder trabalho e sem deixar
processo vivo. `$E` = `<estado>`. Prazos em `orq.env`: `PAUSA_PRAZO_MIN` (padrão 15) e `PAUSA_IMEDIATA_SEG`
(padrão 120).

## Gatilhos

| Pedido | Modo |
|---|---|
| `/orquestrador-t3-pessoal $E pausar`, "pausar" na thread, o arquivo `$E/PAUSAR`, ou a pausa diária agendada (`$E/AGENDA`) | **suave**: cada agente fecha o passo atual e para |
| `/orquestrador-t3-pessoal $E pausar agora`, "pausar agora", "preciso da máquina" | **imediata**: aviso curto, depois corte |
| `capacidade.sh` em `ESTADO=critico` | **proteção**: pausa só os agentes mais novos, até a máquina respirar |
| `/orquestrador-t3-pessoal $E parar`, "parar tudo" | **parada**: pausa imediata, heartbeat apagado, vigílias encerradas |
| `/orquestrador-t3-pessoal $E retomar`, ou, com a pausa ativa, "retomar", "continue", "segue", "pode seguir", "volta", "voltou", ou o usuário apagar `$E/PAUSADO` | **retomada** |

O usuário pede com as palavras dele: não exija o comando nem devolva o comando para ele digitar. Mensagem do usuário
pedindo pausa vence qualquer passo do playbook, exceto um merge em andamento (abaixo).

## O que é um ponto seguro

| Quem | Ponto seguro |
|---|---|
| Implementador | Nenhum comando rodando, e nenhum servidor, watcher ou navegador aberto por ele. Tudo commitado na branch da tarefa: o item X.Y pela metade vira um commit `wip(<ID>): pausa em <item>`, **sem push**. O `relatorio.md` tem a seção **Pausa** (item atual, o que falta, como retomar, `HEAD`). Mensagem final `STATUS: PAUSADO` |
| Revisor | Nenhum processo vivo. Achados e checagens até aqui em `tarefas/<ID>/revisao-c<N>.parcial.md`. `STATUS: PAUSADO` |
| Orquestrador | Nenhum passo atômico pela metade: um merge termina junto com `pull --ff-only` e a atualização do PAINEL. Nada é despachado depois do pedido |

Os briefs já trazem a seção **Pausa**: a mensagem de pausa só a dispara.

## Pausa suave

1. **Marque:** grave `$E/PAUSADO` (modo, horário, motivo) e apague `$E/PAUSAR`. Se o heartbeat estiver ligado,
   mude-o para 5 min (`update_scheduled_task`, `everyMs: 300000`) para conferir o prazo. Registre no DIARIO.
2. **Corte o que não começou:** `bin/agentes.py ativos`. Para cada agente, `task_status`:
   - em `preparing` ou `queued` → `task_cancel` (motivo "pausa") e a tarefa volta a `pendente`;
   - mensagens na fila dos filhos (`t3_queue_list`) → `t3_queue_cancel`.
3. **Avise quem está rodando:** para cada agente em `running` ou `waiting`, envie com `t3_thread_send`
   (`mode: "steer"`) ao `childThreadId`:
   `PAUSA (suave): termine o passo atual, siga a seção "Pausa" do seu brief e encerre o turno com STATUS: PAUSADO.`
   Marque o agente com `agentes.py set <ID> <papel> estado=pausando` e a tarefa como `pausando` no PAINEL.
4. **Encerre o turno.** As conclusões te acordam.
5. **A cada `STATUS: PAUSADO`:** confira o ponto seguro:
   - `git -C <worktree> status --short` sem mudanças rastreadas;
   - `bin/orfaos.sh <worktree>` sem processos.

   Ok → `estado=pausada`, tarefa `pausada`. Sobrou processo → `bin/orfaos.sh --matar <worktree>`. Sobrou mudança
   sem commit → deixe como está e anote `pausada (worktree suja)`: nada se perde, o agente resolve na retomada.
6. **Prazo esgotado** (`PAUSA_PRAZO_MIN` desde o passo 3) para quem não respondeu: `task_cancel` (motivo "pausa:
   prazo esgotado"), `bin/orfaos.sh --matar <worktree>`, tarefa `pausada (forçada)`.
7. **Todos pausados:** desligue o heartbeat (`update_scheduled_task`, `enabled: false`) e encerre as vigílias
   (`unwatch_pull_request` dos PRs vigiados): ninguém processa eventos na pausa, e a retomada as re-arma. Título da
   thread `· ⏸️ pausado`. Escreva o **relatório de pausa** no modelo de
   [`escrita/ESCRITA.md`](escrita/ESCRITA.md) (tabela: tarefa, estado, `HEAD`, worktree limpa ou suja, o que falta),
   com `texto.py --tipo pausa` limpo. Ponha-o na seção **Pausa** do PAINEL, poste na thread e avise com
   `PushNotification`.

## Pausa imediata

Igual à suave, num turno só:

1. Passos 1 e 2 da suave.
2. Steer: `PAUSA (imediata): pare em até 2 minutos. Se der, commite o que tem como wip(<ID>) sem push; mate os
   processos que você abriu; encerre o turno com STATUS: PAUSADO.`
3. Espere com `t3_thread_wait` em cada `childThreadId`, dividindo `PAUSA_IMEDIATA_SEG` entre eles (o tempo que um
   gastar sai do total).
4. Quem não terminou: `task_cancel`. Depois `bin/orfaos.sh --matar` em todas as worktrees ativas.
5. Passos 5 e 7 da suave.

Um provedor que não aceita steer (alguns revisores) recebe a mensagem só depois do turno: ele cai no corte do passo 4.
Revisões são refeitas sem perda, com a `revisao-c<N>.parcial.md` nas notas.

## Pausa de proteção (máquina)

Quando `capacidade.sh` mostrar `ESTADO=critico` (memória quase no fim, PSI alto, load muito acima do teto):

1. Não despache nada.
2. Pause em modo suave **um** agente por iteração: o implementador despachado por último que não está perto do fim
   (sem PR aberto). Tarefa `pausada (proteção)`.
3. Volte ao primeiro despacho só depois de duas iterações seguidas em `ESTADO=ok`, retomando primeiro os pausados
   por proteção. Registre cada passo no DIARIO.

## Parada

1. Pausa imediata.
2. `delete_scheduled_task` do heartbeat (id em `$E/HEARTBEAT`) e `unwatch_pull_request` dos PRs abertos.
3. DIARIO: relatório do ponto de parada (o que está mergeado, o que está pausado e onde, decisões pendentes).
4. O estado fica inteiro: `/orquestrador-t3-pessoal $E retomar` recria o heartbeat e continua.

## Retomada

1. Rode o passo 0 do playbook (varredura) e `bin/capacidade.sh` para saber as vagas.
   - **Homologação:** com tarefa que usa tela, rode `$E/bin/slot browser -- $E/bin/hml vivo`. Ele faz um login de
     verdade com uma sessão nova, então sessão ou token vencido não atrapalham. `NO AR` → siga. `FORA DO AR` →
     retome só as tarefas sem tela e diga ao usuário, numa linha, qual pedido do login falhou (host e status).
     `CREDENCIAL RECUSADA` ou `SEM LOGIN AUTOMÁTICO` → um pedido de decisão com o comando exato. Não teste a
     homologação com `curl` na raiz: 404 e 502 ali não dizem se o login funciona.
   - Apague `$E/PAUSADO`.
2. Ordem: `em revisão` → `corrigindo` → `implementando` (quem está mais perto do merge primeiro), e dentro de cada
   grupo os pausados por proteção por último.
3. Para cada agente pausado, até acabarem as vagas, com `t3_thread_send` ao `childThreadId`:
   `RETOMAR: leia git log, git status e a seção "Pausa" do relatório (ou a revisao-c<N>.parcial.md). Desfaça o
   commit wip só se for refazê-lo melhor. Continue do ponto em que parou e siga o brief até o fim.`
   O envio cria uma tarefa nova no mesmo filho: grave o `taskId` novo com `agentes.py set … taskId=<novo>
   estado=rodando` e devolva a tarefa ao status anterior.
4. Quem não coube espera `pausada` até a próxima iteração com vaga.
5. Religue o heartbeat (`enabled: true`, `everyMs` = `HEARTBEAT_MIN`), re-arme as vigílias dos PRs abertos, volte o
   título da thread ao estado normal e registre no DIARIO.
