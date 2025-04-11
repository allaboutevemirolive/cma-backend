# course-management-app-backend

## Run Docker Compose

```sh
docker-compose down # Stop existing containers
docker-compose build --no-cache web # Rebuild 'web' service without cache
docker-compose up -d # Start services in detached mode
```

## Check Logs

```sh
docker-compose logs -f web
```

## Run Migrations (in a separate terminal)

```sh
# In the NEW terminal
docker-compose exec web python manage.py makemigrations courses
docker-compose exec web python manage.py migrate
```

## Run Test

```sh
docker-compose exec web python manage.py test apps.courses
```

## Explore the API Documentation (Swagger)

Open your web browser and navigate to: `http://localhost:8000/swagger/`


## Initalize Django Admin

```bash
docker-compose exec web python manage.py createsuperuser
```

Example:

- Username: admin
- Email: admin@example.com
- Password: 1234567890

```sh
$ docker-compose exec web python manage.py createsuperuser
Username (leave blank to use 'root'): admin
Email address: admin@example.com
Password:
Password (again):
This password is too common.
This password is entirely numeric.
Bypass password validation and create user anyway? [y/N]: y
Superuser created successfully.
```

Go to `http://localhost:8000/admin/` in your browser and log in with the superuser credentials.


## Test the Role-Based Access Control (RBAC) using Swagger UI

Refer to `cma-plan` repository.

## Test API endpoints

- Use Swagger
- Use dedicated API testing software like Postman and Yakk
- Send `curl` request (Refer to `cma-plan` repository)
