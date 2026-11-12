# Modelos e effort por papel e por tarefa

Segue o guia da Anthropic de escolha de modelo (nov/2026) e os guias de prompt de cada modelo. Três regras:

1. **O modelo dá a capacidade; o effort dá o cuidado.** Effort mais alto faz o modelo pensar mais, chamar mais
   ferramentas e conferir mais o próprio trabalho. Ele reduz a falha por caso de borda esquecido e não conserta a
   abordagem errada: conhecimento que o modelo não tem só vem do modelo de cima.
2. **Comece no degrau mais barato que entrega a tarefa e suba com evidência**, nesta ordem: o agente tem como
   conferir o próprio trabalho (teste, build, script)? Depois, um nível de effort. Depois, o modelo seguinte,
   começando num effort mais baixo que o usado no menor.
3. **Acima de `high`, o próximo nível custa tanto quanto o modelo de cima.** `xhigh` e `max` só entram com ganho
   medido e o "pode" do usuário. Antes disso, teste o modelo seguinte em `medium`.

A qualidade não depende só do modelo do implementador: ela é segurada pelo contrato de escopo, pelas checagens
objetivas (testes, lint, `escopo.py`, `provas.py`) e pelo revisor adversarial de outra família de modelo.

## Preço de referência (API, US$ por 1M tokens)

| Modelo | Id | Entrada / saída | Effort padrão | Para quê |
|---|---|---|---|---|
| Claude Fable 5.2 | `claude-fable-5-2` | 8 / 40 | `high` (`medium` no T3 e no Claude Code) | O trabalho técnico mais difícil e aberto: arquitetura, migração e refatoração grandes, liderar muitos agentes, execução longa sem ninguém olhando |
| Claude Opus 5.5 | `claude-opus-5-5` | 4 / 20 | `medium` | O padrão para código e trabalho de conhecimento complexos. Em `medium` iguala o Opus 5 em `high`. Na dúvida, comece aqui |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | 2 / 10 | `high` | Tarefa bem delimitada: bugfix, feature contra uma especificação, investigação, revisão, rascunho |
| Claude Haiku 5.5 | `claude-haiku-5-5` | 0,10 / 0,50 (5× acima de 100 mil tokens de prompt) | `medium` | Volume com resultado fácil de conferir: busca, leitura de log, extração, triagem. Não serve para laço longo de agente nem para editar código |

Leitura de cache: 0,20 no Fable e no Opus, 0,10 no Sonnet. Numa execução longa quase toda a entrada é leitura de
cache, então a diferença entre Fable e Opus fica na saída e na entrada nova, que custam o dobro. Na assinatura o preço
vira consumo de limite, na mesma proporção.

Números do guia para calibrar (Opus 5.5 no SWE-bench Pro): `medium` fica 2,5 pontos abaixo de `high` por 70% do
custo; `low` fica 8 pontos abaixo por um terço; `xhigh` ganha 1,4 ponto por 2,5 vezes o custo. Fable 5.2 em `high`
empata com Opus 5.5 em `max` pela metade do custo por tarefa.

## Papéis

