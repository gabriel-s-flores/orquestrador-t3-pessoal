#!/usr/bin/env python3
# Mede onde o tempo de cada tarefa foi, a partir de tarefas/<ID>/eventos.jsonl (gravado pelo agentes.py). Serve para
# comparar um épico com outro: as mesmas contas da medição de novembro de 2026 (LICOES.md).
# Uso: <estado>/bin/tempos.py [--json] [<ID>...]
#   Por tarefa, em minutos e com as pausas descontadas: despacho→PRONTO, PRONTO→merge e, dentro deste, revisores
#   rodando, correção depois de devolutiva, espera antes do primeiro revisor e espera depois da aprovação.
#   A coluna "bases" conta os pedidos de atualização da base (evento atualizar-base): mais de 1 por tarefa é retrabalho.
#   No fim, medianas por classe e com ou sem devolutiva. Tarefa sem os eventos pronto e merge fica fora das contas.
import os, sys, json, glob
from datetime import datetime
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, Entrada
O = estado()
a = sys.argv[1:]
em_json = '--json' in a
ids = [x for x in a if not x.startswith('--')] or sorted(os.path.basename(os.path.dirname(f)) for f in glob.glob(f'{O}/tarefas/*/eventos.jsonl'))
dt = datetime.fromisoformat
mn = lambda x, y: (y - x).total_seconds() / 60
med = lambda v: sorted(v)[len(v) // 2] if v else None

def soma(intervalos, lo, hi):
    """Minutos cobertos pela união dos intervalos, dentro de [lo, hi]."""
    t = 0.0; fim = lo
    for x, y in sorted((max(x, lo), min(y, hi)) for x, y in intervalos if x < hi and y > lo):
        if y > fim:
            t += mn(max(x, fim), y); fim = y
    return t

linhas = []
for tid in ids:
    try:
        ev = [json.loads(l) for l in open(f'{O}/tarefas/{tid}/eventos.jsonl') if l.strip()]
    except FileNotFoundError:
        continue
    for e in ev:
        e['t'] = dt(e['em'])
    um = lambda nome, ultimo=False: next((e['t'] for e in (reversed(ev) if ultimo else ev) if e['evento'] == nome), None)
    despacho = next((e['t'] for e in ev if e['evento'] == 'estado' and e.get('papel') == 'impl' and e.get('estado') == 'rodando'), None)
    pronto, merge, aprovada = um('pronto'), um('merge', True), um('aprovada', True)
    rev, pausa, aberto = [], [], {}
    for e in ev:
        if e['evento'] != 'estado':
            continue
        papel, est = e.get('papel', ''), e.get('estado')
        if papel.startswith('rev'):
            if est == 'rodando': aberto[papel] = e['t']
            elif papel in aberto: rev.append((aberto.pop(papel), e['t']))
        if est == 'pausada': aberto['pausa:' + papel] = e['t']
        elif 'pausa:' + papel in aberto: pausa.append((aberto.pop('pausa:' + papel), e['t']))
    corr = []; dev = None
    for e in ev:
        if e['evento'] == 'devolutiva': dev = e['t']
        elif e['evento'] == 'pronto' and dev: corr.append((dev, e['t'])); dev = None
    try:
        classe = Entrada(O, tid).classe() or '?'
    except SystemExit:
        classe = '?'
    if tid == 'SUITE' or not despacho:
        continue
    r = {'tarefa': tid, 'classe': classe, 'devolutivas': sum(1 for e in ev if e['evento'] == 'devolutiva'),
         'bases': sum(1 for e in ev if e['evento'] == 'atualizar-base'),
         'revisores': sum(1 for e in ev if e['evento'] == 'estado' and e.get('papel', '').startswith('rev') and e.get('estado') == 'rodando')}
    if despacho and pronto:
        r['impl'] = mn(despacho, pronto) - soma(pausa, despacho, pronto)
    if pronto and merge:
        r['gate'] = mn(pronto, merge) - soma(pausa, pronto, merge)
        r['revisao'] = soma(rev, pronto, merge); r['correcao'] = soma(corr, pronto, merge)
        r['antes_revisor'] = mn(pronto, min(x for x, _ in rev)) if rev and min(x for x, _ in rev) > pronto else 0.0
        r['pos_aprovacao'] = mn(aprovada, merge) if aprovada and aprovada < merge else 0.0
    linhas.append(r)

if em_json:
    print(json.dumps(linhas, ensure_ascii=False, indent=1)); sys.exit(0)
f = lambda v: '   —' if v is None else f'{v:4.0f}'
print('tarefa        classe  impl  PRONTO→merge  revisão  correção  antes do revisor  pós-aprovação  devolutivas  revisores  bases')
for r in linhas:
    print(f"{r['tarefa']:13} {r['classe']:5} {f(r.get('impl'))}  {f(r.get('gate')):>12}  {f(r.get('revisao')):>7}  {f(r.get('correcao')):>8}  "
          f"{f(r.get('antes_revisor')):>16}  {f(r.get('pos_aprovacao')):>13}  {r['devolutivas']:11}  {r['revisores']:9}  {r['bases']:5}")
ok = [r for r in linhas if 'gate' in r]
print(f'\n{len(ok)} de {len(linhas)} tarefas com PRONTO e merge registrados (minutos, pausas descontadas)')
def resumo(nome, rs):
    if not rs:
        return
    g = sum(r['gate'] for r in rs) or 1
    print(f"{nome:22} n={len(rs):3} · impl mediana {f(med([r['impl'] for r in rs if 'impl' in r]))} · PRONTO→merge mediana {f(med([r['gate'] for r in rs]))} "
          f"soma {g / 60:5.1f}h · revisores {100 * sum(r['revisao'] for r in rs) / g:3.0f}% · correção {100 * sum(r['correcao'] for r in rs) / g:3.0f}% · "
          f"antes do revisor {100 * sum(r['antes_revisor'] for r in rs) / g:3.0f}% · pós-aprovação {100 * sum(r['pos_aprovacao'] for r in rs) / g:3.0f}%")
def rodadas(pasta, prefixo, nome):
    try:
        ev = [json.loads(l) for l in open(f'{O}/tarefas/{pasta}/eventos.jsonl') if l.strip()]
    except FileNotFoundError:
        return
    ini = {e.get('head'): dt(e['em']) for e in ev if e['evento'] == prefixo + '-inicio'}
    rod = [(mn(ini[e.get('head')], dt(e['em'])), e.get('resultado', '?')) for e in ev if e['evento'] == prefixo + '-fim' and e.get('head') in ini]
    if rod:
        print(f"{nome}: {len(rod)} rodada(s), {sum(1 for _, x in rod if x == 'verde')} verde(s), mediana {f(med([m for m, _ in rod]))} min, soma {sum(m for m, _ in rod) / 60:.1f}h")
rodadas('SUITE', 'suite', 'suíte longa'); rodadas('PONTA', 'ponta', 'checagem de ponta')
if linhas:
    print(f"pedidos de base: {sum(r['bases'] for r in linhas)} em {len(linhas)} tarefa(s); {sum(1 for r in linhas if r['bases'] > 1)} tarefa(s) com mais de 1")
resumo('todas', ok); resumo('sem devolutiva', [r for r in ok if not r['devolutivas']]); resumo('com devolutiva', [r for r in ok if r['devolutivas']])
for c in ('P', 'M', 'G', 'GG'):
    resumo('classe ' + c, [r for r in ok if r['classe'] == c])
