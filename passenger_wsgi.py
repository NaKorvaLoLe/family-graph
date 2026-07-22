"""WSGI entry for Passenger (Beget and similar shared hosting)."""
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
APP_DIR = PROJECT_DIR.parent
VENV_SITE = APP_DIR / 'env' / 'lib'

# Add project to path
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Prefer venv site-packages (Python 3.x)
if VENV_SITE.exists():
    for site in VENV_SITE.glob('python*/site-packages'):
        sys.path.insert(0, str(site))
        break

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Load .env from APP_DIR if present
env_file = APP_DIR / '.env'
if env_file.exists():
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

from config.wsgi import application  # noqa: E402
