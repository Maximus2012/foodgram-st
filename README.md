## **Технологии, используемые в проекте**
- **БД**: PostgreSQL  
- **Серверная часть**: Django 3.2.16 + DRF 3.12.4  
- **Авторизация**: JWT через Djoser 2.3.1  
- **Инфраструктура**: Docker + Docker Compose, Gunicorn, Nginx  
- **CI/CD**: GitHub Actions + публикация в Docker Hub  

---

## **Как развернуть проект локально**

###  1. Клонирование репозитория
```bash
git clone https://github.com/Maximus2012/foodgram-st.git
```

###  2. Настройка переменных окружения
Создайте файл `.env` в корне проекта и добавьте туда следующее:

```ini
DEBUG=True of False
SECRET_KEY=секретный_ключ
DB_NAME=имя_бд
DB_USER=пользователь_бд
DB_PASSWORD=пароль_бд
DB_HOST=db
DB_PORT=порт_бд
DOCKER_USERNAME=ваш_логин_на_docker_hub
```

###  3. Сборка и запуск контейнеров
```bash
docker-compose up -d --build
```
После старта проект будет доступен по адресу:  
👉 [http://localhost:80](http://localhost:80)

###  4. Панель администратора Django
Доступна по адресу:  
👉 [http://localhost:8000/admin](http://localhost:8000/admin)

---

###  Импорт начальных данных
Для загрузки данных ингредиентов выполните:
```bash
python manage.py import_data
```