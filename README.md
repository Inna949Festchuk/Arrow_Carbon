## Arrow_Carbon
Проект по расчету углеродных единиц и ПДРЕ на основе спутниковых снимков и геоданных.

### Запуск проекта через Docker Compose

Ниже описан типичный сценарий запуска проекта в Docker‑окружении на базе Debian‑образа.

#### 1. Предварительные требования

- Установленные `docker` и `docker-compose` (или `docker compose`):
  - Проверьте установку:

```bash
docker --version
docker compose version  # для новых версий Docker
```

#### 2. Файл окружения `.env`

В корне проекта (`Arrow_Carbon`) создайте файл `.env` со значениями по умолчанию (их можно поменять под себя):

```bash
cat > .env << 'EOF'
POSTGRES_DB=pdre_db
POSTGRES_USER=pdre_user
POSTGRES_PASSWORD=pdre_password

# DJANGO_SECRET_KEY можно переопределить при необходимости
DJANGO_SECRET_KEY=dev-secret-key-change-me

# DEBUG=1 для разработки, 0 для продакшена
DJANGO_DEBUG=1
EOF
```

#### 3. Сборка образа и запуск контейнеров

Из корня репозитория (`/home/user/Документы/Arrow_Carbon`) выполните:

```bash
docker compose build
docker compose up
```

- `docker compose build` соберёт образ `web` на основе `Dockerfile` (Debian + Python + GeoDjango).
- `docker compose up` поднимет все сервисы:
  - `web` — Django‑приложение;
  - `db` — PostgreSQL + PostGIS;
  - `redis` — брокер сообщений для Celery;
  - `celery_worker` — фоновый обработчик задач;
  - `celery_beat` — планировщик периодических задач.

Django автоматически выполнит миграции при старте контейнера `web` (см. команду в `docker-compose.yml`).

#### 4. Доступ к приложению и сервисам

- Веб‑приложение Django:  
  `http://localhost:8000/`

- Админ‑панель Django:  
  `http://localhost:8000/admin/`

  Если суперпользователь ещё не создан, можно временно зайти внутрь контейнера `web` и создать его:

```bash
docker compose exec web python manage.py createsuperuser
```

- База данных PostgreSQL + PostGIS доступна на порту `5432` хоста (логин/пароль из `.env`).
- Redis доступен на порту `6379`.

#### 5. Полезные команды Docker

- Остановить все контейнеры (с сохранением данных в volume):

```bash
docker compose down
```

- Остановить и удалить контейнеры + сети + тома (полная очистка):

```bash
docker compose down -v
```

- Просмотреть логи только веб‑приложения:

```bash
docker compose logs -f web
```

- Выполнить произвольную Django‑команду (пример — миграции):

```bash
docker compose exec web python manage.py migrate
```
