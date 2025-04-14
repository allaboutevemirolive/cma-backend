#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
BASE_URL="http://localhost:8000" # Adjust if your backend runs elsewhere
# Use the same user who created the courses OR an admin user if you want to delete ANY course
DELETER_USER="instructor1"       # CHANGE if needed (e.g., to 'admin')
DELETER_PASS="ny990107"          # CHANGE if needed
# Set a large page size to try and get all courses in one go
# Adjust if you expect > 1000 courses managed by this user or if deleting as admin
PAGE_SIZE_LIMIT=1000

# --- Check for dependencies ---
if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed. Please install it (e.g., sudo apt install curl)."
    exit 1
fi
if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed. Please install it (e.g., sudo apt install jq)."
    exit 1
fi

# --- Login and Get Token ---
echo "Attempting to log in as user '$DELETER_USER' to delete courses..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/token/" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$DELETER_USER\", \"password\": \"$DELETER_PASS\"}")

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

# --- Get List of Course IDs ---
# Fetch courses, requesting a large page size to simplify pagination handling.
# Note: This assumes the API respects page_size parameter.
# The default /api/courses/ endpoint returns non-deleted courses.
echo "Fetching list of courses (attempting to fetch up to $PAGE_SIZE_LIMIT)..."
COURSES_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/courses/?page_size=${PAGE_SIZE_LIMIT}" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

# Extract only the IDs from the 'results' array using jq
# If no courses are found, this will be empty.
COURSE_IDS=$(echo "$COURSES_RESPONSE" | jq -r '.results[].id')

# Check if any IDs were found
if [ -z "$COURSE_IDS" ]; then
  echo "No active courses found via the API endpoint ${BASE_URL}/api/courses/."
  echo "Perhaps they were already deleted or none exist."
  exit 0
fi

# Count the number of courses found
NUM_FOUND=$(echo "$COURSE_IDS" | wc -w | xargs) # xargs trims whitespace
echo "Found $NUM_FOUND course ID(s) to attempt deletion."

# --- Loop and Delete Courses ---
echo "Starting course deletion loop..."
DELETED_COUNT=0
SKIPPED_COUNT=0
FAILED_COUNT=0

# Use a while read loop for robustness, especially if IDs could have unexpected characters (unlikely for integers)
echo "$COURSE_IDS" | while IFS= read -r course_id; do
  # Skip empty lines if jq somehow produces them
  if [ -z "$course_id" ]; then
    continue
  fi

  echo " - Attempting to delete course with ID: $course_id"
  # Send DELETE request and capture HTTP status code
  DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/api/courses/${course_id}/" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

  case "$DELETE_STATUS" in
    204)
      echo "   - Success (Status: $DELETE_STATUS - No Content)"
      ((DELETED_COUNT++))
      ;;
    403)
      echo "   - Skipped: Permission Denied (Status: $DELETE_STATUS - Forbidden). User '$DELETER_USER' might not own this course or lack admin rights."
      ((SKIPPED_COUNT++))
      ;;
    404)
      echo "   - Skipped: Not Found (Status: $DELETE_STATUS). Course might have been deleted already."
      ((SKIPPED_COUNT++))
      ;;
    *)
      echo "   - Failed (Status: $DELETE_STATUS)"
      ((FAILED_COUNT++))
      ;;
  esac
  # Optional: Add a small delay to avoid hammering the server
  # sleep 0.1
done

echo "-------------------------------------"
echo "Finished course deletion attempts."
echo "Successfully deleted: $DELETED_COUNT course(s)."
echo "Skipped (Permission/Not Found): $SKIPPED_COUNT course(s)."
if [ "$FAILED_COUNT" -gt 0 ]; then
   echo "Failed attempts (Other errors): $FAILED_COUNT course(s)."
   echo "-------------------------------------"
   exit 1 # Exit with error if any unexpected failures occurred
fi
echo "-------------------------------------"

exit 0
