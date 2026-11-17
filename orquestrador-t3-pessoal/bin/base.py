#!/usr/bin/env python3
# Diz se um PR atrás da base precisa trazer o épico antes do merge, e se um head atualizado ainda é o conteúdo que
# a revisão aprovou (INTEGRACAO.md). Só lê: roda no CHECKOUT do orq.env, depois de `git fetch origin`.
# Uso: <estado>/bin/base.py <head> [--repo DIR] [--base REF]
#        EM DIA    o head já contém a ponta da base                                      (código 0)
#        LIMPO     está atrás, o merge é limpo e nenhum arquivo do PR mudou na base     (código 0)
#        COMUM     o merge é limpo, mas a base mudou arquivos que o PR também muda      (código 1)
#        CONFLITO  o merge não é limpo                                                   (código 2)
#      <estado>/bin/base.py --equivale <head revisado> <head novo> [--repo DIR] [--base REF]
#        EQUIVALENTE  a mudança do PR em relação à base é a mesma nos dois heads        (código 0)
#        DIFERENTE    lista os arquivos em que ela mudou (correção nova ou conflito resolvido)  (código 1)
# Código 3 = erro (ref que não existe no checkout: faltou git fetch?).
import os, sys, subprocess
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from _orq import estado, params
O = estado(); P = params(O)
a = sys.argv[1:]
def opt(nome, padrao):
    if nome in a:
        i = a.index(nome); v = a[i + 1]; del a[i:i + 2]; return v
    return padrao
repo = opt('--repo', P.get('CHECKOUT', '.')); base = opt('--base', f"origin/{P['BASE']}")
equivale = '--equivale' in a
a = [x for x in a if x != '--equivale']
if len(a) != (2 if equivale else 1):
    sys.exit(open(os.path.realpath(__file__)).read().split('\nimport ')[0].replace('#!/usr/bin/env python3\n', ''))

def git(*x, ok=(0,), cru=False):
    """Roda o git no repositório. A saída vem em bytes do git: nome de arquivo com acento e conteúdo fora de UTF-8 não
    podem derrubar a conta. cru=True devolve os bytes (para o diff que vai ao patch-id)."""
    r = subprocess.run(['git', '--literal-pathspecs', '-C', repo, *x], capture_output=True)
    if r.returncode not in ok:
        erro = r.stderr.decode('utf-8', 'replace').strip()[:200]
        print(f'base: git {" ".join(x)} falhou: {erro} (faltou git fetch origin?)', file=sys.stderr); sys.exit(3)
    if not cru:
        r.stdout = r.stdout.decode('utf-8', 'surrogateescape')
    return r

def arquivos(de, ate):
    # -z: o nome sai como está no repositório, sem as aspas e os escapes que o git põe em nome com acento
    return set(git('diff', '--name-only', '--no-renames', '-z', de, ate).stdout.split('\0')) - {''}

def mudanca(head):
    """Por arquivo, a identidade da mudança do head em relação ao ponto em que ele saiu da base (patch-id)."""
    mb = git('merge-base', base, head).stdout.strip(); ids = {}
    for f in arquivos(mb, head):
        d = git('diff', '--no-renames', mb, head, '--', f, cru=True).stdout
        p = subprocess.run(['git', '-C', repo, 'patch-id', '--stable'], input=d, capture_output=True).stdout.split()
        ids[f] = p[0].decode() if p else 'binário-ou-vazio:' + git('rev-parse', f'{head}:{f}', ok=(0, 128)).stdout.strip()
    return ids

if equivale:
    velho, novo = mudanca(a[0]), mudanca(a[1])
    dif = sorted(f for f in set(velho) | set(novo) if velho.get(f) != novo.get(f))
    print(f'# {a[0][:9]} × {a[1][:9]} contra {base}: {len(novo)} arquivo(s) no PR')
    print('Resultado: ' + ('DIFERENTE' if dif else 'EQUIVALENTE'))
    for f in dif:
        print(f'- {f}' + ('' if f in velho and f in novo else ' (só num dos heads)'))
    sys.exit(1 if dif else 0)

head = a[0]
ponta = git('rev-parse', base).stdout.strip(); mb = git('merge-base', base, head).stdout.strip()
if mb == ponta:
    print(f'# {head[:9]} contém a ponta de {base}\nResultado: EM DIA'); sys.exit(0)
atras = git('rev-list', '--count', f'{head}..{base}').stdout.strip()
comum = sorted(arquivos(mb, head) & arquivos(mb, base))
limpo = git('merge-tree', '--write-tree', '--name-only', base, head, ok=(0, 1)).returncode == 0
print(f'# {head[:9]} está {atras} commit(s) atrás de {base}')
if not limpo:
    print('Resultado: CONFLITO'); sys.exit(2)
print('Resultado: ' + ('COMUM' if comum else 'LIMPO'))
for f in comum:
    print(f'- {f}')
sys.exit(1 if comum else 0)
