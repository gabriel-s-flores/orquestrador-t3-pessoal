#!/usr/bin/env python3
# Comenta no PR do GitHub o resumo das provas de uma revisão aprovada (PROVAS.md). Os arquivos de prova ficam na
# pasta de estado; o comentário lista, por critério, qual arquivo prova o quê, e leva a revisão.
# Uso: pr-provas.py --checar                                  gh instalado e autenticado
#      pr-provas.py <ID> <ciclo> [--pr <url|número>] [--simular]   comenta (só com PROVADO; repetir não duplica)
import os, re, sys, json, shutil, subprocess, tempfile, datetime
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params, mascarar
O = estado(); P = params(O)
a = sys.argv[1:]
simular = '--simular' in a
a = [x for x in a if x != '--simular']
pr = None
if '--pr' in a:
    i = a.index('--pr'); pr = a[i + 1]; del a[i:i + 2]

def gh(*args):
    if not shutil.which('gh'):
        sys.exit('pr-provas: o gh (GitHub CLI) não está instalado')
    return subprocess.run(['gh', *args], capture_output=True, text=True)

if '--checar' in a:
    r = gh('auth', 'status')
    if r.returncode:
        sys.exit('pr-provas: gh sem autenticação (rode "gh auth login" num terminal)')
    print(f'GitHub ok: gh autenticado · repositório {P.get("REPO", "—")}'); sys.exit(0)

if len(a) != 2:
    sys.exit('uso: pr-provas.py <ID> <ciclo> [--pr <url|número>] [--simular] | --checar')
tid, ciclo = a
pasta = f'{O}/tarefas/{tid}/evidencias/revisao-c{ciclo}'
r = subprocess.run([os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'provas.py'), tid, ciclo], capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout); sys.exit('pr-provas: as provas não estão PROVADO; nada foi enviado')
m = json.load(open(f'{pasta}/provas.json'))
pr = pr or m.get('pr') or ''
num = re.search(r'(\d+)\s*$', str(pr))
if not num:
    sys.exit('pr-provas: sem o número do PR (passe --pr ou grave "pr" no provas.json)')
num = num.group(1)
limpo = lambda s: re.sub(r'[`|\n]', ' ', str(s or '')).strip()

linhas = [f'✅ Revisão aprovada (ciclo {ciclo}) · head `{str(m.get("head", ""))[:7]}`', '', '**Provas por critério**']
for c in m.get('criterios', []):
    provas = ', '.join(f'`{p.get("arquivo")}`' + (f' ({limpo(p.get("resumo"))})' if p.get('resumo') else '')
                       for p in c.get('provas', []))
    linhas.append(f'- {c.get("id")} {limpo(c.get("descricao"))[:100]}: {provas}')
for p in m.get('mutacao', []):
    linhas.append(f'- Mutação: `{p.get("arquivo")}`' + (f' ({limpo(p.get("resumo"))})' if p.get('resumo') else ''))
linhas += ['', 'Os arquivos de prova ficam na pasta de estado da orquestração, fora do repositório.']
rev = f'{O}/tarefas/{tid}/revisao-c{ciclo}.md'
if os.path.exists(rev):
    linhas += ['', '<details><summary>Revisão completa</summary>', '', open(rev).read().strip()[:40000], '', '</details>']
texto = mascarar('\n'.join(linhas))

livro_f = f'{O}/tarefas/{tid}/pr-comentarios.json'
livro = json.load(open(livro_f)) if os.path.exists(livro_f) else []
if any(str(x.get('ciclo')) == str(ciclo) and str(x.get('pr')) == num for x in livro):
    print(f'PR #{num}: comentário do ciclo {ciclo} já enviado'); sys.exit(0)
if simular:
    print(f'simulação: comentário no PR #{num} de {P.get("REPO", "—")}:\n{texto}'); sys.exit(0)
with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as f:
    f.write(texto)
try:
    r = gh('pr', 'comment', num, '-R', P['REPO'], '--body-file', f.name)
finally:
    os.unlink(f.name)
if r.returncode:
    sys.exit(f'pr-provas: gh pr comment falhou: {r.stderr.strip()[:300]}')
livro.append({'ciclo': ciclo, 'pr': num, 'em': datetime.datetime.now().astimezone().isoformat(timespec='seconds')})
json.dump(livro, open(livro_f, 'w'), ensure_ascii=False, indent=1)
print(f'PR #{num}: provas comentadas')
