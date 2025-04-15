#!/usr/bin/env python3

import requests
import os
import sys
import random
import json
import time  # Import time for a potential wait
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP  # For more precise price calculation

# --- Configuration ---
# BASE_URL = "http://localhost:8000"  # Old - Host perspective
BASE_URL = "http://web:8000"  # New - Docker network service name
INSTRUCTOR_USER = os.getenv(
    "POPULATE_INSTRUCTOR_USER", "instructor1"
)  # Use env var or default
INSTRUCTOR_PASS = os.getenv(
    "POPULATE_INSTRUCTOR_PASS", "ny990107"
)  # Use env var or default
# Use Pathlib for better path handling
# SCRIPT_DIR = Path(__file__).parent.resolve() # This is /app/scripts inside container
# --- MODIFIED ---
# IMAGE_PATH = SCRIPT_DIR / "test_assets" / "sample_course.png" # Old relative path logic
IMAGE_PATH = Path(
    "/app/test_assets/sample_course.png"
)  # Absolute path inside container
# -------------
NUM_COURSES = int(os.getenv("POPULATE_NUM_COURSES", 30))  # Use env var or default
MAX_RETRIES = 5  # Number of retries for initial connection
RETRY_DELAY = 3  # Seconds between retries

# --- Wait for backend to be ready ---
print(f"Waiting for backend service at {BASE_URL}...")
retries = 0
while retries < MAX_RETRIES:
    try:
        # Simple check: can we reach the base URL?
        response = requests.get(
            BASE_URL + "/api/token/", timeout=5
        )  # Check token endpoint
        # Check for a reasonable status code (e.g., 405 Method Not Allowed is ok here, just means endpoint exists)
        if response.status_code < 500:
            print("Backend appears to be running.")
            break
        else:
            print(f"Backend returned status {response.status_code}. Retrying...")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}. Retrying...")
    except requests.exceptions.Timeout:
        print("Connection timed out. Retrying...")
    except requests.exceptions.RequestException as e:
        print(f"An unexpected request error occurred: {e}. Retrying...")

    retries += 1
    if retries >= MAX_RETRIES:
        print("Error: Backend service did not become ready. Exiting.")
        sys.exit(1)
    time.sleep(RETRY_DELAY)


# --- Check if image file exists ---
if not IMAGE_PATH.is_file():
    print(f"Error: Image file not found at '{IMAGE_PATH}' inside the container.")
    print(
        "Please ensure the 'test_assets' directory was correctly copied in the Dockerfile."
    )
    sys.exit(1)

# --- Login and Get Token ---
print(f"Attempting to log in as instructor '{INSTRUCTOR_USER}'...")
login_url = f"{BASE_URL}/api/token/"
login_payload = {"username": INSTRUCTOR_USER, "password": INSTRUCTOR_PASS}
access_token = None

try:
    response = requests.post(login_url, json=login_payload, timeout=10)  # Added timeout
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

    try:
        login_data = response.json()
        access_token = login_data.get("access")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON response from login endpoint.")
        print(f"Response Text: {response.text}")
        sys.exit(1)

    if not access_token:
        print("Error: 'access' token not found in login response.")
        print(f"Response JSON: {login_data}")
        sys.exit(1)
    else:
        print("Login successful. Token obtained.")

except requests.exceptions.RequestException as e:
    print(f"Error during login request: {e}")
    print(f"Ensure the backend service ('web') is running and accessible at {BASE_URL}")
    print(
        f"Also, ensure the instructor user '{INSTRUCTOR_USER}' exists with the correct password."
    )
    sys.exit(1)
except Exception as e:  # Catch other potential errors during login
    print(f"An unexpected error occurred during login: {e}")
    sys.exit(1)


# --- Create Courses ---
print(f"Starting course creation loop ({NUM_COURSES} courses)...")
courses_url = f"{BASE_URL}/api/courses/"
auth_headers = {"Authorization": f"Bearer {access_token}"}
statuses = ["draft", "active", "inactive"]
base_price = Decimal("19.99")
price_increment = Decimal("2.50")
created_count = 0
failed_count = 0

for i in range(1, NUM_COURSES + 1):
    course_title = f"Sample Course {i}: Introduction to Topic {i}"
    course_desc = (
        f"This is a sample description for course number {i}. "
        f"It covers the fundamental concepts and provides practical examples for Topic {i}."
    )
    # Calculate price with Decimal for precision
    course_price = (base_price + (i - 1) * price_increment).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    random_status = random.choice(statuses)

    print(
        f"Creating Course {i}: '{course_title}' (Price: {course_price}, Status: {random_status})"
    )

    # Prepare data (form fields) and files for multipart/form-data upload
    course_data = {
        "title": course_title,
        "description": course_desc,
        "price": str(
            course_price
        ),  # Send price as string, backend should handle conversion
        "status": random_status,
    }

    try:
        # Open the file in binary read mode ('rb') for each request
        # Use the absolute path within the container
        with open(IMAGE_PATH, "rb") as image_file:
            files = {
                "image": (IMAGE_PATH.name, image_file, "image/png")
            }  # You might need to adjust mime type

            # Make the POST request with headers, data, and files
            response = requests.post(
                courses_url,
                headers=auth_headers,
                data=course_data,
                files=files,
                timeout=30,  # Longer timeout for file upload
            )

        # Check response status
        if response.status_code >= 200 and response.status_code < 300:
            print(
                f" - Course {i} creation request successful (Status: {response.status_code})."
            )
            created_count += 1
        else:
            print(
                f"Warning: Failed to create course {i}. Status: {response.status_code}"
            )
            failed_count += 1
            try:
                # Try to print error details from response if available (e.g., JSON error)
                error_details = response.json()
                print(f"   Error Details: {error_details}")
            except json.JSONDecodeError:
                # Otherwise print raw text
                print(f"   Response Text: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Error creating course {i}: {e}")
        failed_count += 1
    except FileNotFoundError:
        # Should have been caught earlier, but good practice
        print(f"Error: Image file '{IMAGE_PATH}' disappeared during script execution.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred creating course {i}: {e}")
        failed_count += 1

    # Optional: Add a small delay
    # import time
    # time.sleep(0.1)

print("-------------------------------------")
print(f"Finished. Created: {created_count}, Failed: {failed_count}")
print("-------------------------------------")

if failed_count > 0:
    sys.exit(1)  # Exit with error if any courses failed
else:
    sys.exit(0)  # Exit successfully
