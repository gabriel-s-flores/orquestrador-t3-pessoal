# Incluído pelos scripts do orquestrador. Descobre a pasta de estado e carrega orq.env (exportado para os filhos).
# A pasta de estado é a que contém o link bin/ → esta pasta da skill: chame os scripts por <estado>/bin/<script>.
# ORQ no ambiente tem precedência.
# No Git Bash (Windows): ORQ sai no formato C:/... (o Python do Windows não entende /c/...), o orq.env pode ter CRLF
# e o Python roda em modo UTF-8 (WINDOWS.md).
case "$(uname -s 2>/dev/null)" in MINGW*|MSYS*|CYGWIN*) ORQ_WIN=1 ;; *) ORQ_WIN= ;; esac
if [ -z "${ORQ:-}" ]; then
  if [ -n "$ORQ_WIN" ]; then ORQ=$(cd "$(dirname "$0")/.." && pwd -W); else ORQ=$(cd "$(dirname "$0")/.." && pwd); fi
elif [ -n "$ORQ_WIN" ]; then
  ORQ=$(cygpath -m "$ORQ" 2>/dev/null || echo "$ORQ")
fi
[ -f "$ORQ/orq.env" ] || { echo "orquestrador: $ORQ/orq.env não existe (chame por <estado>/bin/... ou defina ORQ)" >&2; exit 2; }
export ORQ
[ -n "$ORQ_WIN" ] && export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
set -a
# shellcheck disable=SC1090,SC1091
. <(tr -d '\r' < "$ORQ/orq.env")
set +a
