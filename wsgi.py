#!/home/c/ck78395/familygraph/env/bin/python
"""Точка входа Timeweb (mod_wsgi) — по официальной инструкции."""
import os
import sys
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


try:
    # 1) Активация venv (как требует Timeweb)
    activate_this = VENV_DIR / 'bin' / 'activate_this.py'
    if activate_this.is_file():
        exec(
            compile(activate_this.read_text(encoding='utf-8'), str(activate_this), 'exec'),
            {'__file__': str(activate_this)},
        )
    else:
        # python -m venv не создаёт activate_this.py — добавляем site-packages вручную
        site = VENV_DIR / 'lib'
        if site.exists():
            for pkg in sorted(site.glob('python*/site-packages'), reverse=True):
                sys.path.insert(0, str(pkg))
                break
        venv_python = VENV_DIR / 'bin' / 'python'
        if venv_python.exists():
            os.environ['VIRTUAL_ENV'] = str(VENV_DIR)

    # 2) Корень проекта
    project_path = str(PROJECT_DIR)
    if project_path not in sys.path:
        sys.path.insert(0, project_path)

    # 3) SQLite на Python 3.10 + mod_wsgi очень медленный (логин «висит»)
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    os.environ['HTTPS'] = 'on'

    from django.core.wsgi import get_wsgi_application

    _app = get_wsgi_application()

    def application(environ, start_response):
        environ['wsgi.url_scheme'] = 'https'
        environ['HTTPS'] = 'on'
        if 'HTTP_X_FORWARDED_PROTO' not in environ:
            environ['HTTP_X_FORWARDED_PROTO'] = 'https'
        return _app(environ, start_response)

except Exception:
    _log('=== wsgi.py crash ===\n')
    import traceback
    _log(traceback.format_exc())
    raise
