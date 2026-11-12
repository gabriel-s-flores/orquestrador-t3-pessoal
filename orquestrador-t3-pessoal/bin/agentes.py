#!/usr/bin/env python3
# Registro dos agentes de cada tarefa em tarefas/<ID>/agentes.json (fonte para pausa, retomada, carga e órfãos).
# Uso:
#   agentes.py set <ID> <papel> chave=valor...   papel: impl | rev-c<N> | plano. Chaves usuais: taskId, threadId,
#                                                alvo, worktree, estado (rodando|pausando|pausada|concluida|cancelada)
#   agentes.py ativos [--json | --contar]        estado rodando ou pausando
#   agentes.py pausados [--json]                 estado pausada
#   agentes.py worktrees                         worktrees registradas (todas as tarefas)
#   agentes.py mostra <ID>
import sys, os, json, glob, datetime
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado
O = estado()
agora = lambda: datetime.datetime.now().astimezone().isoformat(timespec='seconds')

def arq(tid):
    return f'{O}/tarefas/{tid}/agentes.json'

def ler(tid):
    try:
        return json.load(open(arq(tid)))
    except FileNotFoundError:
        return {}

def todos():
    for f in sorted(glob.glob(f'{O}/tarefas/*/agentes.json')):
        tid = os.path.basename(os.path.dirname(f))
        for papel, a in json.load(open(f)).items():
            yield tid, papel, a

def listar(estados, modo):
    sel = [(t, p, a) for t, p, a in todos() if a.get('estado') in estados]
    if modo == '--contar':
        print(len(sel))
    elif modo == '--json':
        print(json.dumps([{'tarefa': t, 'papel': p, **a} for t, p, a in sel], ensure_ascii=False, indent=1))
    else:
        for t, p, a in sel:
            print(f"{t}\t{p}\t{a.get('estado')}\ttask={a.get('taskId', '—')}\tthread={str(a.get('threadId', '—'))[:8]}"
                  f"\talvo={a.get('alvo', '—')}\tdesde={a.get('desde', '—')}")

cmd = sys.argv[1] if len(sys.argv) > 1 else ''
if cmd == 'set':
    tid, papel, pares = sys.argv[2], sys.argv[3], sys.argv[4:]
    os.makedirs(os.path.dirname(arq(tid)), exist_ok=True)
    d = ler(tid); a = d.setdefault(papel, {})
    for par in pares:
        if '=' not in par:
            sys.exit(f'agentes.py: "{par}" não é chave=valor')
        k, v = par.split('=', 1)
        if k == 'taskId' and a.get('taskId') and a['taskId'] != v:
            a.setdefault('historico', []).append({'taskId': a['taskId'], 'ate': agora()})
        a[k] = v
    if a.get('estado') == 'rodando' and 'desde' not in a:
        a['desde'] = agora()
    a['atualizado'] = agora()
    tmp = arq(tid) + '.tmp'
    json.dump(d, open(tmp, 'w'), ensure_ascii=False, indent=1); os.replace(tmp, arq(tid))
    print(f'{tid} {papel}: ' + ', '.join(f'{k}={v}' for k, v in a.items() if k != 'historico'))
elif cmd == 'ativos':
    listar({'rodando', 'pausando'}, sys.argv[2] if len(sys.argv) > 2 else '')
elif cmd == 'pausados':
    listar({'pausada'}, sys.argv[2] if len(sys.argv) > 2 else '')
elif cmd == 'worktrees':
    for w in sorted({a['worktree'] for _, _, a in todos() if a.get('worktree')}):
        print(w)
elif cmd == 'mostra':
    print(json.dumps(ler(sys.argv[2]), ensure_ascii=False, indent=1))
else:
    sys.exit(open(os.path.realpath(__file__)).read().split('\nimport ')[0].replace('#!/usr/bin/env python3\n', ''))
