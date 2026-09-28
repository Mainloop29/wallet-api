# Wallet API

REST API для работы с кошельками пользователей.

## Стек

- **FastAPI** — асинхронный веб-фреймворк
- **SQLAlchemy 2.0** (async) + **asyncpg** — работа с БД
- **PostgreSQL 16** — база данных
- **Alembic** — миграции
- **Docker / docker-compose** — инфраструктура
- **pytest + httpx + pytest-asyncio** — тесты

## Запуск

Всё поднимается одной командой из корня проекта:

```bash
docker compose up --build
```

Подожди ~30–60 секунд. В логах увидишь:

```
wallet-api-api-1  | INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial wallets table
wallet-api-api-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

После этого API доступно:

- **Swagger UI** — http://localhost:8000/docs
- **Healthcheck** — http://localhost:8000/health

### Остановка

```bash
docker compose down          # остановить, данные сохранятся
docker compose down -v       # остановить и удалить данные БД
```

## Эндпоинты

### Получить баланс кошелька

```
GET /api/v1/wallets/{wallet_id}
```

**Пример:**

```bash
curl http://localhost:8000/api/v1/wallets/3f2a1c9e-8d4b-4a2f-9c1e-1b2c3d4e5f6a
```

**Ответ:**

```json
{
  "id": "3f2a1c9e-8d4b-4a2f-9c1e-1b2c3d4e5f6a",
  "balance": "1000.00"
}
```

### Изменить баланс кошелька

```
POST /api/v1/wallets/{wallet_id}/operation
Content-Type: application/json
```

**Тело запроса:**

```json
{
  "operation_type": "DEPOSIT",
  "amount": 1000
}
```

- `operation_type`: `"DEPOSIT"` или `"WITHDRAW"`.
- `amount`: положительное число, не более 2 знаков после запятой.

**Пример:**

```bash
curl -X POST http://localhost:8000/api/v1/wallets/3f2a1c9e-8d4b-4a2f-9c1e-1b2c3d4e5f6a/operation \
  -H "Content-Type: application/json" \
  -d '{"operation_type": "DEPOSIT", "amount": 1000}'
```

**Ответ:**

```json
{
  "id": "3f2a1c9e-8d4b-4a2f-9c1e-1b2c3d4e5f6a",
  "balance": "1000.00"
}
```

### Ошибки

| Код | Причина |
|-----|---------|
| `404` | Кошелёк не найден |
| `400` | Недостаточно средств для списания |
| `422` | Некорректные данные (отрицательная сумма, неизвестный `operation_type`) |

## Конкурентность

Приложение корректно обрабатывает **параллельные запросы к одному кошельку**.

Изменение баланса выполняется в транзакции с `SELECT ... FOR UPDATE`, что:

- **сериализует** параллельные операции над одним кошельком,
- **исключает потерянные обновления** при параллельных депозитах,
- **не даёт уйти в минус** при параллельных списаниях.

### Проверка вручную

После запуска API создай кошелёк и запусти 20 параллельных депозитов по 100:

```bash
# Создать кошелёк (эндпоинта создания нет — создаём через psql)
docker compose exec db psql -U wallet -d wallet_db \
  -c "INSERT INTO wallets (id, balance) VALUES (gen_random_uuid(), 0) RETURNING id;"

# Записать UUID в переменную
WID="<вставь UUID>"

# 20 параллельных депозитов
for i in $(seq 1 20); do
  curl -s -X POST "http://localhost:8000/api/v1/wallets/$WID/operation" \
    -H "Content-Type: application/json" \
    -d '{"operation_type":"DEPOSIT","amount":100}' &
done
wait

# Проверить баланс
curl "http://localhost:8000/api/v1/wallets/$WID"
```

**Ожидаемый результат:** `balance = 2000.00` (а не меньше — как было бы при гонке).

## Тесты

Запускаются в отдельном контейнере (Linux), изолированно:

```bash
docker compose --profile tests run --rm tests
```

**Ожидаемый результат:**

```
============================= 8 passed in X.XXs ==============================
```

8 тестов покрывают:

- получение баланса,
- 404 для несуществующего кошелька,
- депозит,
- списание,
- недостаток средств,
- валидацию отрицательной суммы,
- **20 параллельных депозитов** (итог = 2000),
- **20 параллельных списаний** (итог = 0, 10 успехов + 10 отказов).

## Структура проекта

```
wallet-api/
├── alembic/                 # миграции Alembic
│   ├── versions/
│   │   └── 0001_initial.py
│   ├── env.py
│   └── script.py.mako
├── app/                     # код приложения
│   ├── routers/
│   │   └── wallets.py       # эндпоинты
│   ├── config.py            # настройки из env
│   ├── crud.py              # работа с БД + SELECT FOR UPDATE
│   ├── database.py          # движок, сессия, Base
│   ├── exceptions.py        # 404 и 400
│   ├── main.py              # точка входа FastAPI
│   ├── models.py            # ORM-модель Wallet
│   └── schemas.py           # Pydantic-схемы
├── tests/                   # тесты
│   ├── conftest.py
│   └── test_wallets.py
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

## Переменные окружения

Смотри `.env.example`. Для локального запуска скопируй его в `.env`:

```bash
cp .env.example .env
```

- `DATABASE_URL` — строка подключения к PostgreSQL.
- `DB_ECHO` — `true`, чтобы видеть SQL-запросы в логах.

## Разработка без Docker

Если хочешь запустить API локально:

```bash
python -m venv .venv
source .venv/Scripts/activate 
# или
source .venv/bin/activate   

pip install -r requirements.txt

cp .env.example .env

alembic upgrade head
uvicorn app.main:app --reload
```