#!/bin/bash

# --- Configuration ---
BASE_URL="http://localhost:8000" # Adjust if your backend runs elsewhere
INSTRUCTOR_USER="instructor1" # CHANGE if you used a different username
INSTRUCTOR_PASS="ny990107"    # CHANGE if you used a different password
IMAGE_PATH="test_assets/sample_course.png" # Relative path from script location
NUM_COURSES=30

# --- Check if image file exists ---
if [ ! -f "$IMAGE_PATH" ]; then
  echo "Error: Image file not found at '$IMAGE_PATH'."
  echo "Please ensure the image exists and the path is correct relative to the script."
  exit 1
fi

# --- Login and Get Token ---
echo "Attempting to log in as instructor '$INSTRUCTOR_USER'..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/token/" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$INSTRUCTOR_USER\", \"password\": \"$INSTRUCTOR_PASS\"}")

# Extract access token using jq
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access')

# Check if token extraction was successful
if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
  echo "Error: Failed to get access token. Check credentials and backend status."
  echo "Response: $LOGIN_RESPONSE"
  exit 1
else
  echo "Login successful. Token obtained."
fi

# --- Create Courses ---
echo "Starting course creation loop ($NUM_COURSES courses)..."

for i in $(seq 1 $NUM_COURSES)
do
  COURSE_TITLE="Sample Course ${i}: Introduction to Topic ${i}"
  COURSE_DESC="This is a sample description for course number ${i}. It covers the fundamental concepts and provides practical examples for Topic ${i}."
  # Generate a slightly varying price (e.g., starting at 19.99, increasing by 2.50 each time)
  COURSE_PRICE=$(echo "scale=2; 19.99 + ($i - 1) * 2.50" | bc)
  # Randomly assign status (optional)
  STATUSES=("draft" "active" "inactive")
  RANDOM_STATUS=${STATUSES[$RANDOM % ${#STATUSES[@]}]}

  echo "Creating Course $i: '$COURSE_TITLE' (Price: $COURSE_PRICE, Status: $RANDOM_STATUS)"

  curl -s -X POST "${BASE_URL}/api/courses/" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -F "title=${COURSE_TITLE}" \
    -F "description=${COURSE_DESC}" \
    -F "price=${COURSE_PRICE}" \
    -F "status=${RANDOM_STATUS}" \
    -F "image=@${IMAGE_PATH}" # Use @ prefix for file upload

  # Check curl exit status (optional but good practice)
  if [ $? -ne 0 ]; then
      echo "Warning: curl command failed for course $i"
  fi

  echo " - Course $i creation request sent."
  # Optional: Add a small delay to avoid hammering the server
  # sleep 0.1
done

echo "-------------------------------------"
echo "Finished creating $NUM_COURSES courses."
echo "-------------------------------------"

exit 0