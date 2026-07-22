#!/home/c/ck78395/familygraph/env/bin/python
"""WSGI entry for Timeweb (как у webworklife / blog)."""
import os
import sys
import traceback
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
APP_DIR = PROJECT_DIR.parent
VENV_DIR = APP_DIR / 'env'
ERROR_LOG = PROJECT_DIR / 'wsgi_error.log'


def _log(msg: str) -> None:
    try:
        with ERROR_LOG.open('a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except OSError:
        pass


def _load_env(path: Path) -> None:
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as exc:
        _log(f'Cannot read {path}: {exc}')
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


try:
    if str(PROJECT_DIR) not in sys.path:
        sys.path.insert(0, str(PROJECT_DIR))

    venv_site = VENV_DIR / 'lib'
    if venv_site.exists():
        for site in sorted(venv_site.glob('python*/site-packages'), reverse=True):
            sys.path.insert(0, str(site))
            break

    _load_env(PROJECT_DIR / '.env')
    if (PROJECT_DIR / 'env').is_file():
        _load_env(PROJECT_DIR / 'env')
    _load_env(APP_DIR / '.env')

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
except Exception:
    _log('=== wsgi.py crash ===')
    _log(traceback.format_exc())
    raise
