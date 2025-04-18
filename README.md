# Course Management App Backend (MVP)

<p align="center">
  <img src="./assets/cma.png" alt="ChatGPT Reverse Logo" width="600"/>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/></a>
  <a href="https://semver.org"><img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version"/></a>
</p>


This is the backend service for the Course Management Application (MVP version), built with Django and Django REST Framework. It provides APIs for managing users (Admin, Instructor, User), courses, and enrollments according to defined roles and permissions.

## Features (MVP)

*   **User Roles:** Admin, Instructor, User.
*   **Authentication:** JWT-based login (`/api/token/`), token refresh (`/api/token/refresh/`).
*   **Registration:** Users can register as 'Instructor' or 'User' (`/api/register/`).
*   **Course Management:**
    *   Instructors: Create, View Own, Edit Own, Delete Own Courses.
    *   Users/Instructors/Admins: Browse/View All Courses.
    *   Admins: Delete Any Course.
*   **Enrollment Management:**
    *   Users: Enroll in Courses, View Own Enrollments, Unenroll (Delete Enrollment).
    *   Admins: View All Enrollments.
*   **Admin User Management:**
    *   Admins: View All Users, Delete Any User (excluding superusers).

## Prerequisites

*   Docker
*   Docker Compose

## Project Setup & Running

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Create Environment File:**
    Create a `.env` file in the project root directory (where `docker-compose.yml` is located) with the following content (adjust values if needed, especially `SECRET_KEY` for production):

    ```dotenv
    # backend/.env

    # Django Settings
    SECRET_KEY='django-insecure-=your-very-secret-key-replace-me!*&' # CHANGE THIS!
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1

    # Database Settings (for Docker Compose service named 'db')
    DATABASE_URL=postgres://course_user:course_password@db:5432/course_db

    # Other Settings (if needed)
    # EMAIL_HOST_USER=...
    ```
    **Important:** For production, set `DEBUG=False`, generate a strong `SECRET_KEY`, and list your actual domain(s) in `ALLOWED_HOSTS`.

    Or you can rename filename from `example.env` to `.env` at the root project.

3.  **Build and Start Services:**
    Use Docker Compose to build the image and start the database (`db`) and web application (`web`) containers.

    ```sh
    # Stop any potentially running containers from previous runs
    docker-compose down

    # Build the 'web' service image (use --no-cache if you need a clean build)
    docker-compose build web

    # Start all services in detached mode (-d)
    docker-compose up -d
    ```

4.  **Check Logs (Optional):**
    Monitor the logs of the web service to ensure it started correctly.
    ```sh
    docker-compose logs -f web
    ```
    Press `Ctrl+C` to stop following the logs. You should see messages indicating the development server is running on `http://0.0.0.0:8000/`.

## Database Migrations

After the containers are running, apply the database migrations. Run these commands in a **separate terminal** window while the containers are up.

```sh
docker-compose exec web python manage.py makemigrations profiles
docker-compose exec web python manage.py makemigrations courses
docker-compose exec web python manage.py makemigrations enrollments

# Apply the migrations (this command is usually fine without app labels)
docker-compose exec web python manage.py migrate
```

## Create Superuser (Admin Account)

Create an initial administrative user to access the Django admin interface and perform admin actions via the API.

```bash
# Execute the createsuperuser command inside the 'web' container
docker-compose exec web python manage.py createsuperuser
```

Follow the prompts. Example credentials:

*   Username: `admin`
*   Email: `admin@example.com`
*   Password: `yoursecurepassword` (choose a strong one)

You can bypass password validation if needed during development by answering 'y'.


## Create Instructor

Go to `http://localhost:8000/swagger/`.

Register new instructor with this information, then wait for response code `201`.

```txt
{
  "username": "instructor1",
  "email": "instructor1@example.com",
  "password": "aabc@123a",
  "password2": "aabc@123a",
  "first_name": "instructor",
  "last_name": "1",
  "role": "instructor"
}
```

## Create Student

Go to `http://localhost:8000/swagger/`.

Register new student with this information, then wait for response code `201`.

