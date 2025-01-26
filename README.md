# Библиотечное API

Проект представляет собой RESTful API для управления библиотечным каталогом. Он предоставляет функциональность для работы с книгами, авторами, читателями и процессом выдачи книг, а также реализует авторизацию и аутентификацию с использованием JWT токенов.

## Описание функционала

### 1. Авторизация и Аутентификация
- **JWT токены**: Реализована аутентификация с использованием JWT токенов.
- **Роли пользователей**: Пользователи делятся на две роли:
  - **Администратор**: Может управлять всеми ресурсами (книги, авторы, пользователи).
  - **Читатель**: Может только просматривать книги и взаимодействовать с ними.

### 2. Управление книгами
- Реализованы CRUD операции для книг.
- Каждая книга имеет следующие поля:
  - ID
  - Название
  - Описание
  - Дата публикации
  - Автор(ы)
  - Жанр(ы)
  - Количество доступных экземпляров
- Все операции с книгами реализованы в эндпоинтах API через соответствующие модели и методы.

### 3. Управление авторами
- Реализованы CRUD операции для авторов.
- Поля автора:
  - ID
  - Имя
  - Биография
  - Дата рождения
- Для авторов предусмотрены отдельные CRUD операции.

### 4. Управление читателями
- Администратор может просматривать информацию о читателях.
- Читатели могут обновлять свою личную информацию через API.

### 5. Выдача и возврат книг
- Реализована возможность выдачи книги читателю с ограничением на 5 книг одновременно.
- Фиксируются дата выдачи и предполагаемая дата возврата.
- При возврате книги обновляется количество доступных экземпляров.

### 6. Дополнительные требования
- Пагинация и фильтрация реализованы для списков книг и авторов.
- Валидация входных данных с использованием Pydantic.
- Обработка ошибок с корректными HTTP статусами.
- Логирование действий (выдача, возврат книг) реализовано.
- Использование Alembic для миграций базы данных.
- **Тестирование**: Все эндпоинты покрыты юнит-тестами, которые успешно прошли.

## Технические характеристики

- Язык программирования: Python 3.8+
- Фреймворк: FastAPI
- База данных: PostgreSQL
- ORM: SQLAlchemy
- Аутентификация: JWT
- Управление миграциями: Alembic
- Тестирование: Pytest

## Структура проекта

literature_hub_api/
- alembic/
  - versions/
- app/
  - api/
    - v1/
      - endpoints/
        - auth_portal.py
        - authors.py
        - literature_items.py
        - transactions.py
        - users.py
      - __init__.py
    - __init__.py
  - core/
    - config.py
    - logging.py
    - security.py
    - __init__.py
  - db/
    - base.py
    - session.py
    - __init__.py
  - models/
    - user.py
    - author.py
    - literature_item.py
    - transactions.py
    - __init__.py
  - schemas/
    - auth_token.py
    - user.py
    - author.py
    - literature_item.py
    - login.py
    - transactions.py
    - __init__.py
  - utils.py
  - dependencies.py
  - main.py
- tests/
  - test_auth_portal.py
  - test_authors.py
  - test_literature_items.py
  - test_users.py
  - test_transactions.py
  - __init__.py
- venv/
- .env
- .gitignore
- app.log
- docker-compose.yml
- Dockerfile
- requirements.txt
- alembic.ini
- README.md


## Запуск проекта

### 1. Установка зависимостей:

```bash
pip install -r requirements.txt
```

### 2. Настройка базы данных:

Убедитесь, что у вас настроена база данных PostgreSQL, и создайте файл `.env` с необходимыми параметрами:

```bash
DATABASE_URL=postgresql://username:password@localhost/dbname
SECRET_KEY=your_secret_key
```

### 3. Миграции:

Примените миграции с помощью Alembic:

```bash
alembic upgrade head
```

### 4. Запуск приложения:

Для запуска проекта используйте Uvicorn:

```bash
uvicorn app.main:app --reload
```

### 5. Тестирование:

Для запуска тестов используйте Pytest:

```bash
pytest
```

## Docker

Проект полностью контейнеризован с использованием Docker. Это позволяет легко развернуть приложение и базу данных в любой среде.

### Запуск проекта с Docker

1. **Создание образов и запуск контейнеров**:
   Для начала необходимо собрать образы и запустить контейнеры с помощью Docker Compose:

   ```bash
   docker-compose up --build
   ```

2. **Параметры Docker Compose**:
   В проекте используется файл `docker-compose.yml` для настройки и запуска контейнеров для приложения и базы данных PostgreSQL.

3. **Подключение к базе данных**:
   Приложение использует контейнер с PostgreSQL, доступный через сервис `db`. Убедитесь, что в файле `.env` правильно настроены параметры подключения к базе данных:
   
   ```bash
   DATABASE_URL=postgresql://user:password@db/dbname
   SECRET_KEY=your_secret_key
   ```

4. **Остановка контейнеров**:
   Чтобы остановить контейнеры, используйте команду:

   ```bash
   docker-compose down
   ```

## Заключение

Этот проект представляет собой функциональное API для управления библиотечным каталогом. Все основные требования к функционалу выполнены, включая авторизацию, управление книгами, авторами и читателями, а также выдачу и возврат книг. Логирование, контейнеризация с Docker и юнит-тесты реализованы успешно.