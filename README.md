# course-management-app-backend

## Run Docker Compose

```sh
docker-compose down # Stop existing containers
docker-compose build --no-cache web # Rebuild 'web' service without cache
docker-compose up -d # Start services in detached mode
docker-compose logs -f web # Check logs
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

Example with this credentials:

```txt
Username: admin
Email: admin@example.com
Password: 1234567890
```

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


## Test the RBAC (Role-Based Access Control) using Swagger UI

Refer to `cma-plan` repository.

## Test API endpoints

- Use Swagger
- Use dedicated API testing software like Postman and Yakk
- Send `curl` request (Refer to `cma-plan` repository)


## Generate the ERD (Entity-Relationship Diagram) Image

```sh
docker-compose exec web python manage.py graph_models -a -o /app/erd.png
```

## View SQL Schema

### Step 1: Find Migration Numbers  
Look inside the `migrations` directory of each app to find the migration numbers you're interested in (e.g., `0001_initial.py`, `0003_...`).

### Step 2: Run `sqlmigrate`  
Execute the command inside the container, specifying the app label and the migration number:

```bash
# Example: SQL for the initial 'profiles' migration
docker-compose exec web python manage.py sqlmigrate profiles 0001

# Example: SQL for the course migration that added the instructor ForeignKey
docker-compose exec web python manage.py sqlmigrate courses 0003

# Example: SQL for the initial 'enrollments' migration
docker-compose exec web python manage.py sqlmigrate enrollments 0001

# Example: SQL for the initial 'quizzes' migration
docker-compose exec web python manage.py sqlmigrate quizzes 0001
```

This will print the PostgreSQL-specific SQL that Django generated for that migration.

## Viewing Full Schema (Database Tools)
To see the *complete* SQL schema for your tables *as they exist in the database after all migrations*, it's best to use a database client tool connected to your running PostgreSQL container (on `localhost:5435` with user `course_user`, password `course_password`, database `course_db` by default):

### Using `psql`:

```bash
# Connect to the database inside the db container
docker-compose exec db psql -U course_user -d course_db

# Inside psql, list tables:
\dt

# Describe a specific table (e.g., courses_course):
\d+ courses_course
\d+ profiles_profile
# etc.