```txt
{
  "username": "student1",
  "email": "student1@example.com",
  "password": "aabc@123a",
  "password2": "aabc@123a",
  "first_name": "student",
  "last_name": "1",
  "role": "student"
}
```

## Populate Database

Run this script at the root project, only after you create `instructor1`:

```sh
pip install requests
python scripts/create_courses.py
```

## Accessing the Application & API

*   **Django Admin:** `http://localhost:8000/admin/` (Log in with the superuser credentials)
*   **API Documentation (Swagger UI):** `http://localhost:8000/swagger/`
*   **API Documentation (ReDoc):** `http://localhost:8000/redoc/`

## API Endpoints (MVP Summary)

Use an API client like Postman, Insomnia, or `curl` to interact with these endpoints. Remember to authenticate by first obtaining a token from `/api/token/` and including it in the `Authorization: Bearer <your_access_token>` header for protected endpoints.

*   **Authentication & Users:**
    *   `POST /api/token/`
        *   **Purpose:** Login - Obtain JWT access and refresh tokens.
        *   **Payload:** `{ "username": "...", "password": "..." }`
        *   **Access:** Public
    *   `POST /api/token/refresh/`
        *   **Purpose:** Refresh JWT access token.
        *   **Payload:** `{ "refresh": "..." }`
        *   **Access:** Public (Requires valid refresh token)
    *   `POST /api/register/`
        *   **Purpose:** Register a new User or Instructor.
        *   **Payload:** `{ "username": "...", "email": "...", "password": "...", "password2": "...", "role": "student" | "instructor", "first_name": "(optional)", "last_name": "(optional)" }`
        *   **Access:** Public
    *   `GET /api/users/me/` (Optional - Keep if frontend needs it)
        *   **Purpose:** Retrieve details of the currently authenticated user.
        *   **Access:** Any Authenticated User
    *   `GET /api/admin/users/`
        *   **Purpose:** List all users (User & Instructor).
        *   **Access:** Admin Only
    *   `DELETE /api/admin/users/{pk}/`
        *   **Purpose:** Delete a specific user.
        *   **Access:** Admin Only (Cannot delete superusers)

*   **Courses:** (`/api/courses/`)
    *   `GET /api/courses/`
        *   **Purpose:** List all available (non-deleted) courses. Supports filtering, searching, ordering.
        *   **Access:** Any Authenticated User
    *   `POST /api/courses/`
        *   **Purpose:** Create a new course. Instructor is set automatically.
        *   **Payload:** `{ "title": "...", "description": "...", "price": "...", "status": "(optional, default 'draft')", "image": "(optional file upload)" }`
        *   **Access:** Instructor Only
    *   `GET /api/courses/{pk}/`
        *   **Purpose:** Retrieve details of a specific course.
        *   **Access:** Any Authenticated User
    *   `PUT /api/courses/{pk}/`
        *   **Purpose:** Fully update a specific course.
        *   **Access:** Owner Instructor or Admin Only
    *   `PATCH /api/courses/{pk}/`
        *   **Purpose:** Partially update a specific course. Admin can change `instructor_id`. Can send `image: null` to remove image.
        *   **Access:** Owner Instructor or Admin Only
    *   `DELETE /api/courses/{pk}/`
        *   **Purpose:** Soft-delete a specific course.
        *   **Access:** Owner Instructor or Admin Only
    *   `POST /api/courses/{pk}/restore/` (Custom Action)
        *   **Purpose:** Restore a soft-deleted course.
        *   **Access:** Admin Only
    *   `GET /api/courses/deleted/` (Custom Action)
        *   **Purpose:** List soft-deleted courses.
        *   **Access:** Admin Only

