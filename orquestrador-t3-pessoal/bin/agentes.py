#!/usr/bin/env python3
# Registro dos agentes de cada tarefa em tarefas/<ID>/agentes.json (fonte para pausa, retomada, carga e órfãos) e dos
# eventos com hora em tarefas/<ID>/eventos.jsonl (fonte do bin/tempos.py; o arquivo só cresce).
# Uso:
#   agentes.py set <ID> <papel> chave=valor...   papel: impl | rev-c<N> | plano. Chaves usuais: taskId, threadId,
#                                                alvo, worktree, estado (rodando|pausando|pausada|concluida|cancelada)
#                                                Mudança de estado ou de taskId vira evento sozinha.
#   agentes.py evento <ID> <evento> [chave=valor...]   o que o set não vê: pronto | veredito | devolutiva | aprovada |
#                                                merge | atualizar-base | suite-inicio | suite-fim
#                                                (chaves usuais: head, ciclo, resultado, pr)
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

def evento(tid, nome, **campos):
    os.makedirs(f'{O}/tarefas/{tid}', exist_ok=True)
    with open(f'{O}/tarefas/{tid}/eventos.jsonl', 'a') as f:
        f.write(json.dumps({'em': agora(), 'evento': nome, **campos}, ensure_ascii=False) + '\n')

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
    antes = (a.get('estado'), a.get('taskId'))
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
    if a.get('estado') != antes[0]:
        evento(tid, 'estado', papel=papel, estado=a.get('estado'), alvo=a.get('alvo', ''))
    elif a.get('taskId') != antes[1]:
        evento(tid, 'taskId', papel=papel)
    print(f'{tid} {papel}: ' + ', '.join(f'{k}={v}' for k, v in a.items() if k != 'historico'))
elif cmd == 'evento' and len(sys.argv) >= 4:
    campos = {}
    for par in sys.argv[4:]:
        if '=' not in par:
            sys.exit(f'agentes.py: "{par}" não é chave=valor')
        k, v = par.split('=', 1); campos[k] = v
    evento(sys.argv[2], sys.argv[3], **campos)
    print(f'{sys.argv[2]} evento {sys.argv[3]}' + ''.join(f' {k}={v}' for k, v in campos.items()))
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
