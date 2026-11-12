#!/usr/bin/env python3
# Gera tarefas/<ID>/brief-revisor-c<CICLO>.md a partir de modelos/brief-revisor.md.
# Uso: <estado>/bin/mkrev.py <ID> <PR> <HEAD_SHA> <CICLO> <notas.md | -> [--alvo <papel | provedor:modelo:effort>]
# O brief leva o trecho do modelo do revisor (prompts/rev-<família>.md, PROMPTS.md): por padrão REVISOR, ou
# REVISOR_CRITICO nas classes G e GG; --alvo REVISOR_RESERVA quando o revisor padrão está fora.
# Do ciclo 2 em diante, as notas levam o histórico: devolutiva anterior, resposta do implementador, objeções em aberto.
import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params, preencher, Entrada, spec_de, alvo_tarefa, bloco
O = estado(); P = params(O)
a = sys.argv[1:]
alvo = None
if '--alvo' in a:
    i = a.index('--alvo'); alvo = a[i + 1]; del a[i:i + 2]
if len(a) != 5:
    sys.exit('uso: mkrev.py <ID> <PR> <HEAD_SHA> <CICLO> <notas.md | -> [--alvo <papel | provedor:modelo:effort>]')
tid, pr, head, ciclo, notas_src = a
notas = sys.stdin.read() if notas_src == '-' else open(notas_src).read()
d = f'{O}/tarefas/{tid}'
e = Entrada(O, tid)
crit = '\n'.join(f'  - `{cid}`: {desc}' for cid, desc in e.criterios()) or '  - (sem itens no aceite: veja o brief)'
url = f"https://github.com/{P['REPO']}/pull/{pr}"
try:
    modelo = (spec_de(P, alvo) if alvo else alvo_tarefa(O, P, tid, revisor=True))[1]
except SystemExit as x:  # orq.env antigo, sem REVISOR: o brief sai sem o trecho do modelo
    print(f'aviso: {x}; brief sem o trecho do modelo', file=sys.stderr); modelo = ''
s = preencher(open(f'{O}/modelos/brief-revisor.md').read(), {
    'BLOCO_MODELO': bloco(O, 'rev', modelo) if modelo else '',
    'ID': tid, 'CICLO': ciclo, 'PR_URL': url, 'PR_NUMERO': pr, 'HEAD_SHA': head, 'DIR_TAREFA': d,
    'CRITERIOS': crit, 'PROVAS': ', '.join(e.provas_exigidas()), 'ISSUE': e.linha('Issue') or '—',
    'ORQ': O, 'BASE': P['BASE'], 'REPO': P.get('REPO', ''), 'ORQ_NOME': P.get('ORQ_NOME', 'Orquestrador'),
})
s = s.rstrip('\n') + '\n\n## Notas do orquestrador para esta revisão\n' + notas.strip() + '\n'
f = f'{d}/brief-revisor-c{ciclo}.md'
open(f, 'w').write(s)
print(f)
