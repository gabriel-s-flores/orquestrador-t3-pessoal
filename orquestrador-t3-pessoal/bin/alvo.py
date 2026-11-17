#!/usr/bin/env python3
# Imprime o target do delegate_task para um papel, um alvo literal ou uma tarefa, a partir do orq.env (MODELOS.md).
# Uso: <estado>/bin/alvo.py <papel | provedor:modelo:effort> [opções]
#      <estado>/bin/alvo.py --tarefa <ID> [REVISOR] [opções]
#   papel: P | M | G | GG | REVISOR | REVISOR_CRITICO | REVISOR_RESERVA | PLANO_REVISOR | ORQUESTRADOR
#   --tarefa <ID>   implementador: modelo da classe da tarefa, com o **Effort:** dela se houver;
#                   com REVISOR: REVISOR_CRITICO nas classes G e GG, REVISOR nas outras
#   --acima         o próximo degrau da ESCADA (falha de cuidado: mais effort; no topo do modelo, o modelo seguinte)
#   --acima-modelo  o primeiro degrau do modelo seguinte (falha de capacidade)
#   --selecao       formato modelSelection (t3_thread_configure, t3_thread_launch)
#   --spec          formato provedor:modelo:effort (para gravar em agentes.py e passar de volta a --acima)
#   --bloco impl|rev  o trecho de brief deste modelo (para anexar à devolutiva quando o modelo muda)
#      <estado>/bin/alvo.py --lista CONSELHO     um target por linha, para cada alvo da lista (REVISAO.md, revisão final)
# Código 3 = topo da escada, ou modelo fora dela: não há degrau acima.
import sys, os, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params, spec_de, spec_txt, alvo_tarefa, acima, bloco, lista, opcao_effort
O = estado(); P = params(O)
a = sys.argv[1:]
def alvo_json(spec, chave='providerInstanceId'):
    prov, modelo, effort = spec
    opcoes = [{'id': opcao_effort(P, prov), 'value': effort}] if effort else []
    return json.dumps({chave: prov, 'model': modelo, 'options': opcoes}, ensure_ascii=False)
if len(a) == 2 and a[0] == '--lista':
    itens = lista(P, a[1].upper())
    if not itens:
        sys.exit(f'alvo.py: {a[1].upper()} vazio ou ausente no orq.env')
    for x in itens:
        print(alvo_json(spec_de(P, x)))
    sys.exit(0)
def opt(nome):
    if nome in a:
        i = a.index(nome)
        if i + 1 >= len(a):
            sys.exit(f'alvo.py: {nome} pede um valor')
        v = a[i + 1]; del a[i:i + 2]; return v
    return None
tarefa = opt('--tarefa'); papel_bloco = opt('--bloco')
flags = {x for x in a if x.startswith('--')}; pos = [x for x in a if not x.startswith('--')]
desconhecidas = flags - {'--acima', '--acima-modelo', '--selecao', '--spec'}
if desconhecidas or len(pos) > 1 or (not pos and not tarefa) or papel_bloco not in (None, 'impl', 'rev'):
    sys.exit(open(os.path.realpath(__file__)).read().split('\nimport ')[0].replace('#!/usr/bin/env python3\n', ''))
if tarefa:
    if pos and not pos[0].upper().startswith('REVISOR'):
        sys.exit('alvo.py: com --tarefa, o papel só pode ser REVISOR (sem papel = implementador)')
    spec = alvo_tarefa(O, P, tarefa, revisor=bool(pos)) if not pos or pos[0].upper() == 'REVISOR' else spec_de(P, pos[0])
else:
    spec = spec_de(P, pos[0])
if flags & {'--acima', '--acima-modelo'}:
    novo = acima(P, spec, so_modelo='--acima-modelo' in flags)
    if not novo:
        print(f'alvo.py: {spec_txt(spec)} não tem degrau acima na ESCADA (topo, ou modelo fora dela)', file=sys.stderr)
        sys.exit(3)
    spec = novo
prov, modelo, effort = spec
if papel_bloco:
    print(bloco(O, papel_bloco, modelo))
elif '--spec' in flags:
    print(spec_txt(spec))
else:
    print(alvo_json(spec, 'instanceId' if '--selecao' in flags else 'providerInstanceId'))