*   **Enrollments:** (`/api/enrollments/`)
    *   `GET /api/enrollments/`
        *   **Purpose:** List enrollments. Returns own enrollments for Users, or all for Admins. Supports filtering.
        *   **Access:** Authenticated Users (filtered), Admin (all)
    *   `POST /api/enrollments/`
        *   **Purpose:** Enroll the current user in a course.
        *   **Payload:** `{ "course_id": ... }`
        *   **Access:** User Only (Instructors cannot enroll)
    *   `GET /api/enrollments/{pk}/`
        *   **Purpose:** Retrieve details of a specific enrollment.
        *   **Access:** Owner User or Admin Only
    *   `DELETE /api/enrollments/{pk}/`
        *   **Purpose:** Unenroll (soft-delete) from a course.
        *   **Access:** Owner User or Admin Only
    *   *(Note: PUT/PATCH on enrollments are disabled for MVP)*

*   **Media Files:**
    *   `GET /media/...`
        *   **Purpose:** Base URL path for accessing user-uploaded files (like course images). The frontend needs to prepend the domain (e.g., `http://localhost:8000`) to the relative paths returned by the API (e.g., `/media/course_images/my_image.jpg`).

## Running Tests

Execute the test suite within the `web` container. Replace `apps.courses` with the specific app you want to test, or run tests for all apps.

```sh
# Example: Run tests for the 'courses' app
docker-compose exec web python manage.py test apps.courses

# Example: Run tests for the 'enrollments' app
docker-compose exec web python manage.py test apps.enrollments

# Example: Run tests for the 'users' app (if tests exist)
docker-compose exec web python manage.py test apps.users

# Run tests for ALL apps (might take longer)
docker-compose exec web python manage.py test
```

## Generating ERD (Entity-Relationship Diagram)

If you have `django-extensions` and `graphviz` installed (as per the Dockerfile), you can generate an ERD image of your models.

```sh
# Generate the diagram for all apps (-a) and output to erd.png inside the container's /app directory
docker-compose exec web python manage.py graph_models -a -o /app/erd.png
```
You might need to copy this file from the container to your host or adjust the output path if needed.

## Viewing Database Schema

### View SQL for Specific Migrations

See the SQL Django generated for a particular migration:

```bash
# Example: SQL for the initial 'profiles' migration
docker-compose exec web python manage.py sqlmigrate profiles 0001

# Example: SQL for the course migration that added the instructor ForeignKey
docker-compose exec web python manage.py sqlmigrate courses 0003

# Example: SQL for the initial 'enrollments' migration
docker-compose exec web python manage.py sqlmigrate enrollments 0001
```

### View Live Schema (using psql)

Connect directly to the running PostgreSQL database container:

```bash
# Connect to the database inside the db container
docker-compose exec db psql -U course_user -d course_db

# Inside psql:
\dt # List tables
\d+ apps_courses_course # Describe the course table (prefix with app name)
\d+ apps_enrollments_enrollment # Describe the enrollment table
\d+ apps_profiles_profile # Describe the profile table
\q # Exit psql
```

### View Live Schema (GUI Tool)

Connect your preferred database GUI tool (DBeaver, pgAdmin, TablePlus, etc.) to the database:

*   **Host:** `localhost`
*   **Port:** `5435` (as mapped in `docker-compose.yml`)
*   **Database:** `course_db` (or your value from `.env`)
*   **User:** `course_user` (or your value from `.env`)
*   **Password:** `course_password` (or your value from `.env`)

### Dump Schema Structure

Create a SQL file containing the `CREATE TABLE` statements for the current schema:

```bash
# Dump only the schema structure to a file named schema_dump.sql in your project root
docker-compose exec -T db pg_dump --schema-only -U course_user -d course_db > schema_dump.sql
```

## Clean Persistent

```sh
# Stop and remove containers and network
docker-compose down

# Remove the custom built image
docker image rm cma-backend-web
```

## Clean All Active Docker Images (Warning)

1. **Stop all running containers**:
   ```bash
   docker stop $(docker ps -q)
   ```

2. **Remove all containers**:
   ```bash
   docker rm $(docker ps -aq)
   ```

3. **Now remove all images**:
   ```bash
   docker rmi $(docker images -q)
   ```

## Clean All Active/Inactive Docker Images (Warning)

```bash
docker system prune -a --volumes
```

- This will remove **all**:
  - stopped containers
  - unused networks
  - dangling images
  - unused volumes

> ⚠️ Be careful with this. It will free up a lot of space but also delete **everything not in use**.
