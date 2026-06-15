## Контекстный Генератор Примеров

Сервис помогает изучающим английский язык находить контекстные примеры употребления слов и фраз в реальной речи. Пользователь получает определения с разбором по частям речи, живые примеры из словарей и параллельных корпусов, а также их автоматический перевод на русский язык.

**Ссылка на рабочий проект:** [https://ваш-логин.pythonanywhere.com](https://ваш-логин.pythonanywhere.com)

### Технологии
- **Python 3.10**
- **Django 4.2**
- **Requests** — для работы с внешними API
- **BeautifulSoup** — для парсинга Linguee
- **PyMultiDictionary** — для получения определений
- **Gunicorn** — для деплоя на PythonAnywhere

### Скриншоты
- [Главная страница (светлая тема)](screenshots/main_light.png)
- [Результат поиска с примерами](screenshots/search_result.png)
- [Главная страница (тёмная тема)](screenshots/dark_theme.png)

### График/Аналитика
- [Диаграмма источников примеров](screenshots/sources_chart.png)
- [Статистика запросов по дням](screenshots/requests_stats.png)

## Как запустить проект локально
1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/ваш-юзернейм/context_generator.git
   cd context_generator
   ```
2. **Создайте и активируйте виртуальное окружение:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # для Linux/Mac
   venv\Scripts\activate    # для Windows
   ```
3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Настройте переменные окружения:**
   ```bash
   SECRET_KEY=ваш-секретный-ключ
   YANDEX_API_KEY=ваш-ключ-yandex-api
   DEBUG=True
   ```
5. **выполните миграции:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
6. **Загрузите изначальные данные:**
    ```bash
   python manage.py loaddata initial_data
   ```
7. **Создайте суперпользователя:**
    ```bash
   python manage.py loaddata initial_data
   ```
8. **Запустите сервер:**
   ```bash
   python manage.py runserver
   ```
9. **Откройте проект в браузере:**
   Перейдите по ссылке: http://127.0.0.1:8000/