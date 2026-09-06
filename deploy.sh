#!/usr/bin/env bash
#
# Deploy in one command, in the right order, stopping at the first failure.
#
# Running "git pull" alone is what breaks the site: the templates and models
# become the new ones while the database columns and the collected static files
# are still the old ones. Every page that touches a new field then returns 500,
# and the browser keeps loading last release's CSS.
#
#   ./deploy.sh
#
set -euo pipefail

cd "$(dirname "$0")"

# The cPanel virtualenv, when it is not already active.
VENV="${VENV:-$HOME/virtualenv/as-artgroup/3.12/bin/activate}"
if [ -z "${VIRTUAL_ENV:-}" ] && [ -f "$VENV" ]; then
  # shellcheck disable=SC1090
  source "$VENV"
fi

step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

step "1/5  Kodu çəkirəm"
git pull --ff-only

step "2/5  Asılılıqları yoxlayıram"
pip install -q -r requirements.txt

step "3/5  Bazanı köçürürəm"
# --noinput so an interactive prompt cannot hang a deploy.
python manage.py migrate --noinput

step "4/5  Statik faylları yığıram"
python manage.py collectstatic --noinput

step "5/5  Konfiqurasiyanı yoxlayıram (xəbərdarlıqlar deploy-u dayandırmır)"
python manage.py check --deploy || true

mkdir -p tmp && touch tmp/restart.txt

printf '\n\033[1;32mDeploy tamamlandı.\033[0m Passenger yenidən başladıldı.\n'
printf 'Yoxlayın:  https://as-artgroup.az/az/\n\n'
