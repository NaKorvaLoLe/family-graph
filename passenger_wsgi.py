"""WSGI entry for Passenger (Beget and similar shared hosting)."""
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
# Beget: код в ~/familygraph/public_html, venv в ~/familygraph/env
APP_DIR = PROJECT_DIR.parent
VENV_DIR = APP_DIR / 'env'
# если venv лежит внутри public_html (как на некоторых сайтах)
if not VENV_DIR.exists() and (PROJECT_DIR / 'env').exists():
    VENV_DIR = PROJECT_DIR / 'env'

VENV_SITE = VENV_DIR / 'lib'

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if VENV_SITE.exists():
    for site in sorted(VENV_SITE.glob('python*/site-packages'), reverse=True):
        sys.path.insert(0, str(site))
        break

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# .env в public_html (как у вас) или рядом в familygraph/
_load_env(PROJECT_DIR / '.env')
_load_env(PROJECT_DIR / 'env')  # если файл без точки: public_html/env
_load_env(APP_DIR / '.env')

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
