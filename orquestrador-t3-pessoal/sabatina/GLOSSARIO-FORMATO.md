# Formato do glossário

Adaptação de `CONTEXT-FORMAT.md` (Matt Pocock).

## Estrutura

```md
# {Nome do contexto}

{Uma ou duas frases: o que é este contexto e por que existe.}

## Linguagem

**Pedido**:
{Uma ou duas frases definindo o termo}
_Evite_: compra, transação

**Fatura**:
Cobrança enviada ao cliente depois da entrega.
_Evite_: boleto, conta

**Cliente**:
Pessoa ou organização que faz pedidos.
_Evite_: comprador, conta
```

## Regras

- **Tome partido.** Quando houver várias palavras para o mesmo conceito, escolha a melhor e liste as outras em
  `_Evite_`.
- **Definições curtas.** Uma ou duas frases no máximo. Diga o que a coisa *é*, não o que ela faz.
- **Só termos deste domínio.** Conceitos gerais de programação (timeout, tipo de erro, utilitários) ficam de fora,
  mesmo que o projeto os use muito. Antes de incluir, pergunte: é um conceito próprio deste contexto ou um conceito
  geral? Só o primeiro entra.
- **Agrupe em subtítulos** quando surgirem grupos naturais. Se tudo pertence a uma área só, uma lista plana basta.

## Um contexto ou vários

- **Um contexto (a maioria):** um glossário só.
- **Vários contextos:** um mapa (`$E/MAPA-DE-CONTEXTOS.md`) lista os contextos, onde vivem e
  como se relacionam:

```md
# Mapa de contextos

## Contextos

- [Pedidos](./GLOSSARIO-pedidos.md): recebe e acompanha os pedidos dos clientes
- [Cobrança](./GLOSSARIO-cobranca.md): gera faturas e processa pagamentos

## Relações

- **Pedidos → Cobrança**: Pedidos emite `PedidoEntregue`; Cobrança consome para gerar a fatura
- **Pedidos ↔ Cobrança**: tipos compartilhados `ClienteId` e `Dinheiro`
```

Com o mapa, descubra a que contexto o assunto pertence. Na dúvida, pergunte.
