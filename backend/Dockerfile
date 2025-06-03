FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

# Создание директории для статических файлов
RUN mkdir -p /app/static

# Команда для запуска приложения с применением миграций, импорта данных и статических файлов
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py import_data && python manage.py collectstatic --noinput && gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120"]