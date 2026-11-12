# Incluído pelos scripts do orquestrador. Descobre a pasta de estado e carrega orq.env (exportado para os filhos).
# A pasta de estado é a que contém o link bin/ → esta pasta da skill: chame os scripts por <estado>/bin/<script>.
# ORQ no ambiente tem precedência.
if [ -z "${ORQ:-}" ]; then ORQ=$(cd "$(dirname "$0")/.." && pwd); fi
[ -f "$ORQ/orq.env" ] || { echo "orquestrador: $ORQ/orq.env não existe (chame por <estado>/bin/... ou defina ORQ)" >&2; exit 2; }
export ORQ
set -a
# shellcheck disable=SC1091
. "$ORQ/orq.env"
set +a
