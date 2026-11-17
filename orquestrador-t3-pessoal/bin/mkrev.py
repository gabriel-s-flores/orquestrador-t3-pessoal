#!/usr/bin/env python3
# Gera tarefas/<ID>/brief-revisor-c<CICLO>.md a partir de modelos/brief-revisor.md.
# Uso: <estado>/bin/mkrev.py <ID> <PR> <HEAD_SHA> <CICLO> <notas.md | -> [--alvo <papel | provedor:modelo:effort>]
# O brief leva o trecho do modelo do revisor (prompts/rev-<família>.md, PROMPTS.md): por padrão REVISOR, ou
# REVISOR_CRITICO nas classes G e GG; --alvo REVISOR_RESERVA quando o revisor padrão está fora.
# Do ciclo 2 em diante, as notas levam o histórico: devolutiva anterior, resposta do implementador, objeções em aberto.
# Com REVISAO_RODADA="curta" no orq.env e modelos/brief-revisor-rodada.md na pasta de estado (REVISAO.md), o ciclo 2
# em diante sai como rodada curta: só a correção e os achados abertos. Volta sozinho para a revisão completa quando
# falta o head revisado do ciclo anterior, ele não é ancestral do head novo, ou a correção passa de RODADA_MAX_LINHAS.
#   --completa            força a revisão completa
#   --anterior <sha>      head revisado no ciclo anterior (padrão: a linha "Head revisado:" de revisao-c<N-1>.md)
#   --reprovar 1.2,3.4    critérios que pedem prova nova nesta rodada (ligados a achado ou tocados pela correção).
#                         A rodada curta exige esta opção: sem ela sai a revisão completa. "--reprovar nenhum" quando
#                         nenhum critério está ligado a achado.
# A escolha fica em tarefas/<ID>/rodada-c<N>.json, que o provas.py lê.
import sys, os, re, json, subprocess
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params, preencher, Entrada, spec_de, alvo_tarefa, bloco, nota_windows
O = estado(); P = params(O)
a = sys.argv[1:]
alvo = None
if '--alvo' in a:
    i = a.index('--alvo'); alvo = a[i + 1]; del a[i:i + 2]
def opt(nome):
    if nome in a:
        i = a.index(nome)
        if i + 1 >= len(a):
            sys.exit(f'mkrev.py: {nome} pede um valor')
        v = a[i + 1]; del a[i:i + 2]; return v
    return ''
anterior = opt('--anterior'); tem_reprovar = '--reprovar' in a
reprovar = [x for x in re.split(r'[,\s]+', opt('--reprovar')) if x and x.lower() != 'nenhum']
completa = '--completa' in a
a = [x for x in a if x != '--completa']
if len(a) != 5:
    sys.exit('uso: mkrev.py <ID> <PR> <HEAD_SHA> <CICLO> <notas.md | -> [--alvo <papel | provedor:modelo:effort>] '
             '[--completa] [--anterior <sha>] [--reprovar <critérios>]')
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
# Rodada curta ou revisão completa (REVISAO.md). Sem a chave REVISAO_RODADA, nada muda: revisão completa.
n = int(re.match(r'\d+', ciclo).group()) if re.match(r'\d+', ciclo) else 1
modelo_brief = f'{O}/modelos/brief-revisor.md'; rodada = {}
curta = f'{O}/modelos/brief-revisor-rodada.md'
if n >= 2 and P.get('REVISAO_RODADA'):
    git = lambda *x: subprocess.run(['git', '-C', P.get('CHECKOUT', '.'), *x], capture_output=True, text=True)
    if not anterior:
        try:
            mm = re.search(r'^Head revisado:\s*`?([0-9a-f]{7,40})', open(f'{d}/revisao-c{n - 1}.md').read(), re.M)
            anterior = mm.group(1) if mm else ''
        except FileNotFoundError:
            anterior = ''
    linhas = None; motivo = ''
    if P['REVISAO_RODADA'] != 'curta': motivo = f'REVISAO_RODADA="{P["REVISAO_RODADA"]}"'
    elif not os.path.exists(curta): motivo = 'a pasta de estado não tem modelos/brief-revisor-rodada.md'
    elif completa: motivo = 'pedida com --completa'
    elif not tem_reprovar: motivo = 'faltou --reprovar <critérios ligados aos achados> (ou --reprovar nenhum)'
    elif not anterior: motivo = f'sem "Head revisado:" em revisao-c{n - 1}.md (passe --anterior <sha>)'
    elif git('merge-base', '--is-ancestor', anterior, head).returncode != 0:
        motivo = f'{anterior[:9]} não é ancestral de {head[:9]} (histórico reescrito, ou falta git fetch no CHECKOUT)'
    else:
        st = git('log', '--no-merges', '--shortstat', '--format=', f'{anterior}..{head}', '--not', f"origin/{P['BASE']}").stdout
        linhas = sum(int(x) for x in re.findall(r'(\d+) (?:insertion|deletion)', st))
        maximo = int(P.get('RODADA_MAX_LINHAS') or 400)
        if linhas > maximo: motivo = f'correção com {linhas} linhas (RODADA_MAX_LINHAS={maximo})'
    rodada = {'tipo': 'completa' if motivo else 'curta', 'motivo': motivo, 'anterior': anterior, 'linhas': linhas, 'reprovar': reprovar}
    json.dump(rodada, open(f'{d}/rodada-c{ciclo}.json', 'w'), ensure_ascii=False, indent=1)
    if rodada['tipo'] == 'curta': modelo_brief = curta
    print('mkrev: rodada curta' + (f' ({linhas} linhas desde {anterior[:9]})' if not motivo else f' não: revisão completa, {motivo}'), file=sys.stderr)
s = preencher(open(modelo_brief).read(), {
    'HEAD_ANTERIOR': rodada.get('anterior') or '—', 'CICLO_ANTERIOR': str(n - 1), 'LINHAS': str(rodada.get('linhas') or 0),
    'REPROVAR': ', '.join(f'`{x}`' for x in reprovar) or 'nenhum além dos que a correção tocar', 'ACHADOS': f'{d}/achados.md',
    'BLOCO_MODELO': '\n\n'.join(x for x in (nota_windows(), bloco(O, 'rev', modelo) if modelo else '') if x),
    'ID': tid, 'CICLO': ciclo, 'PR_URL': url, 'PR_NUMERO': pr, 'HEAD_SHA': head, 'DIR_TAREFA': d,
    'CRITERIOS': crit, 'PROVAS': ', '.join(e.provas_exigidas()), 'ISSUE': e.linha('Issue') or '—',
    'ORQ': O, 'BASE': P['BASE'], 'REPO': P.get('REPO', ''), 'ORQ_NOME': P.get('ORQ_NOME', 'Orquestrador'),
})
s = s.rstrip('\n') + '\n\n## Notas do orquestrador para esta revisão\n' + notas.strip() + '\n'
f = f'{d}/brief-revisor-c{ciclo}.md'
open(f, 'w').write(s)
print(f)
