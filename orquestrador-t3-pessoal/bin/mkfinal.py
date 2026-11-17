#!/usr/bin/env python3
# Gera tarefas/FINAL/brief-final-<n>.md a partir de modelos/brief-revisao-final.md, para a revisão final do épico
# (REVISAO.md). O texto é o mesmo para todos os revisores; muda o número e o trecho do modelo de cada um.
# Uso: <estado>/bin/mkfinal.py <n> <papel | provedor:modelo:effort> [notas.md | -]
#   <n>: 1, 2, 3… na ordem de CONSELHO (ou 1 com REVISOR_CRITICO, na revisão final de um revisor só)
import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params, preencher, spec_de, bloco, nota_windows
O = estado(); P = params(O)
a = sys.argv[1:]
if len(a) not in (2, 3):
    sys.exit('uso: mkfinal.py <n> <papel | provedor:modelo:effort> [notas.md | -]')
n, alvo = a[0], a[1]
notas = '' if len(a) == 2 else (sys.stdin.read() if a[2] == '-' else open(a[2]).read())
modelo = spec_de(P, alvo)[1]
d = f'{O}/tarefas/FINAL'
os.makedirs(d, exist_ok=True)
s = preencher(open(f'{O}/modelos/brief-revisao-final.md').read(), {
    'N': n, 'ORQ': O, 'BASE': P['BASE'], 'ORIGEM': P.get('ORIGEM', 'main'),
    'ORQ_NOME': P.get('ORQ_NOME', 'Orquestrador'), 'BLOCO_MODELO': '\n\n'.join(x for x in (nota_windows(), bloco(O, 'rev', modelo)) if x),
})
if notas.strip():
    s = s.rstrip('\n') + '\n\n## Notas do orquestrador para esta revisão\n' + notas.strip() + '\n'
f = f'{d}/brief-final-{n}.md'
open(f, 'w').write(s)
print(f)
