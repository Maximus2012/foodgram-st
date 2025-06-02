# 🍲 Foodgram – Recipe Sharing API

A backend service for managing and sharing recipes, subscribing to authors, adding favorites, and generating shopping lists.

---

## Tech Stack

| **Category**        | **Technologies**                               |
|---------------------|------------------------------------------------|
| Backend             | Python 3.9, Django 3.2, Django REST Framework  |
| Authentication      | Djoser, Simple JWT                             |
| Database            | PostgreSQL                                     |
| Containerization    | Docker, Docker Compose                         |
| CI/CD               | GitHub Actions, Nginx                          |

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Maximus2012/foodgram-st.git
cd foodgram-st/infra
```

---

### 2. Setup Environment Variables

Create a `.env` file at:

```
foodgram-st/backend/.env
```

Example content:

```env
DEBUG=False
SECRET_KEY=your-django-secret-key

DB_NAME=foodgram
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=127.0.0.1,localhost,example.com
```

---

### 3. Run with Docker

```bash
docker compose build
docker compose up
```

After startup, the project will be available at:  
👉 [http://127.0.0.1](http://127.0.0.1)

Django Admin Panel
Accessible at:  
👉 [http://localhost/admin/](http://localhost/admin/)


---

### 4. Run API Locally (Without Docker)

1. Go to the `backend` folder:

```bash
cd ../backend
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate it:

- **Windows**:

```bash
venv\Scripts\activate
```

- **macOS/Linux**:

```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Load initial ingredient data:

```bash
python manage.py import_data
```

6. Run the server:

```bash
python manage.py runserver
```

After startup, the project will be available at:  
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Project Structure

```
foodgram-st/
├── backend/ Django project
├── frontend/                 # Optional React app
├── infra/
│   ├── docker-compose.yml    # Docker Compose config
│   └── nginx.conf            # Nginx config
├── data/                     # Initial ingredients
└── docs/                     # API documentation
```

---

## Author

**Max Kochetkov**  
[GitHub Profile](https://github.com/Maximus2012)