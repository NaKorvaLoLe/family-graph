#!/usr/bin/env bash
# Запускается на сервере из PUBLIC_HTML после git pull.
# Ожидает: APP_DIR (venv рядом), PUBLIC_HTML (код проекта).
# Beget: часто нет ensurepip — создаём venv без pip и ставим get-pip.py

set -euo pipefail

APP_DIR="${APP_DIR:?APP_DIR is required}"
PUBLIC_HTML="${PUBLIC_HTML:-$PWD}"

ENV_DIR="$APP_DIR/env"
PYTHON="$ENV_DIR/bin/python"
PIP="$ENV_DIR/bin/pip"

cd "$PUBLIC_HTML"

ensure_venv() {
  if [ -x "$PIP" ]; then
    echo "=== venv already OK: $ENV_DIR ==="
    return
  fi

  echo "=== Create venv at $ENV_DIR ==="
  rm -rf "$ENV_DIR"

  if python3 -m venv --help 2>&1 | grep -q -- '--without-pip'; then
    python3 -m venv --without-pip "$ENV_DIR"
  else
    python3 -m venv "$ENV_DIR" || true
  fi

  if [ ! -x "$PYTHON" ]; then
    echo "ERROR: python not found in $ENV_DIR"
    exit 1
  fi

  if [ ! -x "$PIP" ]; then
    echo "=== Bootstrap pip (get-pip.py) ==="
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    "$PYTHON" /tmp/get-pip.py
    rm -f /tmp/get-pip.py
  fi

  if [ ! -x "$PIP" ]; then
    echo "ERROR: pip still missing in $ENV_DIR"
    exit 1
  fi
}

ensure_venv

echo "=== Install deps ==="
"$PIP" install --upgrade pip
"$PIP" install -r requirements.txt

# Безопасная загрузка .env (без source — иначе ломают $, ), # и т.п.)
load_env_file() {
  local file="$1"
  [ -f "$file" ] || return 0
  echo "=== Load env: $file ==="
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in
      ''|\#*) continue ;;
    esac
    case "$line" in
      *=*) ;;
      *) continue ;;
    esac
    local key="${line%%=*}"
    local value="${line#*=}"
    key="${key%"${key##*[![:space:]]}"}"
    key="${key#"${key%%[![:space:]]*}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ "$value" == \"*\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' ]]; then
      value="${value:1:${#value}-2}"
    fi
    export "${key}=${value}"
  done < "$file"
}

if [ -f "$PUBLIC_HTML/.env" ]; then
  load_env_file "$PUBLIC_HTML/.env"
elif [ -f "$PUBLIC_HTML/env" ] && [ ! -d "$PUBLIC_HTML/env" ]; then
  load_env_file "$PUBLIC_HTML/env"
elif [ -f "$APP_DIR/.env" ]; then
  load_env_file "$APP_DIR/.env"
fi

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings}"

echo "=== Migrate ==="
"$PYTHON" manage.py migrate --noinput

echo "=== Collect static ==="
"$PYTHON" manage.py collectstatic --noinput

mkdir -p tmp
touch tmp/restart.txt

# Timeweb: wsgi.py должен быть исполняемым
chmod +x wsgi.py 2>/dev/null || true

echo "=== Deploy finished ==="
"$PYTHON" -c "import django; print('Django', django.get_version())"
