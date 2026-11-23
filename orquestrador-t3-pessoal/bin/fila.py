#!/usr/bin/env python3
# Fila de integração (INTEGRACAO.md): os PRs aprovados entram no épico um por vez. Quem tem a vez é o único que faz
# merge ou traz a base; enquanto ele não sai, a base fica parada e ninguém a traz duas vezes.
# Estado em <estado>/fila.json. Rode depois de `git fetch origin` no CHECKOUT: a ação vem do bin/base.py.
# Uso:
#   fila.py                         a fila na ordem em que anda, e quem tem a vez
#   fila.py entra <ID> <PR> <head>  PR aprovado e provado entra; de novo, com o head novo, depois de uma atualização
#   fila.py vez                     quem age agora e o que faz (dá a vez ao próximo quando ninguém a tem):
#       ACAO=merge      head em dia: feche o portão e faça o merge
#       ACAO=direto     atrás da base, sem arquivo em comum: o mesmo merge, sem trazer a base
#       ACAO=servidor   merge limpo com arquivo em comum: gh pr update-branch (o GitHub traz a base, sem agente)
#       ACAO=atualizar  o implementador traz a base e roda as checagens (MERGE_LIMPO="atualizar")
#       ACAO=resolver   conflito: o implementador resolve
#       ACAO=esperar    o pedido já saiu neste head (fila.py pediu)
#       ACAO=passar     o dono da vez esperou mais que INTEGRACAO_PRAZO_MIN: rode fila.py passa <ID>
#       ACAO=buscar     o head não está no CHECKOUT: git fetch origin e rode de novo
#       ACAO=nada       fila vazia, ou parada (ponta vermelha, todos esperando o head novo)
#   fila.py pediu <ID>              o pedido de atualização saiu para quem tem a vez; grava o evento atualizar-base
#   fila.py passa <ID>              solta a vez sem sair da fila; volta a concorrer quando entrar com o head novo
#   fila.py sai <ID>                depois do merge, ou quando a tarefa volta para correção ou para uma rodada nova
# Ordem de quem recebe a vez: primeiro quem entra sem agente (merge, direto, servidor); depois quem libera mais
# tarefas do BACKLOG (caminho crítico); no empate, quem entrou antes. Quem já tem a vez termina.
# <estado>/PONTA_VERMELHA (IDs separados por espaço) para a fila: só essas tarefas, as da correção, recebem a vez.
import os, re, sys, json, datetime, subprocess
sys.dont_write_bytecode = True
BIN = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, BIN)
from _orq import estado, params, Entrada
O = estado(); P = params(O)
ARQ = f'{O}/fila.json'
DIRETO = P.get('MERGE_LIMPO', 'atualizar') == 'direto'
SEM_AGENTE = ('merge', 'direto', 'servidor')
agora = lambda: datetime.datetime.now().astimezone().isoformat(timespec='seconds')
minutos = lambda desde: int((datetime.datetime.now().astimezone() - datetime.datetime.fromisoformat(desde)).total_seconds() // 60)

def prazo():
    try:
        return int(float(P.get('INTEGRACAO_PRAZO_MIN', '') or 30))
    except ValueError:
        return 30

def ler():
    try:
        return json.load(open(ARQ)).get('itens', [])
    except FileNotFoundError:
        return []

def gravar(itens):
    tmp = ARQ + '.tmp'
    json.dump({'itens': itens}, open(tmp, 'w'), ensure_ascii=False, indent=1); os.replace(tmp, ARQ)

def item(itens, tid):
    for i in itens:
        if i['id'] == tid:
            return i
    sys.exit(f'fila: {tid} não está na fila')

def base_de(head):
    """Resultado do bin/base.py para o head: EM DIA, LIMPO, COMUM, CONFLITO, ou ? quando o head não está no CHECKOUT."""
    r = subprocess.run([sys.executable, os.path.join(BIN, 'base.py'), head], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', env={**os.environ, 'ORQ': O})
    m = re.search(r'^Resultado: (.+)$', r.stdout or '', re.M)
    return m.group(1).strip() if m else '?'

def acao_de(base):
    if base == '?':
        return 'buscar'
    if base == 'EM DIA':
        return 'merge'
    if base == 'CONFLITO':
        return 'resolver'
    if not DIRETO:
        return 'atualizar'
    return 'direto' if base == 'LIMPO' else 'servidor'

def liberadas():
    """Por tarefa, quantas tarefas do BACKLOG dependem dela, direta ou indiretamente."""
    try:
        ids = re.findall(r'^### (\S+) · ', open(f'{O}/BACKLOG.md').read(), re.M)
    except FileNotFoundError:
        return {}
    dep = {}
    for t in ids:
        try:
            bruto = Entrada(O, t).linha('Depende de')
        except SystemExit:
            bruto = ''
        dep[t] = {x.strip('`') for x in re.split(r'[,\s]+', bruto)} & set(ids)
    conta = {}
    for t in ids:
        visto, pilha = set(), [t]
        while pilha:
            x = pilha.pop()
            for f in ids:
                if x in dep[f] and f not in visto:
                    visto.add(f); pilha.append(f)
        conta[t] = len(visto)
    return conta

def esperando_head(i):
    """Passou a vez com o pedido em aberto: só volta a concorrer quando entrar com o head novo."""
    return bool(i.get('passou') and i.get('pedido') and i['pedido'].get('head') == i['head'])

def vermelha():
    """IDs que podem andar com a ponta vermelha; None = ponta sem alerta."""
    try:
        return set(open(f'{O}/PONTA_VERMELHA').read().split())
    except FileNotFoundError:
        return None

def ordenados(itens, lib):
    """Candidatos à vez, na ordem: (chave, item, base, ação)."""
    so = vermelha(); c = []
    for i in itens:
        if esperando_head(i) or (so is not None and i['id'] not in so):
            continue
        b = base_de(i['head']); a = acao_de(b)
        c.append(((a not in SEM_AGENTE, -lib.get(i['id'], 0), i['entrou']), i, b, a))
    return sorted(c, key=lambda x: x[0])

def do_dono(i):
    """Base e ação de quem tem a vez, contando o pedido em aberto e o prazo."""
    b = base_de(i['head']); a = acao_de(b); ped = i.get('pedido')
    desde = ped['em'] if ped and ped.get('head') == i['head'] else i['vez']
    if ped and ped.get('head') == i['head'] and a != 'merge':
        a = 'passar' if minutos(desde) > prazo() else 'esperar'
    elif a not in SEM_AGENTE and a != 'buscar' and minutos(desde) > prazo():
        a = 'passar'
    return b, a, minutos(desde)

cmd = sys.argv[1] if len(sys.argv) > 1 else ''
a = sys.argv[2:]
itens = ler()
if cmd == 'entra' and len(a) == 3:
    tid, pr, head = a[0], a[1].lstrip('#'), a[2]
    i = next((x for x in itens if x['id'] == tid), None)
    if i is None:
        i = {'id': tid, 'pr': pr, 'head': head, 'entrou': agora(), 'vez': None, 'pedido': None, 'passou': None}
        itens.append(i)
    else:
        if i['head'] != head:
            i['pedido'] = None; i['passou'] = None
        i['pr'], i['head'] = pr, head
    gravar(itens)
    print(f'{tid} na fila (#{pr}, {head[:9]}); {len(itens)} PR(s)')
elif cmd == 'sai' and len(a) == 1:
    item(itens, a[0])
    gravar([x for x in itens if x['id'] != a[0]])
    print(f'{a[0]} saiu da fila; {len(itens) - 1} PR(s)')
elif cmd == 'passa' and len(a) == 1:
    i = item(itens, a[0])
    i['vez'] = None; i['passou'] = agora()
    gravar(itens)
    print(f'{a[0]} soltou a vez' + ('; volta a concorrer quando entrar com o head novo' if esperando_head(i) else ''))
elif cmd == 'pediu' and len(a) == 1:
    i = item(itens, a[0])
    if not i.get('vez'):
        sys.exit(f'fila: {a[0]} não tem a vez; pedido de base só para quem tem (fila.py vez)')
    i['pedido'] = {'head': i['head'], 'em': agora()}
    gravar(itens)
    os.makedirs(f'{O}/tarefas/{a[0]}', exist_ok=True)
    with open(f'{O}/tarefas/{a[0]}/eventos.jsonl', 'a') as f:
        f.write(json.dumps({'em': agora(), 'evento': 'atualizar-base', 'head': i['head']}, ensure_ascii=False) + '\n')
    print(f'{a[0]} pedido registrado no head {i["head"][:9]}')
elif cmd == 'vez' and not a:
    if not itens:
        print('# fila vazia\nACAO=nada'); sys.exit(0)
    dono = next((x for x in itens if x.get('vez')), None)
    if dono is None:
        cands = ordenados(itens, liberadas())
        if not cands:
            motivo = 'ponta vermelha: só a correção anda' if vermelha() is not None else 'todos esperam o head novo'
            print(f'# fila: {len(itens)} PR(s), parada ({motivo})\nACAO=nada'); sys.exit(0)
        _, dono, b, ac = cands[0]
        dono['vez'] = agora(); dono['passou'] = None
        gravar(itens); esp = 0
    else:
        b, ac, esp = do_dono(dono)
        so = vermelha()
        if so is not None and dono['id'] not in so and ac in SEM_AGENTE:
            print(f'# fila: {len(itens)} PR(s), parada (ponta vermelha: {dono["id"]} tem a vez e espera a correção)\nACAO=nada')
            sys.exit(0)
    print(f'# fila: {len(itens)} PR(s) · vez de {dono["id"]} (#{dono["pr"]}) há {esp} min')
    print(f'VEZ={dono["id"]}\nPR={dono["pr"]}\nHEAD={dono["head"]}\nBASE={b}\nACAO={ac}\nESPERA={esp}/{prazo()}')
elif not cmd or cmd == 'mostra':
    if not itens:
        print('fila vazia'); sys.exit(0)
    lib = liberadas()
    dono = next((x for x in itens if x.get('vez')), None)
    linhas = []
    if dono:
        b, ac, esp = do_dono(dono)
        linhas.append((dono, b, ac, f'tem a vez há {esp} min'))
    for _, i, b, ac in ordenados([x for x in itens if x is not dono], lib):
        linhas.append((i, b, ac, 'na fila'))
    fora = [x for x in itens if x is not dono and x not in [l[0] for l in linhas]]
    for i in fora:
        linhas.append((i, '—', '—', 'espera o head novo' if esperando_head(i) else 'parada: ponta vermelha'))
    print(f'fila de integração: {len(itens)} PR(s) · MERGE_LIMPO={"direto" if DIRETO else "atualizar"}'
          + (' · PONTA VERMELHA' if vermelha() is not None else ''))
    for n, (i, b, ac, sit) in enumerate(linhas, 1):
        print(f'{n}. {i["id"]} #{i["pr"]} {i["head"][:9]} · base {b} · ação {ac} · libera {lib.get(i["id"], 0)} · {sit}')
else:
    sys.exit(open(os.path.realpath(__file__)).read().split('\nimport ')[0].replace('#!/usr/bin/env python3\n', ''))
