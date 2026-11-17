#!/usr/bin/env python3
# Confere o manifesto de provas de uma revisão (PROVAS.md) antes de qualquer aprovação.
# Uso: <estado>/bin/provas.py <ID> <ciclo> [--head <sha>]     valida tarefas/<ID>/evidencias/revisao-c<N>/provas.json
#      <estado>/bin/provas.py <ID> --criterios                 critérios e tipos de prova exigidos pela tarefa
# Rodada curta (REVISAO.md): critério com "herdada_de": <ciclo> reaproveita a prova copiada do ciclo anterior. Só vale
# com rodada-c<N>.json do mkrev.py em "curta", fora dos critérios de "reprovar", e com as checagens do projeto
# regravadas no head novo ("checagens" no manifesto).
# Código 0 = PROVADO, 1 = INCOMPLETO, 2 = erro de uso.
import os, re, sys, json, shutil, subprocess
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params, Entrada, tem_segredo
O = estado(); P = params(O)
a = sys.argv[1:]
if not a:
    sys.exit('uso: provas.py <ID> <ciclo> [--head <sha>] | provas.py <ID> --criterios')
tid = a[0]; e = Entrada(O, tid)
exigidos = e.provas_exigidas(); criterios = e.criterios()
if '--criterios' in a:
    print(f'{tid} · tipos exigidos: {", ".join(exigidos)}')
    for cid, desc in criterios:
        print(f'- {cid}: {desc}')
    sys.exit(0)
ciclo = a[1]; head = a[a.index('--head') + 1] if '--head' in a else None
pasta = f'{O}/tarefas/{tid}/evidencias/revisao-c{ciclo}'
max_mb = float(P.get('PROVA_MAX_MB') or 20); max_s = float(P.get('PROVA_VIDEO_MAX_S') or 90)
falhas, avisos = [], []
try:
    m = json.load(open(f'{pasta}/provas.json'))
except FileNotFoundError:
    print(f'Resultado: INCOMPLETO\n- falta {pasta}/provas.json (modelo em PROVAS.md)'); sys.exit(1)
except json.JSONDecodeError as x:
    print(f'Resultado: INCOMPLETO\n- provas.json inválido: {x}'); sys.exit(1)
if head and not str(m.get('head', '')).startswith(head[:7]):
    falhas.append(f'head do manifesto ({str(m.get("head"))[:9]}) não é o head revisado ({head[:9]})')

def conferir(pr, onde):
    tipo, arq = pr.get('tipo'), pr.get('arquivo')
    if tipo not in ('log', 'mutacao', 'print', 'video', 'medicao', 'requisicao', 'arquivo'):
        falhas.append(f'{onde}: tipo de prova inválido "{tipo}"'); return None
    caminho = os.path.join(pasta, arq or '')
    if not arq or not os.path.isfile(caminho) or os.path.getsize(caminho) == 0:
        falhas.append(f'{onde}: arquivo ausente ou vazio "{arq}"'); return None
    mb = os.path.getsize(caminho) / 1048576
    if mb > max_mb:
        falhas.append(f'{onde}: {arq} tem {mb:.1f} MB (máximo {max_mb:g})')
    cabeca = open(caminho, 'rb').read(16)
    if tipo == 'print' and not (cabeca.startswith(b'\x89PNG') or cabeca.startswith(b'\xff\xd8')):
        falhas.append(f'{onde}: {arq} não é PNG nem JPEG')
    if tipo == 'video':
        if shutil.which('ffprobe'):
            r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', caminho],
                               capture_output=True, text=True)
            try:
                dur = float(r.stdout.strip())
                if dur > max_s: falhas.append(f'{onde}: {arq} tem {dur:.0f} s (máximo {max_s:g})')
            except ValueError:
                falhas.append(f'{onde}: {arq} não é um vídeo válido')
        else:
            avisos.append(f'{onde}: sem ffprobe para conferir {arq}')
    if tipo in ('log', 'mutacao', 'medicao', 'requisicao', 'arquivo'):
        txt = open(caminho, errors='replace').read()
        if tem_segredo(txt):
            falhas.append(f'{onde}: {arq} parece ter segredo ou dado pessoal; mascare antes')
        rc = re.findall(r'^# exit=(-?\d+)', txt, re.M)
        if tipo in ('log', 'mutacao', 'medicao', 'requisicao'):
            if not rc:
                falhas.append(f'{onde}: {arq} não foi gravado com bin/prova (sem "# exit=")')
            elif tipo == 'mutacao' and rc[-1] == '0':
                falhas.append(f'{onde}: {arq} é mutação com exit=0 (o teste não caiu)')
            elif tipo in ('log', 'medicao') and rc[-1] != '0':
                falhas.append(f'{onde}: {arq} terminou com exit={rc[-1]}')
    elif tipo in ('print', 'video'):
        avisos.append(f'{onde}: confira {arq} a olho: sem dados pessoais nem tokens na tela')
    return tipo

