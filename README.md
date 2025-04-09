# course-management-app-backend
Full-Stack Developer Technical Assessment Backend

## Run Docker Compose

```sh
docker-compose down
docker-compose up --build
```

## Run Migrations (in a separate terminal)

```sh
# In the NEW terminal
docker-compose exec web python manage.py makemigrations courses
docker-compose exec web python manage.py migrate
```

## Explore the API Documentation (Swagger)

Open your web browser and navigate to: `http://localhost:8000/swagger/`


## Check Django Admin

```bash
docker-compose exec web python manage.py createsuperuser
```
(Follow the prompts to create a username and password)

Go to `http://localhost:8000/admin/` in your browser

Log in with the superuser credentials.
