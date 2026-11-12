#!/usr/bin/env python3
# Gera tarefas/<ID>/brief.md a partir de modelos/brief-implementador.md e da entrada da tarefa no BACKLOG.md.
# Uso: <estado>/bin/mkbrief.py <ID> <notas.md | -> [--alvo <papel | provedor:modelo:effort>]
# O brief termina com o trecho do modelo que vai rodar a tarefa (prompts/impl-<família>.md, PROMPTS.md): por padrão o
# alvo da classe com o **Effort:** da tarefa; --alvo quando ela é despachada num degrau acima (alvo.py --acima).
# Campos da entrada: ver modelos/BACKLOG.md (Issue, Origem, Depende de, Classe, Escopo, Fora do escopo, Arquivos,
# Orçamento, Aceite, Evidências e, opcional, Branch). A fase é o último "## " antes da entrada.
import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params, preencher, Entrada, spec_de, alvo_tarefa, bloco
O = estado(); P = params(O)
a = sys.argv[1:]
alvo = None
if '--alvo' in a:
    i = a.index('--alvo'); alvo = a[i + 1]; del a[i:i + 2]
if len(a) != 2:
    sys.exit('uso: mkbrief.py <ID> <notas.md | -> [--alvo <papel | provedor:modelo:effort>]')
tid, notas_src = a
notas = sys.stdin.read() if notas_src == '-' else open(notas_src).read()
e = Entrada(O, tid)
if not e.classe():
    print(f'aviso: {tid} sem **Classe:** P|M|G|GG no BACKLOG; usando M', file=sys.stderr)
plano = lambda s, padrao: ' '.join(s.split()) or padrao
d = f'{O}/tarefas/{tid}'
os.makedirs(d + '/evidencias', exist_ok=True)
try:
    prov, modelo, effort = spec_de(P, alvo) if alvo else alvo_tarefa(O, P, tid)
except SystemExit as x:  # orq.env antigo, sem os alvos por classe: o brief sai sem o trecho do modelo
    print(f'aviso: {x}; brief sem o trecho do modelo', file=sys.stderr); prov = modelo = effort = ''
out = preencher(open(f'{O}/modelos/brief-implementador.md').read(), {
    'BLOCO_MODELO': bloco(O, 'impl', modelo) if modelo else '', 'MODELO': modelo or '—', 'EFFORT': effort or '—',
    'ID': tid, 'TITULO': e.titulo, 'FASE': e.fase,
    'ISSUE': e.linha('Issue') or '—', 'ORIGEM': e.linha('Origem') or '—', 'CLASSE': e.classe() or 'M',
    'DEPENDENCIAS': e.linha('Depende de') or '—',
    'ESCOPO': plano(e.bloco('Escopo'), 'ver o título, o aceite e as notas do orquestrador.'),
    'FORA_ESCOPO': plano(e.bloco('Fora do escopo'), 'tudo o que o aceite não pede.'),
    'ARQUIVOS': ', '.join(f'`{g}`' for g in e.globs()) or 'não declarados: toque só o que o aceite exige e justifique no Mapa de escopo.',
    'ORCAMENTO': plano(e.bloco('Orçamento'), 'não declarado.'),
    'ACEITE': '\n'.join('  ' + l.strip() for l in (e.bloco('Aceite') or 'ver as notas do orquestrador').splitlines()),
    'EVIDENCIAS': plano(e.bloco('Evidências'), 'ver as notas do orquestrador.'),
    'PROVAS': ', '.join(e.provas_exigidas()),
    'NOTAS': notas.strip(), 'BRANCH': e.bloco('Branch').strip('`') or f"{P['PREFIXO']}/{tid.lower()}",
    'DIR_TAREFA': d, 'ORQ': O, 'BASE': P['BASE'], 'REPO': P.get('REPO', ''),
    'ORQ_NOME': P.get('ORQ_NOME', 'Orquestrador'),
})
open(d + '/brief.md', 'w').write(out)
print(d + '/brief.md')
