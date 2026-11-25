#!/usr/bin/env bash
#
# Gnana setup.sh — one command to go from a fresh clone to a running website.
# Safe to re-run: it creates missing config, starts web+db+redis (Docker),
# applies the DB, seeds the demo users, and waits until the site answers.
#
# Usage (run from the repo root):
#   bash setup.sh                 # full stack (web + Postgres + Redis via Docker)
#   USE_SQLITE=1 bash setup.sh    # skip Docker, run the app against a local SQLite file
#
# Needs: a Linux box (dnf/apt/yum), an outbound internet connection.
# Important: you still must open port 8000 in the server's firewall /
# AWS Security Group before the site is reachable from outside.

set -euo pipefail
cd "$(dirname "$0")"          # always work relative to this script

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[setup]${NC} $*"; }
warn() { echo -e "${YELLOW}[setup]${NC} $*"; }
die()  { echo -e "${RED}[setup]${NC} $*" >&2; exit 1; }

SUDO=""
[ "$(id -u)" -eq 0 ] || SUDO="sudo"

# ---------------------------------------------------------------------------
# 1) choose DB path, find a package manager and a decent Python
# ---------------------------------------------------------------------------
DB_ENGINE=postgres
if [ "${USE_SQLITE:-0}" = "1" ]; then
  DB_ENGINE=sqlite
  warn "USE_SQLITE=1 -> skipping Docker; using a SQLite file instead"
fi

if   command -v dnf     >/dev/null 2>&1; then PKG=dnf
elif command -v apt-get >/dev/null 2>&1; then PKG=apt
elif command -v yum     >/dev/null 2>&1; then PKG=yum
else die "No supported package manager found (need dnf/apt/yum)."; fi

PY=""
for candidate in python3.12 python3.11 python3.10 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then PY="$candidate"; break; fi
done
[ -n "$PY" ] || die "Python is not installed."

# Project needs Python >= 3.10
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || die "Python $("$PY" -c 'import sys; print(sys.version.split()[0])') is too old; install Python 3.10+."

# ---------------------------------------------------------------------------
# 2) install system packages (idempotent; missing ones only)
# ---------------------------------------------------------------------------
info "package manager: $PKG   |   python: $PY"

# dnf: if a package pull would fail because curl conflicts with the
# preinstalled curl-minimal (Amazon Linux 2023), retry with --allowerasing
# so curl-minimal is swapped for full curl instead of dying.
try_install_dnf() {
  if ! $SUDO "$PKG" install -y "$1" >/dev/null 2>&1; then
    warn "first install of $1 failed; retrying with --allowerasing (curl-minimal swap)"
    $SUDO "$PKG" install -y --allowerasing "$1" >/dev/null 2>&1 \
      || warn "could not install $1"
  fi
}

case "$PKG" in
  dnf|yum)
    # Install only what's missing. AL2023 ships `curl` as `curl-minimal`; the
    # full curl package conflicts with it, so never force-install curl if the
    # curl binary already exists.
    command -v make >/dev/null 2>&1 || try_install_dnf make
    command -v curl >/dev/null 2>&1 || try_install_dnf curl
    command -v git  >/dev/null 2>&1 || try_install_dnf git
    if ! command -v "$PY" >/dev/null 2>&1; then try_install_dnf "$PY"; fi
    if [ "$DB_ENGINE" = postgres ]; then
      if ! command -v docker >/dev/null 2>&1; then
        try_install_dnf docker
      fi
      if ! docker compose version >/dev/null 2>&1; then
        command -v docker-compose-plugin >/dev/null 2>&1 \
          || try_install_dnf docker-compose-plugin
      fi
      $SUDO systemctl enable --now docker >/dev/null 2>&1 || true
    fi
    ;;
  apt)
    $SUDO apt-get update -qq >/dev/null
    command -v make >/dev/null 2>&1 || $SUDO apt-get install -y -qq make >/dev/null
    command -v curl >/dev/null 2>&1 || $SUDO apt-get install -y -qq curl >/dev/null
    command -v git  >/dev/null 2>&1 || $SUDO apt-get install -y -qq git >/dev/null
    command -v "$PY" >/dev/null 2>&1 \
      || $SUDO apt-get install -y -qq "$PY" >/dev/null 2>&1 \
      || warn "could not install $PY via apt (using existing)"
    if [ "$DB_ENGINE" = postgres ]; then
      command -v docker >/dev/null 2>&1 \
        || $SUDO apt-get install -y -qq docker.io >/dev/null 2>&1 \
        || warn "Docker install failed; we will fall back to SQLite if needed"
      $SUDO apt-get install -y -qq docker-compose-plugin >/dev/null 2>&1 || true
      $SUDO systemctl enable --now docker >/dev/null 2>&1 || true
    fi
    ;;
