# Prompt por modelo

Cada agente recebe o brief escrito para o modelo que vai rodá-lo. As regras vêm dos guias de prompt da Anthropic para
Fable 5.2, Opus 5.5, Sonnet 5.5 e Haiku 5.5 e das boas práticas gerais (nov/2026). Leia antes de escrever notas de
tarefa, devolutiva, mensagem a um agente ou pedido a um subagente.

## O que vale para todos

1. **Escreva para um colega novo e capaz, sem contexto.** Diga o objetivo, quem lê o resultado e o que é "pronto". Se
   alguém de fora ficaria em dúvida lendo o texto, o agente também fica.
2. **Regra com alcance e motivo.** "Requisição só para localhost e homologação: produção tem dado real" funciona
   melhor que "NUNCA acesse produção". O modelo generaliza a partir do motivo, e uma regra absoluta sem alcance é
   aplicada além do que você queria.
3. **Sem maiúsculas de ênfase.** `CRÍTICO`, `OBRIGATORIAMENTE` e `SEMPRE` em caixa alta fazem o modelo aplicar a regra
   demais. Escreva a instrução em tom normal.
4. **Diga o que fazer.** "Sugestão vai em Propostas" no lugar de "não faça melhorias".
5. **Passos numerados** só quando a ordem ou a completude importam. O resto em frases.
6. **Material longo em cima, pedido embaixo.** Contrato da tarefa, histórico e trechos de arquivo vêm antes; a
   instrução do que fazer agora fecha a mensagem.
7. **Peça ação, não sugestão**, quando quer a mudança feita: "corrija" e não "poderia sugerir".
8. **Critério de pronto verificável e formato da volta declarado:** o comando que precisa passar e o bloco `STATUS:`.
9. **Não peça o raciocínio no texto da resposta** ("mostre seu raciocínio passo a passo"): Fable, Opus e Sonnet podem
   recusar o pedido. Peça uma explicação curta do resultado ou um resumo do que foi feito.
10. **"Pense menos" e "responda direto" no prompt não funcionam.** Quem controla quanto o modelo pensa é o effort
    ([`MODELOS.md`](MODELOS.md)).

## O que cada modelo pede

| Modelo | O que ele faz sem orientação | O que o brief leva |
|---|---|---|
| **Fable 5.2** (GG, revisão do plano, orquestrador de épico grande) | Segue regras ao pé da letra e acumula cautela: com vários "nunca" no contexto, segura trabalho de rotina e pede aprovação que não precisa. Sem dizer de quem é o código, só acrescenta e relata problemas vizinhos; dizendo que é dele, refatora o que não foi pedido. Delega com facilidade quando o prompt convida. Em `low` e `medium` pode encerrar com trabalho devido | A lista "Sem pedir aprovação" com as ações nomeadas. A exceção escrita dentro da regra. Dono do código por área: o desenho é dele dentro dos arquivos permitidos, do time fora. Quando o subagente compensa e quanto custa. O texto "termine a tarefa inteira", que separa obstáculo comum de barreira deliberada |
| **Opus 5.5** (G, revisor de reserva, orquestrador) | Começa a agir rápido. Manda nota de andamento que encerra o turno: resumo que anuncia o próximo passo, oferta de continuar, lista de decisões que não travam nada | "Olhe em volta antes da primeira edição". Os quatro finais de turno que não servem e os três que servem. Processo em andamento não é tarefa pronta |
| **Sonnet 5.5** (P, M, subagente de análise) | Acrescenta teste, documentação e arquivo de apoio não pedidos, em qualquer effort. Em `low` e `medium` para para confirmar o plano. Em `low` relata pronto sem rodar a checagem. Pode ler uma mensagem no meio do turno como injeção | "Vá até o fim" e "feito e conferido, pare e relate". O parágrafo da checagem de verdade. A seção "Mensagens do orquestrador", que avisa que elas são legítimas |
| **Haiku 5.5** (subagente de busca e leitura) | Em prompt longo e effort baixo, pula busca, para cedo e pula checagem. Erra leitura sem avisar | Pedido curto, com o formato da volta que deixa o erro barato de notar: `arquivo:linha` e o trecho citado, "não encontrei" quando for o caso. A data de hoje se ele tiver busca na web |
| **Outro provedor** (ex.: Sol no Codex) | Não há guia da Anthropic. Em effort baixo faz menos chamadas de ferramenta | A ordem do que decide o veredito primeiro, e os portões mecânicos (`provas.py`, `escopo.py`) que não dependem do effort |

## Onde isso mora

- **Modelos de brief** (`<estado>/modelos/brief-implementador.md` e `brief-revisor.md`): o que vale para qualquer
  modelo, mais as seções "Mensagens do orquestrador", "Sem pedir aprovação" e "Limites".