| Papel | Alvo padrão (`orq.env`) | Por quê |
|---|---|---|
| Montagem e sabatina (a thread nova, com o usuário) | Fable 5.2 · `medium` | Planejar e dividir o trabalho é onde o erro custa mais, e é o caso de uso do Fable. `medium` é o nível dele para trabalho interativo: em `high` cada resposta demora bem mais |
| Revisão adversarial do plano, uma vez antes do loop (`PLANO_REVISOR`) | Fable 5.2 · `high` | Uma chamada só, sem ninguém esperando, com contexto limpo. Pule com 3 tarefas ou menos |
| Orquestrador em loop (`ORQUESTRADOR`) | Opus 5.5 · `medium` | Muitas iterações guiadas pelo playbook e pelos scripts, poucas decisões difíceis. Épico grande (mais de ~12 tarefas, ou várias G e GG em paralelo): Fable 5.2 · `medium` |
| Implementador classe **P** (`MODELO_P`) | Sonnet 5.5 · `medium` | Mudança mecânica ou localizada, com contrato fechado |
| Implementador classe **M** (`MODELO_M`) | Sonnet 5.5 · `high` | Feature ou bugfix num módulo. Sem ninguém no laço, `high` segura a conferência e evita a parada no meio |
| Implementador classe **G** (`MODELO_G`) | Opus 5.5 · `high` | Atravessa módulos, contratos, segurança, concorrência, dados: casos de borda escondidos |
| Implementador classe **GG** (`MODELO_GG`) | Fable 5.2 · `high` | Arquitetura nova, causa raiz desconhecida, ou tarefa que não fechou no Opus |
| Revisor de código (`REVISOR`) | **escolha do usuário na montagem**; recomendado GPT-6.1-Sol · `low` (Codex) | Família diferente da do implementador: os pontos cegos não coincidem. `low` é o padrão do Sol no Codex e o que cabe no limite de uso; as provas (`provas.py`) e o `escopo.py` seguram o piso |
| Revisor das classes G e GG (`REVISOR_CRITICO`) | o mesmo revisor em `medium` (vazio = `REVISOR`) | Só onde o risco justifica um nível a mais |
| Revisor de reserva (`REVISOR_RESERVA`) | Opus 5.5 · `high` | Entra quando o provedor do revisor sai do ar ou bate no limite. Revisar é conferir, e conferência é o que o effort compra |
| Subagente de busca, leitura de logs, inventário de arquivos | Haiku 5.5 (`model: "haiku"` na ferramenta Agent, sem effort) | Leitura que encheria o contexto do agente principal, com erro barato de notar |
| Subagente de análise (impacto, plano de teste, triagem de falha) | Sonnet 5.5 (`model: "sonnet"`, sem effort) | Julgamento médio, contexto isolado |
| Fatos durante a sabatina | Haiku 5.5 (agente `Explore` com `model: "haiku"`) | Sem o `model`, o `Explore` roda no modelo da sessão, que é o mais caro |
| Pedido de rebase, ajuste de relatório, artefato faltando | o mesmo implementador (`t3_thread_send`) | Não cria agente novo: o contexto já está lá |

Edição de código e decisão ficam no agente principal, nunca num subagente menor: quando o modelo pequeno erra a
leitura, o principal abre o arquivo errado e gasta mais do que economizou. Fable não roda como subagente sem pedido
explícito do orquestrador no brief. Subagente não compensa numa cadeia de passos dependentes nem no que cabe num
contexto só: ali, planejar e juntar custa mais do que economiza.

## Classes e effort por tarefa

Toda tarefa do BACKLOG tem `**Classe:**`, que escolhe o **modelo**. Na dúvida entre duas, escolha a de cima.

| Classe | Critério |
|---|---|
| P | 1–3 arquivos, sem decisão de design: configuração, renomeação, documentação, teste faltante, ajuste visual pontual |
| M | Um módulo, padrões existentes, aceite claro por teste |
| G | Mais de um módulo ou serviço; contrato público; autenticação, segurança, concorrência, migração de dados, desempenho |
| GG | Investigação aberta, algoritmo ou arquitetura nova, ou escalonada depois de falhar como G |

O campo opcional `**Effort:**` muda só o **effort** daquela tarefa. Vazio vale o padrão da classe. Decida na montagem,
tarefa por tarefa:

| Effort | Quando | Exemplo |
|---|---|---|
| `medium` | Especificação fechada, aceite todo conferido por teste automático, padrão pronto para copiar, diff pequeno | Endpoint novo igual aos vizinhos; componente a partir de um já existente |
| `high` | A conferência pesa: casos de borda escondidos, bug em código antigo, aceite difícil de verificar, tarefa longa (mais de ~5 itens de aceite), segurança, concorrência, dados | Corrigir corrida numa fila; migração com dados reais; parser |
| `xhigh`, `max` | Só com ganho medido e o "pode" do usuário. Nesses níveis o Sonnet e o Fable abrem rodadas de revisão por conta própria | — |

`low` não entra em implementador nem em revisor Claude: nesse nível o modelo pula a conferência e para no meio da
tarefa, e a rodada perdida custa uma revisão. Fica para subagente de leitura e para o revisor Sol.

## Escada e escalonamento

