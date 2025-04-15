#!/usr/bin/env python3

import requests
import os
import sys
import random
import json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP # For more precise price calculation

# --- Configuration ---
BASE_URL = "http://localhost:8000"  # Adjust if your backend runs elsewhere
INSTRUCTOR_USER = "instructor1"   # CHANGE if you used a different username
INSTRUCTOR_PASS = "aabc@123a"      # CHANGE if you used a different password
NUM_COURSES = 30

# --- Calculate Paths ---
# Use Pathlib for better path handling
# Get the directory containing the script (e.g., /path/to/project/scripts)
SCRIPT_DIR = Path(__file__).parent.resolve()
# Get the parent directory (the project root, e.g., /path/to/project)
PROJECT_ROOT = SCRIPT_DIR.parent
# Construct the image path relative to the project root
IMAGE_PATH = PROJECT_ROOT / "test_assets" / "sample_course.png"

# --- Check if image file exists ---
if not IMAGE_PATH.is_file():
    print(f"Error: Image file not found at '{IMAGE_PATH}'.")
    print("Please ensure the image exists and the path is correct relative to the script's parent directory.")
    sys.exit(1)

# --- Login and Get Token ---
print(f"Attempting to log in as instructor '{INSTRUCTOR_USER}'...")
login_url = f"{BASE_URL}/api/token/"
login_payload = {
    "username": INSTRUCTOR_USER,
    "password": INSTRUCTOR_PASS
}
access_token = None

try:
    response = requests.post(login_url, json=login_payload, timeout=10) # Added timeout
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

    try:
        login_data = response.json()
        access_token = login_data.get('access')
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
    sys.exit(1)
except Exception as e: # Catch other potential errors during login
    print(f"An unexpected error occurred during login: {e}")
    sys.exit(1)


# --- Create Courses ---
print(f"Starting course creation loop ({NUM_COURSES} courses)...")
courses_url = f"{BASE_URL}/api/courses/"
auth_headers = {"Authorization": f"Bearer {access_token}"}
statuses = ["draft", "active", "inactive"]
base_price = Decimal("19.99")
price_increment = Decimal("2.50")

for i in range(1, NUM_COURSES + 1):
    course_title = f"Sample Course {i}: Introduction to Topic {i}"
    course_desc = (
        f"This is a sample description for course number {i}. "
        f"It covers the fundamental concepts and provides practical examples for Topic {i}."
    )
    # Calculate price with Decimal for precision
    course_price = (base_price + (i - 1) * price_increment).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    random_status = random.choice(statuses)

    print(f"Creating Course {i}: '{course_title}' (Price: {course_price}, Status: {random_status})")

    # Prepare data (form fields) and files for multipart/form-data upload
    course_data = {
        "title": course_title,
        "description": course_desc,
        "price": str(course_price), # Send price as string, backend should handle conversion
        "status": random_status,
    }

    try:
        # Open the file in binary read mode ('rb') for each request
        # IMAGE_PATH now correctly points to the file outside the 'scripts' dir
        with open(IMAGE_PATH, 'rb') as image_file:
            # Use IMAGE_PATH.name to get just the filename for the upload metadata
            files = {'image': (IMAGE_PATH.name, image_file, 'image/png')} # You might need to adjust mime type

            # Make the POST request with headers, data, and files
            response = requests.post(
                courses_url,
                headers=auth_headers,
                data=course_data,
                files=files,
                timeout=30 # Longer timeout for file upload
            )

        # Check response status
        if response.status_code >= 200 and response.status_code < 300:
             print(f" - Course {i} creation request successful (Status: {response.status_code}).")
        else:
             print(f"Warning: Failed to create course {i}. Status: {response.status_code}")
             try:
                 # Try to print error details from response if available (e.g., JSON error)
                 error_details = response.json()
                 print(f"   Error Details: {error_details}")
             except json.JSONDecodeError:
                 # Otherwise print raw text
                 print(f"   Response Text: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Error creating course {i}: {e}")
    except FileNotFoundError:
        # This check uses the calculated IMAGE_PATH
        print(f"Error: Image file '{IMAGE_PATH}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred creating course {i}: {e}")

    # Optional: Add a small delay
    # import time
    # time.sleep(0.1)

print("-------------------------------------")
print(f"Finished creating {NUM_COURSES} courses.")
print("-------------------------------------")

sys.exit(0)
