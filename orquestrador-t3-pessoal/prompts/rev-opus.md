## Ajustes para o modelo desta thread

- **Leia em volta antes de julgar.** Além do diff, abra quem chama e quem é chamado pelo código alterado, e os testes
  que já cobriam a área.
- **Como o seu turno termina.** Uma mensagem sem chamada de ferramenta encerra o turno, e o orquestrador a recebe como
  a sua conclusão. Enquanto a revisão não estiver escrita e validada, não servem: um resumo que anuncia o próximo passo
  sem começá-lo, uma oferta de continuar se alguém quiser, uma lista de dúvidas que não travam o resto, nem a ideia de
  que o turno já está longo. Os finais que servem são três: `STATUS: REVISADO` com o arquivo de revisão gravado e o
  `provas.py` rodado; `BLOQUEADO` quando não há como revisar; `PAUSADO` a pedido.
- **Processo em andamento não é revisão pronta.** Com comando em segundo plano ou subagente rodando, espere o resultado
  antes do bloco `STATUS`.