- **Trecho do modelo** (`prompts/impl-<família>.md` e `prompts/rev-<família>.md` na skill): entra no lugar de
  `{BLOCO_MODELO}`, no fim do brief. `mkbrief.py` e `mkrev.py` escolhem o arquivo pelo alvo da tarefa. Um projeto
  troca um trecho pondo a sua versão em `<estado>/modelos/prompts/`.
- **Modelo trocado no meio da tarefa** (escalonamento): a instrução nova vai na mensagem mais recente, nunca numa
  edição do que já foi enviado. Anexe à devolutiva a saída de `alvo.py <novo alvo> --bloco impl`.

## Mensagens do orquestrador aos agentes

**Notas da tarefa** (entram no brief): fatos que o agente não tem como descobrir sozinho. O que já entrou na base, as
tarefas em paralelo e quem é dono de quais arquivos, as decisões anteriores com o motivo. Nota não cria regra nova e
não carrega cautela solta ("cuidado com…", "nunca repita…"): o Fable aplica a cautela ao resto da tarefa. Se há um
risco, diga onde e o que fazer com ele.

**Devolutiva:** itens específicos, cada um com onde, o quê e como conferir. Com `FLUXO=2`, cada item começa pelo ID
do achado e pede a menor correção que resolve ([`REVISAO.md`](REVISAO.md)). Não repasse regra geral que o revisor
escreveu ("pare no primeiro erro", "nunca altere X"): reescreva como correção com alcance. Feche com o que já pode ser
feito sem perguntar (push na branch, rodar de novo as checagens).

**Continuação** (o agente encerrou com trabalho devido e sem bloqueio declarado): nomeie os itens em aberto.

```text
Continue a T2.1: faltam o critério 2.3 (teste de token expirado) e o push. Se um deles estiver bloqueado, diga o que bloqueia.
```

"Continue" sozinho não diz o quê. No máximo duas continuações automáticas por tarefa; depois é falha de cuidado, e a
tarefa sobe um degrau ([`MODELOS.md`](MODELOS.md)).

**Aprovação e resposta a pergunta:** diga a ação inteira ("Sim: rode a migração no banco de homologação"), não "pode"
ou "ok".

**Processo em andamento:** se algo que o agente iniciou ainda roda (subagente, comando em segundo plano), a tarefa
não terminou. Espere e não mande continuação.

## Pedido a um subagente

Subagente de leitura (Haiku 5.5), em quatro partes curtas:

```text
Objetivo: achar onde o front trata a expiração do token de sessão, para eu decidir onde entra o teste da T2.1.
Já sei: o interceptor fica em src/api/http.ts; não é lá que o logout acontece.
Onde procurar: src/**, sem node_modules nem dist.
Volte com: até 10 linhas, cada uma "arquivo:linha — trecho citado — o que faz". Se não achar, diga "não encontrei" e onde procurou.
```

Subagente de análise (Sonnet 5.5): o mesmo formato, com a pergunta de julgamento fechada ("quais testes quebram se eu
mudar a assinatura de X? liste por arquivo") e sem pedir edição. Quem edita e decide é o agente principal.

Não abra subagente para o que um `rg` resolve, para passos que dependem um do outro ou para o que cabe no seu
contexto.

## Revisão do plano (`PLANO_REVISOR`)

Uma chamada, só leitura. O prompt leva, nesta ordem: o `PLANO.md` e o BACKLOG como caminhos de
arquivo; a missão ("procure motivos para este backlog falhar"); o que procurar (tarefa que extrapola o plano, requisito
sem tarefa, dependência errada, classe ou effort subestimados, aceite que não dá para verificar por comando, tarefas
paralelas que disputam os mesmos arquivos, regra sem o caso que ela nega no `Aceite`, tarefa G que segura várias
dependentes e cujo contrato caberia numa tarefa anterior menor); o formato da volta (uma linha por achado: tarefa, problema, correção
proposta); e a frase "é só leitura: não edite arquivos nem crie tarefas".

## Higiene das instruções

A cautela se acumula onde o contexto atravessa sessões: `LICOES.md`, `PROJETO.md`, memória, notas e mensagens entre
agentes. A cada montagem, e quando um agente segurar trabalho de rotina:

- tire a cautela cujo motivo acabou;
- reescreva a regra absoluta com o alcance e o motivo;
- escreva a exceção dentro da regra ("push só na branch da tarefa", e não "nunca dê push" mais uma exceção solta em
  outro lugar);
- nomeie o que não precisa de aprovação. "Aja com mais liberdade" não muda nada.