vistos = set()
por_id = {str(c.get('id')): c for c in m.get('criterios', [])}
linhas = []
herdadas = {cid: str(c.get('herdada_de')) for cid, c in por_id.items() if c.get('herdada_de') not in (None, '')}
if herdadas:
    try:
        rod = json.load(open(f'{O}/tarefas/{tid}/rodada-c{ciclo}.json'))
    except (FileNotFoundError, json.JSONDecodeError):
        rod = {}
    if rod.get('tipo') != 'curta':
        falhas.append('prova herdada só vale em rodada curta (falta rodada-c<N>.json do mkrev.py, ou a rodada é completa)')
    proibidos = {str(x) for x in rod.get('reprovar', [])}
    for cid, de in herdadas.items():
        if cid in proibidos:
            falhas.append(f'critério {cid} está ligado a um achado ou à correção: pede prova nova neste head')
        try:
            ant = json.load(open(f'{O}/tarefas/{tid}/evidencias/revisao-c{de}/provas.json'))
        except (FileNotFoundError, json.JSONDecodeError):
            falhas.append(f'critério {cid}: não achei o manifesto do ciclo {de} de onde a prova foi herdada'); continue
        if not any(str(x.get('id')) == cid and x.get('resultado') == 'ok' for x in ant.get('criterios', [])):
            falhas.append(f'critério {cid}: no ciclo {de} ele não estava "ok", então não há prova para herdar')
for cid, desc in criterios:
    c = por_id.get(cid)
    if not c:
        falhas.append(f'critério {cid} sem entrada no manifesto'); linhas.append(f'⛔ {cid} · {desc[:70]} · sem prova'); continue
    provas = c.get('provas') or []
    tipos = {conferir(p, f'critério {cid}') for p in provas} - {None}
    vistos |= tipos
    if c.get('resultado') != 'ok':
        falhas.append(f'critério {cid} com resultado "{c.get("resultado")}"')
    if not provas:
        falhas.append(f'critério {cid} sem prova')
    linhas.append(f'{"✅" if c.get("resultado") == "ok" and tipos else "⛔"} {cid} · {desc[:70]} · {", ".join(sorted(tipos)) or "—"}'
                  + (f' (herdada do ciclo {herdadas[cid]})' if cid in herdadas else ''))
for p in m.get('mutacao', []):
    t = conferir(p, 'mutação')
    if t: vistos.add(t)
if herdadas:
    no_head = False
    for p in m.get('checagens') or []:
        if conferir(p, 'checagem') == 'log':
            cab = open(os.path.join(pasta, p['arquivo']), errors='replace').readline()
            sha = re.search(r'head ([0-9a-f]{7,40})', cab)
            no_head = no_head or bool(sha and m.get('head') and str(m['head']).startswith(sha.group(1)[:7]))
    if not no_head:
        falhas.append('rodada curta: falta em "checagens" um log das checagens do projeto, gravado com bin/prova no head desta rodada')
for t in exigidos:
    if t not in vistos:
        falhas.append(f'falta prova do tipo "{t}" (exigido pela tarefa)')
res = 'INCOMPLETO' if falhas else 'PROVADO'
print(f'# Provas {tid} · ciclo {ciclo} · head {str(m.get("head", "—"))[:9]}\nResultado: {res}')
print('\n'.join(linhas))
for f in falhas: print(f'- {f}')
for x in avisos: print(f'- aviso: {x}')
sys.exit(1 if falhas else 0)
