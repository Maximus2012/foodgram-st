#  Foodgram – Recipe Sharing API

A backend service for managing and sharing recipes, subscribing to authors, adding favorites, and generating shopping lists.

---

##  Tech Stack
| **Category**        | **Technologies**                               |
|---------------------|------------------------------------------------|
| Backend             | Python 3.9, Django 3.2, Django REST Framework  |
| Authentication      | Djoser, Simple JWT                             |
| Database            | PostgreSQL                                     |
| Containerization    | Docker, Docker Compose                         |
| CI/CD               | GitHub Actions, Nginx                          |

---

##  Getting Started

###  Environment Variables
The project uses the following environment variables to configure database access:

```env
DEBUG=True of False
SECRET_KEY=<your_sercret_key>
DB_NAME=<your_database_name>
DB_USER=<your_username>
DB_PASSWORD=<your_password>
DB_HOST=<your_database_host>
DB_PORT=<your_database_port>
```

###  Running the Project with Docker

```bash
docker compose build
docker compose up
```

After the containers are running, the API will be available based on the settings in your `docker-compose.yml` and Nginx configuration.

After startup, the project will be available at:  
👉 [http://localhost:8000](http://localhost:8000)

###  4. Django Admin Panel
Accessible at:  
👉 [http://localhost:8000/admin](http://localhost:8000/admin)

---

###  Importing Initial Data
To load the initial ingredient data, run:
```bash
python manage.py import_data
```