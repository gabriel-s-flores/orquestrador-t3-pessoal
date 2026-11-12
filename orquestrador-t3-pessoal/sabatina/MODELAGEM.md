# Modelagem de domínio · afiar a linguagem enquanto se desenha

Adaptação em português de `domain-modeling` (Matt Pocock): os artefatos vão para a **pasta de estado**, não para o
repositório, salvo se o `PROJETO.md` disser outro lugar. Use junto com a [`SABATINA.md`](SABATINA.md) quando a conversa mexe com termos do
domínio (o que é um "pedido", um "cliente", um "cancelamento").

É a disciplina *ativa*: desafiar termos, inventar cenários de borda e escrever o glossário e as decisões no momento em
que se cristalizam. Só *ler* o glossário para usar o vocabulário não é esta disciplina; é um hábito que qualquer
etapa pode ter.

## Onde ficam os arquivos

| Glossário | Decisões |
|---|---|
| o que o `PROJETO.md` disser; sem indicação, `$E/GLOSSARIO.md` | `$E/DECISOES.md` |

Crie os arquivos só quando houver algo a escrever.

## Durante a sessão

### Confronte com o glossário

Quando o usuário usar um termo que conflita com o glossário, aponte na hora: "O glossário define 'cancelamento' como
X, mas você parece querer dizer Y. Qual dos dois?"

### Afie a linguagem vaga

Quando o termo for vago ou sobrecarregado, proponha um termo canônico preciso: "Você diz 'conta': é o Cliente ou o
Usuário? São coisas diferentes."

### Discuta cenários concretos

Quando as relações do domínio estiverem em discussão, teste-as com cenários específicos. Invente cenários que
cutuquem os casos de borda e obriguem a precisão nas fronteiras entre os conceitos.

### Cruze com o código

Quando o usuário disser como algo funciona, confira se o código concorda (fato: subagente Haiku). Achou contradição,
mostre: "O código cancela o Pedido inteiro, mas você disse que o cancelamento parcial é possível. Qual está certo?"

### Atualize o glossário na hora

Termo resolvido → glossário atualizado ali mesmo, no formato de [`GLOSSARIO-FORMATO.md`](GLOSSARIO-FORMATO.md). Não
acumule para depois.

O glossário não tem detalhe de implementação. Não é especificação, rascunho nem depósito de decisões técnicas: é só
um glossário.

### Registre decisões com parcimônia

Proponha registrar uma decisão só quando as três condições valem:

1. **Difícil de reverter:** mudar de ideia depois custa caro.
2. **Surpreendente sem contexto:** quem ler o código vai perguntar "por que fizeram assim?".
3. **Fruto de um trade-off real:** havia alternativas de verdade e uma foi escolhida por motivos específicos.

Faltou uma, não registre. Formato em [`DECISAO-FORMATO.md`](DECISAO-FORMATO.md).

Os **não** valem tanto quanto os sim: decisões de fronteira e escopo ("o contexto de Cobrança só referencia o
Cliente por id") entram, e alimentam o "fora do escopo" das tarefas.
