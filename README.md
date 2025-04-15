# Course Management App Backend (MVP)

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

## Initial Setup Commands (After `docker-compose up -d`)

Once the containers are running, execute these commands in order from your project root in a separate terminal:

1.  **Apply Database Migrations:**
    ```bash
    docker-compose exec web python manage.py migrate
    ```

2.  **Create Initial Users (Optional but Recommended):**
    This script creates a default superuser, instructor, and student. It's idempotent (safe to run multiple times). Credentials can be configured via environment variables (see script comments).

    By default we will have this credentials:
    
    ```txt
    Username: admin
    Email: admin@example.com
    Password: aabc@123a

    Username: instructro1
    Email: instructor1@example.com
    Password: aabc@123a

    Username: student1
    Email: student1@example.com
    Password: aabc@123a
    ```
    
    ```bash
    # Example using default credentials (admin/adminpass, instructor1/instrpass, student1/studpass)
    docker-compose exec web python /app/scripts/create_initial_users.py

    # Example setting environment variables (Bash/Zsh) - only affects this one command
    # docker-compose exec \
    #   -e DJANGO_SUPERUSER_PASSWORD=supersecret \
    #   -e DEFAULT_INSTRUCTOR_PASSWORD=instrsecret \
    #   -e DEFAULT_STUDENT_PASSWORD=studsecret \
    #   web python /app/scripts/create_initial_users.py
    ```
    *   Default Superuser: `admin` / `adminpass`
    *   Default Instructor: `instructor1` / `instrpass`
    *   Default Student: `student1` / `studpass`
    *(Remember to change these default passwords if using in a non-development context!)*

3.  **Populate Sample Courses (Optional):**
    Requires the instructor user created in the previous step (or another existing instructor).
    ```bash
    # Using the default instructor1 user created by the previous script
    docker-compose exec web python /app/scripts/populate_courses.py

    # If you used a different instructor username/password:
    # docker-compose exec \
    #   -e POPULATE_INSTRUCTOR_USER=your_instructor_username \
    #   -e POPULATE_INSTRUCTOR_PASS=your_instructor_password \
    #   web python /app/scripts/populate_courses.py
    ```

## Create Superuser (Manual Alternative)

If you prefer not to use the `create_initial_users.py` script, you can create an administrative user manually:
```bash
docker-compose exec web python manage.py createsuperuser
```
Follow the prompts. Example credentials:
*   Username: `admin`
*   Email: `admin@example.com`
*   Password: `yoursecurepassword` (choose a strong one)

You will then need to create instructor/student users via the API or Django admin if you want to use the `populate_courses.py` script or test different roles.

## Populating Sample Data

This project includes a Python script to populate the database with sample courses using the API.

**Prerequisites:**

1.  The application containers must be running (`docker-compose up -d`).
2.  An instructor user must exist in the database. You can create one using the registration API (`POST /api/register/` with role="instructor") or via the Django admin interface after creating a superuser. By default, the script uses `instructor1` / `ny990107`.

**Running the Script:**

1.  **(Optional) Set Environment Variables:** You can override the default instructor credentials and number of courses by setting environment variables before running the command:
    ```bash
    export POPULATE_INSTRUCTOR_USER=your_instructor_username
    export POPULATE_INSTRUCTOR_PASS=your_instructor_password
    export POPULATE_NUM_COURSES=50
    ```

2.  **Rebuild the Image (if you changed `Dockerfile` or `requirements.txt`):**
    ```bash
    docker-compose build web
    ```

3.  **Execute the script:** Run the following command from the directory containing `docker-compose.yml`:
    ```bash
    docker-compose exec web python /app/scripts/populate_courses.py
    ```
    *(Note: If you set environment variables, they need to be passed to the `exec` command if they aren't already part of the container's environment. Simpler is often to modify the script defaults or rely on the `.env` file if you integrate it there.)*

    The script will attempt to log in as the instructor, and then create the specified number of courses, uploading the sample image for each. It includes a short wait at the beginning to allow the web service to fully initialize.

**Troubleshooting:**

*   **Connection Errors:** Ensure `docker-compose up -d` is running and the `web` service started successfully (`docker-compose logs web`). Check the `BASE_URL` in the script points to `http://web:8000`.
*   **Login Failed (401/400):** Verify the instructor username and password are correct and the user exists in the database. Check the script's `INSTRUCTOR_USER`/`INSTRUCTOR_PASS` or the environment variables.
*   **Image Not Found:** Ensure `COPY ./test_assets /app/test_assets` is in the `Dockerfile` and the image was rebuilt. Check the `IMAGE_PATH` in the script points to `/app/test_assets/sample_course.png`.
*   **Permission Denied (403 on Course Creation):** Ensure the user specified (`instructor1` by default) actually has the `instructor` role assigned via their profile.

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

## Stopping the Application

```sh
# Stop and remove the containers, network, and volumes defined in docker-compose.yml
docker-compose down

# To stop without removing volumes (useful for preserving DB data):
# docker-compose stop
```


## Clean Persistent

```sh
# Stop and remove containers and network
docker-compose down

# Remove the custom built image
docker image rm cma-backend-web
```