esac

# Detect whichever compose binary exists: `docker compose` (v2) or the
# legacy `docker-compose` (v1). Docker is required for Postgres+Redis; if
# neither is usable, fall back to SQLite.
COMPOSE=""
if [ "$DB_ENGINE" = postgres ]; then
  if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
  fi
  if [ -z "$COMPOSE" ]; then
    warn "Docker Compose is not available -> falling back to SQLite"
    DB_ENGINE=sqlite
  fi
fi

# ---------------------------------------------------------------------------
# 3) .env — create, set a real SECRET_KEY, allow this server's public IP
# ---------------------------------------------------------------------------
if [ ! -f .env ]; then
  warn ".env missing -> creating it from .env.example"
  cp .env.example .env
fi

if grep -qE '^(SECRET_KEY=|SECRET_KEY=replace-with)' .env; then
  KEY=$("$PY" -c "import secrets; print(secrets.token_urlsafe(50))")
  sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$KEY|" .env
  info "generated a fresh SECRET_KEY"
fi

PUBLIC_IP=$(curl -s --max-time 5 http://checkip.amazonaws.com || true)
if [ -z "$PUBLIC_IP" ]; then PUBLIC_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || true); fi
if [ -n "$PUBLIC_IP" ] && ! grep -qF "$PUBLIC_IP" .env; then
  sed -i "s|^DJANGO_ALLOWED_HOSTS=.*|&,$PUBLIC_IP|" .env
  info "added $PUBLIC_IP to DJANGO_ALLOWED_HOSTS"
fi

sed -i "s|^DB_ENGINE=.*|DB_ENGINE=$DB_ENGINE|" .env

# ---------------------------------------------------------------------------
# 4) Python deps — create the venv and install everything
# ---------------------------------------------------------------------------
info "installing Python dependencies into .venv (may take a few minutes)"
if [ ! -x .venv/bin/python ]; then "$PY" -m venv .venv; fi
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

# ---------------------------------------------------------------------------
# 5) start the app — with Docker (web+db+redis) or with a local venv (SQLite)
# ---------------------------------------------------------------------------
if [ "$DB_ENGINE" = postgres ]; then
  info "building and starting web + Postgres + Redis (Docker)"
  $COMPOSE down --remove-orphans >/dev/null 2>&1 || true
  $COMPOSE up -d --build
  info "waiting for the web app to answer on :8000..."
  up=0
  for _ in $(seq 1 90); do
    if curl -s -o /dev/null --max-time 2 http://localhost:8000/accounts/login/; then up=1; break; fi
    sleep 2
  done
  if [ "$up" = 1 ]; then
    info "web app is up (container: web; see: $COMPOSE ps)"
  else
    warn "web did not answer; last logs:"
    $COMPOSE logs web | tail -20
    warn "Run: $COMPOSE ps / $COMPOSE logs web"
    exit 1
  fi
else
  # SQLite path: no Docker, plain local venv.
  info "applying database migrations"
  .venv/bin/python manage.py migrate --noinput

  info "seeding demo users (one per role)"
  .venv/bin/python manage.py seed_demo_users

  info "starting dev server on 0.0.0.0:8000"
  pkill -f "manage.py runserver" >/dev/null 2>&1 || true
  sleep 1
  LOG=/tmp/gnana-runserver.log
  nohup .venv/bin/python manage.py runserver 0.0.0.0:8000 >"$LOG" 2>&1 &
  SERVER_PID=$!

  up=0
  for _ in $(seq 1 15); do
    if curl -s -o /dev/null --max-time 2 http://localhost:8000/accounts/login/; then up=1; break; fi
    sleep 1
  done
  if [ "$up" = 1 ]; then
    info "server is up (PID $SERVER_PID, log: $LOG)"
  else
    warn "server did not answer; last log lines:"
    tail -5 "$LOG"
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 8) summary
# ---------------------------------------------------------------------------
PASS=$(grep -E '^DEMO_PASSWORD=' .env | cut -d= -f2)
PASS=${PASS:-demo1234}
echo
info "============================================================"
info "Website:  http://${PUBLIC_IP:-<server-ip>}:8000/accounts/login/"
info "Password: $PASS  (every demo account uses the same one)"
info "Accounts: superadmin@demo.gnana.in  admin@demo.gnana.in"
info "          teacher@demo.gnana.in  student@demo.gnana.in"
info "          parent@demo.gnana.in"
info "If the site doesn't load: open TCP port 8000 in your"
info "AWS Security Group (or server firewall) for your IP."
info "============================================================"