# Exit psql
\q
```

### Using a GUI Tool:
Connect tools like DBeaver, pgAdmin, TablePlus, etc., to `localhost:5435` using the credentials. You can then easily browse the tables and their structures.

### Using `pg_dump` (Schema Only):

```bash
# Dump only the schema structure to a file on your host
docker-compose exec -T db pg_dump --schema-only -U course_user -d course_db > schema_dump.sql
```

This will create a `schema_dump.sql` file in your `cma-backend` directory containing the `CREATE TABLE` statements.

## Summary List of Frontend-Facing API Endpoints:

*   **Authentication & User:**
    *   `POST /api/token/`
        *   **Purpose:** Obtain JWT access and refresh tokens (Login).
        *   **Payload:** `{ "username": "...", "password": "..." }`
    *   `POST /api/token/refresh/`
        *   **Purpose:** Refresh an expired JWT access token using a valid refresh token.
        *   **Payload:** `{ "refresh": "..." }`
    *   `GET /api/users/me/`
        *   **Purpose:** Retrieve details of the currently authenticated user (including their profile).

*   **Courses:** (`/api/courses/`)
    *   `GET /api/courses/`
        *   **Purpose:** List all non-deleted courses. Supports filtering (`?status=active`, `?instructor_id=1`), searching (`?search=...`), and ordering (`?ordering=-price`).
    *   `POST /api/courses/`
        *   **Purpose:** Create a new course (Requires Instructor/Admin role).
        *   **Payload:** Course data (title, description, price, status, `instructor_id`). Handles optional `image` upload (multipart/form-data).
    *   `GET /api/courses/{pk}/`
        *   **Purpose:** Retrieve details of a specific non-deleted course.
    *   `PUT /api/courses/{pk}/`
        *   **Purpose:** Fully update a specific course (Requires Instructor/Admin role).
    *   `PATCH /api/courses/{pk}/`
        *   **Purpose:** Partially update a specific course (Requires Instructor/Admin role). Can send `image: null` to remove the image.
    *   `DELETE /api/courses/{pk}/`
        *   **Purpose:** Soft-delete a specific course (Requires Instructor/Admin role).
    *   `POST /api/courses/{pk}/restore/` (Custom Action)
        *   **Purpose:** Restore a soft-deleted course (Requires Instructor/Admin role).
    *   `GET /api/courses/deleted/` (Custom Action)
        *   **Purpose:** List only soft-deleted courses (Requires Instructor/Admin role).

*   **Enrollments:** (`/api/enrollments/`)
    *   `GET /api/enrollments/`
        *   **Purpose:** List enrollments. Returns enrollments for the requesting user, or all if the user is admin. Supports filtering (`?student_id=1`, `?course_id=1`, `?status=active`).
    *   `POST /api/enrollments/`
        *   **Purpose:** Create a new enrollment (Enroll a student in a course). Students can typically only enroll themselves.
        *   **Payload:** `{ "student_id": ..., "course_id": ... }`
    *   `GET /api/enrollments/{pk}/`
        *   **Purpose:** Retrieve details of a specific enrollment (Requires owner or admin).
    *   `PUT /api/enrollments/{pk}/`
        *   **Purpose:** Fully update a specific enrollment (e.g., change status) (Requires owner or admin).
    *   `PATCH /api/enrollments/{pk}/`
        *   **Purpose:** Partially update a specific enrollment (Requires owner or admin).
    *   `DELETE /api/enrollments/{pk}/`
        *   **Purpose:** Soft-delete a specific enrollment (Unenroll) (Requires owner or admin).

*   **Quizzes:** (`/api/quizzes/`)
    *   `GET /api/quizzes/`
        *   **Purpose:** List all quizzes. Might need filtering by course (`?course_id=...`).
    *   `POST /api/quizzes/`
        *   **Purpose:** Create a new quiz for a course (Requires Instructor/Admin role).
        *   **Payload:** Quiz data (title, description, time\_limit\_minutes, `course_id`).
    *   `GET /api/quizzes/{pk}/`
        *   **Purpose:** Retrieve details of a specific quiz (including its questions and choices).
    *   `PUT /api/quizzes/{pk}/`
        *   **Purpose:** Fully update a specific quiz (Requires Instructor/Admin role).
    *   `PATCH /api/quizzes/{pk}/`
        *   **Purpose:** Partially update a specific quiz (Requires Instructor/Admin role).
    *   `DELETE /api/quizzes/{pk}/`
        *   **Purpose:** Delete a specific quiz (Requires Instructor/Admin role).
    *   `POST /api/quizzes/{pk}/start-submission/` (Custom Action)
        *   **Purpose:** Start a new quiz attempt (submission) for the authenticated user. Returns the new or existing "in_progress" submission.

*   **Quiz Questions:** (`/api/questions/`) *(Note: Often better handled via nested routes like `/api/quizzes/{quiz_pk}/questions/`)*
    *   `GET /api/questions/`
        *   **Purpose:** List all questions (Needs filtering, e.g., `?quiz_id=...`).
    *   `POST /api/questions/`
        *   **Purpose:** Create a new question for a specific quiz (Requires Instructor/Admin role).
        *   **Payload:** Question data (text, question\_type, order, `quiz_id`).
    *   `GET /api/questions/{pk}/`
        *   **Purpose:** Retrieve details of a specific question.
    *   `PUT /api/questions/{pk}/`
        *   **Purpose:** Fully update a specific question (Requires Instructor/Admin role).
    *   `PATCH /api/questions/{pk}/`
        *   **Purpose:** Partially update a specific question (Requires Instructor/Admin role).
    *   `DELETE /api/questions/{pk}/`
        *   **Purpose:** Delete a specific question (Requires Instructor/Admin role).

*   **Quiz Choices:** (`/api/choices/`) *(Note: Often better handled via nested routes like `/api/quizzes/{quiz_pk}/questions/{question_pk}/choices/`)*
    *   `GET /api/choices/`
        *   **Purpose:** List all choices (Needs filtering, e.g., `?question_id=...`).
    *   `POST /api/choices/`
        *   **Purpose:** Create a new choice for a specific question (Requires Instructor/Admin role).
        *   **Payload:** Choice data (text, is\_correct, `question_id`).
    *   `GET /api/choices/{pk}/`
        *   **Purpose:** Retrieve details of a specific choice.
    *   `PUT /api/choices/{pk}/`
        *   **Purpose:** Fully update a specific choice (Requires Instructor/Admin role).
    *   `PATCH /api/choices/{pk}/`
        *   **Purpose:** Partially update a specific choice (Requires Instructor/Admin role).
    *   `DELETE /api/choices/{pk}/`
        *   **Purpose:** Delete a specific choice (Requires Instructor/Admin role).

*   **Quiz Submissions:** (`/api/submissions/`)
    *   `GET /api/submissions/`
        *   **Purpose:** List submissions (filtered based on user role: own for student, related for instructor, all for admin). Supports filtering (`?student_id=`, `?quiz_id=`, `?status=`).
    *   `GET /api/submissions/{pk}/`
        *   **Purpose:** Retrieve details of a specific submission (including answers) (Requires owner, instructor, or admin).
    *   `POST /api/submissions/{pk}/submit-answer/` (Custom Action)
        *   **Purpose:** Submit or update an answer for a question within an "in_progress" submission (Requires owner).
        *   **Payload:** `{ "question_id": ..., "selected_choice_id": ... }` OR `{ "question_id": ..., "text_answer": "..." }`
    *   `POST /api/submissions/{pk}/finalize/` (Custom Action)
        *   **Purpose:** Mark an "in_progress" submission as finished and trigger grading (Requires owner).
    *   *(Note: Direct POST/PUT/PATCH/DELETE on `/api/submissions/` are likely disabled by the ViewSet)*

*   **Media Files:**
    *   `GET /media/...`
        *   **Purpose:** Base URL path for accessing user-uploaded files (like course images). The frontend needs to prepend the domain (e.g., `http://localhost:8000`) to the relative paths returned by the API (e.g., `/media/course_images/my_image.jpg`).