A `ESCADA` do `orq.env` é a ordem de subida, do guia da Anthropic: mais effort no mesmo modelo até `high`, depois o
modelo seguinte em `medium`.

```text
Sonnet 5.5 medium → Sonnet 5.5 high → Opus 5.5 medium → Opus 5.5 high → Fable 5.2 medium → Fable 5.2 high
```

Antes de subir, pergunte o que faltou:

| O que aconteceu | O que fazer |
|---|---|
| O agente não tinha como conferir (ambiente fora, fixture faltando, aceite sem comando) | Conserte o meio de verificação. Subir de modelo não resolve |
| Faltou cuidado: checagem pulada, caso de borda esquecido, parou no meio, relatório sem evidência | Um degrau: `alvo.py <alvo atual> --acima --spec` |
| Faltou capacidade: abordagem errada, causa raiz não achada, o mesmo erro duas vezes | O modelo seguinte: `alvo.py <alvo atual> --acima-modelo --spec` |

Gatilhos, sempre só para cima, um passo, registrado no DIARIO com `[modelo]`:

- **Devolutiva com achado alto de correção** no ciclo 1: antes de enviar a devolutiva, suba o implementador com
  `t3_thread_configure` no `childThreadId` (`alvo.py <novo alvo> --selecao`) e anexe à devolutiva o trecho do modelo
  novo (`alvo.py <novo alvo> --bloco impl`).
- **`BLOQUEADO` por dificuldade técnica** (não por falta de informação ou de acesso): retome um passo acima.
- **Duas retomadas por erro do agente** na mesma tarefa: um passo acima na próxima.
- **Topo** (`alvo.py` sai com código 3): `bloqueada`, com os achados para o usuário. `xhigh` é decisão dele.

Trocar o modelo de uma thread reescreve o cache da conversa inteira no primeiro turno, uma vez. Subindo, o modelo novo
lê o raciocínio do anterior; descendo, perde. Por isso não há rebaixamento no meio de uma tarefa. Se três tarefas
seguidas de uma classe passarem limpas na primeira revisão, anote no DIARIO e proponha no PAINEL um nível de effort a
menos para a classe: o usuário decide.

## Como o alvo vira `target`

Quem escolhe o modelo é o código, não o orquestrador. `bin/alvo.py` lê o `orq.env` e o BACKLOG:

```bash
$ <estado>/bin/alvo.py --tarefa T2.1                 # implementador: modelo da classe, effort da tarefa
{"providerInstanceId": "claudeAgent", "model": "claude-sonnet-5-5", "options": [{"id": "effort", "value": "high"}]}
$ <estado>/bin/alvo.py --tarefa T2.1 REVISOR         # REVISOR_CRITICO nas classes G e GG
{"providerInstanceId": "codex", "model": "gpt-6.1-sol", "options": [{"id": "reasoningEffort", "value": "low"}]}
$ <estado>/bin/alvo.py --tarefa T2.1 --spec          # para gravar em agentes.py (alvo=…)
claudeAgent:claude-sonnet-5-5:high
$ <estado>/bin/alvo.py claudeAgent:claude-sonnet-5-5:high --acima --spec
claudeAgent:claude-opus-5-5:medium
```

Papéis aceitos no lugar da tarefa: `P`, `M`, `G`, `GG`, `REVISOR`, `REVISOR_CRITICO`, `REVISOR_RESERVA`,
`PLANO_REVISOR`, `ORQUESTRADOR`. `--selecao` imprime no formato do `t3_thread_configure` e do `t3_thread_launch`.

O formato no `orq.env` é `provedor:modelo:effort`. A opção de effort se chama `effort` no Claude e
`reasoningEffort` no Codex; o `alvo.py` resolve isso. Declare o effort sempre: o padrão muda de modelo para modelo
(o Opus 5.5 roda um nível abaixo do Opus 5 quando o effort é omitido). Confira em `orchestrator_capabilities` que o
provedor tem `canRunChildTask: true` antes de usar.

O brief de cada agente termina com o trecho próprio do modelo que vai rodá-lo, montado por `mkbrief.py` e `mkrev.py`
a partir do mesmo alvo ([`PROMPTS.md`](PROMPTS.md)).
