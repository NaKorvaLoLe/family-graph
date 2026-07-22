# Family Graph

Семейный граф — интерактивная визуализация родственных связей на Three.js с Django-бэкендом.

## Возможности

- Приветственный экран с текстом о ценности семьи
- Интерактивный граф (родитель ↔ ребёнок, братья/сёстры)
- Узлы с фото или инициалами
- Hover — полное имя, клик — краткая информация
- Страница с полной биографией каждого человека
- Заполнение данных через Django Admin

## Установка

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Первоначальная настройка

1. Откройте http://127.0.0.1:8000/admin/
2. Создайте записи **Люди** (Person)
3. Добавьте связи **Родитель — ребёнок** и **Братья/сёстры**
4. При необходимости отредактируйте **Приветственный экран**
5. Откройте http://127.0.0.1:8000/

## Структура проекта

```
familyGraph/
├── config/              # Настройки Django
├── family/              # Основное приложение
│   ├── models.py        # Person, связи, WelcomeScreen
│   ├── admin.py         # Админ-панель
│   ├── views.py         # Страницы и API
│   └── urls.py
├── templates/           # HTML-шаблоны
├── static/
│   ├── scss/            # SCSS стили (компилируются автоматически)
│   └── js/              # Three.js граф
├── media/               # Загруженные фото
└── manage.py
```

## SCSS

Стили написаны на SCSS и компилируются автоматически через `django-sass-processor` при запуске сервера.

## Позиции на графе

В админке у каждого человека есть поля `graph_x` и `graph_y` для сохранения позиции. Если все позиции равны 0, узлы автоматически располагаются по кругу.

## Деплой (GitHub Actions + SSH пароль)

По схеме [appleboy/ssh-action](https://github.com/appleboy/ssh-action): push в `main`/`master` → SSH на сервер → `git pull` → `scripts/server-deploy.sh`.

### 1. Правки перед первым деплоем

В `.github/workflows/deploy.yml` замените:

- `/home/c/ck78395` и `familygraph` → путь сайта на хостинге (если другой)
- `BRANCH` → `main` или `master` (сейчас `main`)

### 2. Secrets в GitHub

**Settings → Secrets and variables → Actions:**

| Secret | Значение |
|--------|----------|
| `HOST` | SSH-хост (например `ck78395.beget.tech`) |
| `USERNAME` | логин SSH |
| `SSH_PASSWORD` | пароль SSH |
| `PORT` | `22` |
| `TOKEN_GITHUB` | [PAT](https://github.com/settings/tokens) с правом `repo` |

### 3. На сервере один раз

```text
/home/c/<login>/familygraph/
├── .env              ← из .env.example (SECRET_KEY, ALLOWED_HOSTS)
├── env/              ← создаст CI (venv)
└── public_html/      ← сюда клонируется репозиторий
```

Скопируйте `.env.example` → `$APP_DIR/.env` и заполните домен.

В панели хостинга для сайта укажите Python/Passenger на `passenger_wsgi.py` в `public_html`.

### 4. Запуск

Репозиторий: https://github.com/NaKorvaLoLe/family-graph

Дальше деплой идёт автоматически на каждый push в `main`/`master`, либо вручную: **Actions → CI/CD Pipeline → Run workflow**.
