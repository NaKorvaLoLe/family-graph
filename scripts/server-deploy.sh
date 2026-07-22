#!/usr/bin/env bash
# Запускается на сервере из PUBLIC_HTML после git pull.
# Ожидает: APP_DIR (venv рядом), PUBLIC_HTML (код проекта).

set -euo pipefail

APP_DIR="${APP_DIR:?APP_DIR is required}"
PUBLIC_HTML="${PUBLIC_HTML:-$PWD}"

ENV_DIR="$APP_DIR/env"
PYTHON="$ENV_DIR/bin/python"
PIP="$ENV_DIR/bin/pip"

cd "$PUBLIC_HTML"

echo "=== Activate venv & install deps ==="
"$PIP" install --upgrade pip
"$PIP" install -r requirements.txt

# .env рядом с проектом или на уровень выше (не в git)
if [ -f "$APP_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$APP_DIR/.env"
  set +a
elif [ -f "$PUBLIC_HTML/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$PUBLIC_HTML/.env"
  set +a
fi

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings}"

echo "=== Migrate ==="
"$PYTHON" manage.py migrate --noinput

echo "=== Collect static ==="
"$PYTHON" manage.py collectstatic --noinput

# Passenger (Beget и др.): перезапуск приложения
mkdir -p tmp
touch tmp/restart.txt

# Если используете systemd/gunicorn — раскомментируйте:
# systemctl --user restart familygraph || true

echo "=== Deploy finished ==="
"$PYTHON" -c "import django; print('Django', django.get_version())"
